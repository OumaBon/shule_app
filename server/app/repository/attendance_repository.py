from .base_repository import BaseRepository
from app.models.attendance import Attendance
from app.models.student import Student
from app.models.school_class import SchoolClass
from app import db
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func, case

class AttendanceRepository(BaseRepository):
    """Repository for Attendance model with specific queries"""
    
    def __init__(self):
        super().__init__(Attendance)
    
    def get_by_student_and_date(self, student_id: int, date: date) -> Optional[Attendance]:
        """Get attendance record for a specific student on a specific date"""
        return self.model.query.filter_by(student_id=student_id, date=date).first()
    
    def get_attendance_by_student_range(self, student_id: int, start_date: date, end_date: date) -> List[Attendance]:
        """Get attendance records for a student in date range"""
        return self.model.query.filter(
            self.model.student_id == student_id,
            self.model.date.between(start_date, end_date)
        ).order_by(self.model.date).all()
    
    def get_attendance_by_class_and_date(self, class_id: int, date: date) -> List[Attendance]:
        """Get all attendance records for a class on a specific date"""
        return self.model.query.join(Student).filter(
            Student.class_id == class_id,
            self.model.date == date
        ).all()
    
    def get_attendance_by_class_range(self, class_id: int, start_date: date, end_date: date) -> List[Attendance]:
        """Get attendance records for a class in date range"""
        return self.model.query.join(Student).filter(
            Student.class_id == class_id,
            self.model.date.between(start_date, end_date)
        ).order_by(self.model.date).all()
    
    def get_attendance_by_teacher_range(self, teacher_id: int, start_date: date, end_date: date) -> List[Attendance]:
        """Get attendance marked by a teacher in date range"""
        return self.model.query.filter(
            self.model.marked_by_id == teacher_id,
            self.model.date.between(start_date, end_date)
        ).order_by(self.model.date).all()
    
    def bulk_mark_attendance(self, attendance_data: List[Dict[str, Any]], marked_by_id: int) -> List[Attendance]:
        """Bulk mark attendance for multiple students"""
        try:
            records = []
            for data in attendance_data:
                attendance = self.get_by_student_and_date(data['student_id'], data['date'])
                if attendance:
                    # Update existing
                    attendance.status = data['status']
                    attendance.marked_by_id = marked_by_id
                    attendance.remarks = data.get('remarks', attendance.remarks)
                    attendance.check_in_time = data.get('check_in_time', attendance.check_in_time)
                else:
                    # Create new
                    attendance = self.model(
                        student_id=data['student_id'],
                        date=data['date'],
                        status=data['status'],
                        marked_by_id=marked_by_id,
                        remarks=data.get('remarks'),
                        check_in_time=data.get('check_in_time')
                    )
                    db.session.add(attendance)
                records.append(attendance)
            db.session.commit()
            return records
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_student_attendance_summary(self, student_id: int, start_date: date, end_date: date = None) -> Dict[str, Any]:
        """Get attendance summary for a student"""
        if not end_date:
            end_date = date.today()
        
        attendance_records = self.get_attendance_by_student_range(student_id, start_date, end_date)
        
        total = len(attendance_records)
        present = sum(1 for r in attendance_records if r.status == Attendance.STATUS_PRESENT)
        absent = sum(1 for r in attendance_records if r.status == Attendance.STATUS_ABSENT)
        late = sum(1 for r in attendance_records if r.status == Attendance.STATUS_LATE)
        excused = sum(1 for r in attendance_records if r.status == Attendance.STATUS_EXCUSED)
        
        return {
            'student_id': student_id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_days': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'attendance_rate': (present / total * 100) if total > 0 else 0,
            'absent_rate': (absent / total * 100) if total > 0 else 0,
            'late_rate': (late / total * 100) if total > 0 else 0
        }
    
    def get_class_attendance_summary(self, class_id: int, month: int, year: int) -> Dict[str, Any]:
        """Get attendance summary for a class for a specific month"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        students = Student.query.filter_by(class_id=class_id).all()
        total_students = len(students)
        
        summary = {
            'class_id': class_id,
            'month': month,
            'year': year,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_students': total_students,
            'student_summaries': []
        }
        
        for student in students:
            student_summary = self.get_student_attendance_summary(student.id, start_date, end_date)
            summary['student_summaries'].append({
                'student_id': student.id,
                'student_name': student.user.full_name,
                'admission_number': student.admission_number,
                'summary': student_summary
            })
        
        # Class totals
        total_present = sum(s['summary']['present'] for s in summary['student_summaries'])
        total_absent = sum(s['summary']['absent'] for s in summary['student_summaries'])
        total_late = sum(s['summary']['late'] for s in summary['student_summaries'])
        total_days = sum(s['summary']['total_days'] for s in summary['student_summaries'])
        
        summary['class_totals'] = {
            'total_present': total_present,
            'total_absent': total_absent,
            'total_late': total_late,
            'overall_attendance_rate': (total_present / total_days * 100) if total_days > 0 else 0
        }
        
        return summary
    
    def get_daily_attendance_report(self, date: date) -> Dict[str, Any]:
        """Get daily attendance report for all classes"""
        report = {
            'date': date.isoformat(),
            'classes': []
        }
        
        classes = SchoolClass.query.filter_by(is_active=True).all()
        
        for school_class in classes:
            students = Student.query.filter_by(class_id=school_class.id).all()
            total_students = len(students)
            
            attendance_records = self.get_attendance_by_class_and_date(school_class.id, date)
            
            present = len([r for r in attendance_records if r.status == Attendance.STATUS_PRESENT])
            absent = len([r for r in attendance_records if r.status == Attendance.STATUS_ABSENT])
            late = len([r for r in attendance_records if r.status == Attendance.STATUS_LATE])
            excused = len([r for r in attendance_records if r.status == Attendance.STATUS_EXCUSED])
            not_marked = total_students - len(attendance_records)
            
            report['classes'].append({
                'class_id': school_class.id,
                'class_name': school_class.name,
                'total_students': total_students,
                'present': present,
                'absent': absent,
                'late': late,
                'excused': excused,
                'not_marked': not_marked,
                'attendance_rate': (present / total_students * 100) if total_students > 0 else 0,
                'records': [record.to_dict() for record in attendance_records]
            })
        
        return report
    
    def get_attendance_trends(self, class_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get attendance trends for the last N days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        trends = []
        current_date = start_date
        while current_date <= end_date:
            attendance_records = self.get_attendance_by_class_and_date(class_id, current_date)
            total_students = Student.query.filter_by(class_id=class_id).count()
            
            present_count = sum(1 for r in attendance_records if r.status == Attendance.STATUS_PRESENT)
            
            trends.append({
                'date': current_date.isoformat(),
                'present_count': present_count,
                'total_students': total_students,
                'attendance_rate': (present_count / total_students * 100) if total_students > 0 else 0
            })
            current_date += timedelta(days=1)
        
        return trends
    
    def get_attendance_by_status(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get attendance counts grouped by status"""
        results = self.model.query.filter(
            self.model.date.between(start_date, end_date)
        ).group_by(self.model.status).value(
            self.model.status,
            func.count(self.model.id)
        ).all()
        
        return {status: count for status, count in results}
    
    def get_missing_attendance_dates(self, class_id: int, start_date: date, end_date: date) -> List[date]:
        """Get dates where attendance hasn't been marked for a class"""
        students = Student.query.filter_by(class_id=class_id).all()
        if not students:
            return []
        
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            # Skip weekends if needed
            if current_date.weekday() < 5:  # Monday to Friday
                all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        missing_dates = []
        for check_date in all_dates:
            attendance_count = self.model.query.filter(
                self.model.date == check_date,
                self.model.student_id.in_([s.id for s in students])
            ).count()
            
            if attendance_count < len(students):
                missing_dates.append(check_date)
        
        return missing_dates
    
    def get_students_with_poor_attendance(self, class_id: int, threshold_percentage: float = 75) -> List[Dict[str, Any]]:
        """Get students with attendance below threshold"""
        students = Student.query.filter_by(class_id=class_id).all()
        start_date = date(date.today().year, 1, 1)  # Start of current year
        end_date = date.today()
        
        poor_attendance_students = []
        for student in students:
            summary = self.get_student_attendance_summary(student.id, start_date, end_date)
            if summary['attendance_rate'] < threshold_percentage:
                poor_attendance_students.append({
                    'student': student.to_dict(),
                    'attendance_rate': summary['attendance_rate'],
                    'present': summary['present'],
                    'absent': summary['absent'],
                    'late': summary['late']
                })
        
        return poor_attendance_students
    
    def copy_attendance_from_previous_day(self, class_id: int, source_date: date, target_date: date, marked_by_id: int) -> int:
        """Copy attendance from one day to another (for holidays/weekends)"""
        source_records = self.get_attendance_by_class_and_date(class_id, source_date)
        
        created_count = 0
        for record in source_records:
            existing = self.get_by_student_and_date(record.student_id, target_date)
            if not existing:
                self.create(
                    student_id=record.student_id,
                    date=target_date,
                    status=record.status,
                    marked_by_id=marked_by_id,
                    remarks=f"Copied from {source_date}"
                )
                created_count += 1
        
        return created_count