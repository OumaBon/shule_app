# app/services/attendance_service.py

from app.schemas.attendance_schema import attendance_schema, attendances_schema, attendance_list_schema, attendances_list_schema, bulk_attendance_schema
from app.models.attendance import Attendance
from app.models.student import Student
from app.models.teacher import Teacher
from app import db 
from marshmallow import ValidationError 
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 
from datetime import date, datetime, timedelta


class AttendanceService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AttendanceService, cls).__new__(cls)
            cls._instance._initialised = False
        return cls._instance  
    
    def __init__(self):
        if hasattr(self, '_initialised') and self._initialised:
            return 
       
        self.attendance_schema = attendance_schema
        self.attendances_schema = attendances_schema
        self.attendance_list_schema = attendance_list_schema
        self.attendances_list_schema = attendances_list_schema
        self.bulk_attendance_schema = bulk_attendance_schema
        self._initialised = True
    
    def mark_attendance(self, data):
        """
        Mark attendance for a single student
        
        Args:
            data: Dictionary containing attendance data
            
        Returns:
            Tuple of (serialized_attendance, error_messages, status_code)
        """
        try:
            # Load and validate data using schema
            attendance = self.attendance_schema.load(data, session=db.session)
            
            db.session.add(attendance)
            db.session.commit()
            return self.attendance_schema.dump(attendance), None, 201
        
        except ValidationError as err:
            db.session.rollback()
            return None, err.messages, 400
        
        except IntegrityError as err:
            db.session.rollback()
            error_msg = str(err).lower()
            if 'unique_student_attendance_per_day' in error_msg:
                return None, {"error": "Attendance already marked for this student today."}, 400
            return None, {"error": "Database integrity error occurred."}, 400
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in mark_attendance: {err}")
            import traceback
            traceback.print_exc()
            return None, {"error": "An unexpected error occurred."}, 500
    
    def mark_bulk_attendance(self, data_list, marked_by_id):
        """
        Mark attendance for multiple students at once
        
        Args:
            data_list: List of attendance data dictionaries
            marked_by_id: Teacher ID marking the attendance
            
        Returns:
            Tuple of (result, error_messages, status_code)
        """
        try:
            created = []
            failed = []
            
            for index, item in enumerate(data_list):
                try:
                    # Add marked_by_id to each item
                    item['marked_by_id'] = marked_by_id
                    if 'date' not in item:
                        item['date'] = date.today()
                    
                    # Validate and create each attendance record
                    attendance = self.attendance_schema.load(item, session=db.session)
                    db.session.add(attendance)
                    created.append({
                        'index': index,
                        'student_id': item.get('student_id')
                    })
                except ValidationError as err:
                    failed.append({
                        'index': index,
                        'student_id': item.get('student_id'),
                        'errors': err.messages
                    })
                except Exception as err:
                    failed.append({
                        'index': index,
                        'student_id': item.get('student_id'),
                        'errors': {'general': str(err)}
                    })
            
            # Commit all successful creations
            if created:
                db.session.commit()
            
            result = {
                'created': len(created),
                'failed': len(failed),
                'created_records': created,
                'failed_entries': failed
            }
            
            status_code = 201 if created else 400
            return result, None, status_code
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in mark_bulk_attendance: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_attendance(self, attendance_id):
        """
        Get attendance by ID
        
        Args:
            attendance_id: Attendance ID
            
        Returns:
            Tuple of (serialized_attendance, error_messages, status_code)
        """
        try:
            attendance = Attendance.query.get(attendance_id)
            if not attendance:
                return None, {"error": "Attendance record not found."}, 404
            return self.attendance_schema.dump(attendance), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_student_attendance(self, student_id, skip=0, limit=100, start_date=None, end_date=None):
        """
        Get attendance records for a specific student
        
        Args:
            student_id: Student ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Tuple of (attendance_data, error_messages, status_code)
        """
        try:
            student = Student.query.get(student_id)
            if not student:
                return None, {"error": "Student not found."}, 404
            
            query = Attendance.query.filter(Attendance.student_id == student_id)
            
            if start_date:
                query = query.filter(Attendance.date >= start_date)
            
            if end_date:
                query = query.filter(Attendance.date <= end_date)
            
            total = query.count()
            
            attendances = query.order_by(Attendance.date.desc()) \
                              .offset(skip) \
                              .limit(limit) \
                              .all()
            
            # Calculate statistics
            present_count = query.filter(Attendance.status == Attendance.STATUS_PRESENT).count()
            absent_count = query.filter(Attendance.status == Attendance.STATUS_ABSENT).count()
            late_count = query.filter(Attendance.status == Attendance.STATUS_LATE).count()
            excused_count = query.filter(Attendance.status == Attendance.STATUS_EXCUSED).count()
            
            result = {
                'student_id': student_id,
                'student_name': student.user.full_name if student.user else 'Unknown',
                'admission_number': student.admission_number,
                'attendance_records': self.attendances_list_schema.dump(attendances),
                'statistics': {
                    'total_records': total,
                    'present': present_count,
                    'absent': absent_count,
                    'late': late_count,
                    'excused': excused_count,
                    'attendance_rate': round((present_count / total * 100), 1) if total > 0 else 0
                },
                'pagination': {
                    'skip': skip,
                    'limit': limit,
                    'total': total
                }
            }
            
            return result, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_daily_attendance(self, attendance_date=None, class_id=None, skip=0, limit=100):
        """
        Get attendance records for a specific date
        
        Args:
            attendance_date: Date to get attendance for (defaults to today)
            class_id: Optional class filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (attendance_data, error_messages, status_code)
        """
        try:
            if attendance_date is None:
                attendance_date = date.today()
            
            query = Attendance.query.filter(Attendance.date == attendance_date)
            
            # Filter by class if provided
            if class_id:
                query = query.join(Student).filter(Student.class_id == class_id)
            
            total = query.count()
            
            attendances = query.order_by(Attendance.created_at.desc()) \
                              .offset(skip) \
                              .limit(limit) \
                              .all()
            
            # Calculate daily statistics
            present_count = query.filter(Attendance.status == Attendance.STATUS_PRESENT).count()
            absent_count = query.filter(Attendance.status == Attendance.STATUS_ABSENT).count()
            late_count = query.filter(Attendance.status == Attendance.STATUS_LATE).count()
            excused_count = query.filter(Attendance.status == Attendance.STATUS_EXCUSED).count()
            
            result = {
                'date': attendance_date.isoformat(),
                'total_records': total,
                'attendance_records': self.attendances_list_schema.dump(attendances),
                'statistics': {
                    'present': present_count,
                    'absent': absent_count,
                    'late': late_count,
                    'excused': excused_count,
                    'attendance_rate': round((present_count / total * 100), 1) if total > 0 else 0
                },
                'pagination': {
                    'skip': skip,
                    'limit': limit,
                    'total': total
                }
            }
            
            return result, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def update_attendance(self, attendance_id, data):
        """
        Update an attendance record
        
        Args:
            attendance_id: Attendance ID to update
            data: Dictionary containing updated data
            
        Returns:
            Tuple of (updated_attendance, error_messages, status_code)
        """
        try:
            attendance = Attendance.query.get(attendance_id)
            if not attendance:
                return None, {"error": "Attendance record not found."}, 404
            
            # Load and update attendance data
            updated_attendance = self.attendance_schema.load(
                data, 
                instance=attendance, 
                session=db.session, 
                partial=True
            )
            
            db.session.commit()
            return self.attendance_schema.dump(updated_attendance), None, 200
        
        except ValidationError as err:
            db.session.rollback()
            return None, err.messages, 400
        
        except IntegrityError as err:
            db.session.rollback()
            return None, {"error": "Database integrity error occurred."}, 400
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in update_attendance: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def delete_attendance(self, attendance_id):
        """
        Delete an attendance record
        
        Args:
            attendance_id: Attendance ID to delete
            
        Returns:
            Tuple of (data, error_messages, status_code)
        """
        try:
            attendance = Attendance.query.get(attendance_id)
            if not attendance:
                return None, {"error": "Attendance record not found."}, 404
            
            db.session.delete(attendance)
            db.session.commit()
            return None, None, 204
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in delete_attendance: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_attendance_statistics(self, start_date=None, end_date=None, class_id=None):
        """
        Get attendance statistics
        
        Args:
            start_date: Optional start date
            end_date: Optional end date
            class_id: Optional class filter
            
        Returns:
            Tuple of (statistics_data, error_messages, status_code)
        """
        try:
            from sqlalchemy import func
            
            query = Attendance.query
            
            if start_date:
                query = query.filter(Attendance.date >= start_date)
            
            if end_date:
                query = query.filter(Attendance.date <= end_date)
            
            if class_id:
                query = query.join(Student).filter(Student.class_id == class_id)
            
            total_records = query.count()
            
            # Status distribution
            status_stats = db.session.query(
                Attendance.status,
                func.count(Attendance.id).label('count')
            ).filter(
                Attendance.date >= start_date if start_date else True,
                Attendance.date <= end_date if end_date else True
            ).group_by(Attendance.status).all()
            
            # Daily attendance trend (last 30 days)
            thirty_days_ago = date.today() - timedelta(days=30)
            daily_stats = db.session.query(
                Attendance.date,
                func.count(Attendance.id).label('total'),
                func.sum(
                    db.case(
                        (Attendance.status == Attendance.STATUS_PRESENT, 1),
                        else_=0
                    )
                ).label('present_count')
            ).filter(
                Attendance.date >= thirty_days_ago
            ).group_by(Attendance.date) \
             .order_by(Attendance.date) \
             .all()
            
            statistics = {
                'total_records': total_records,
                'status_distribution': [
                    {'status': status, 'count': count} 
                    for status, count in status_stats
                ],
                'overall_attendance_rate': round(
                    (query.filter(Attendance.status == Attendance.STATUS_PRESENT).count() / total_records * 100), 1
                ) if total_records > 0 else 0,
                'daily_trend': [
                    {
                        'date': d.isoformat(),
                        'total': total,
                        'present': present,
                        'rate': round((present / total * 100), 1) if total > 0 else 0
                    }
                    for d, total, present in daily_stats
                ]
            }
            
            return statistics, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_class_attendance_summary(self, class_id, attendance_date=None):
        """
        Get attendance summary for a class
        
        Args:
            class_id: Class ID
            attendance_date: Date (defaults to today)
            
        Returns:
            Tuple of (summary_data, error_messages, status_code)
        """
        try:
            if attendance_date is None:
                attendance_date = date.today()
            
            from app.models.school_class import SchoolClass
            
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                return None, {"error": "Class not found."}, 404
            
            # Get all students in class
            students = school_class.students.all()
            
            # Get attendance for each student
            summary = []
            for student in students:
                attendance = Attendance.query.filter(
                    Attendance.student_id == student.id,
                    Attendance.date == attendance_date
                ).first()
                
                summary.append({
                    'student_id': student.id,
                    'admission_number': student.admission_number,
                    'name': student.user.full_name if student.user else 'Unknown',
                    'status': attendance.status if attendance else 'not_marked',
                    'status_display': attendance.status_display if attendance else 'Not Marked',
                    'check_in_time': attendance.check_in_time.isoformat() if attendance and attendance.check_in_time else None,
                    'remarks': attendance.remarks if attendance else None
                })
            
            # Calculate summary statistics
            total_students = len(students)
            marked_count = sum(1 for s in summary if s['status'] != 'not_marked')
            present_count = sum(1 for s in summary if s['status'] == 'present')
            absent_count = sum(1 for s in summary if s['status'] == 'absent')
            late_count = sum(1 for s in summary if s['status'] == 'late')
            excused_count = sum(1 for s in summary if s['status'] == 'excused')
            not_marked_count = total_students - marked_count
            
            result = {
                'class_id': class_id,
                'class_name': school_class.name,
                'date': attendance_date.isoformat(),
                'total_students': total_students,
                'statistics': {
                    'marked': marked_count,
                    'not_marked': not_marked_count,
                    'present': present_count,
                    'absent': absent_count,
                    'late': late_count,
                    'excused': excused_count,
                    'attendance_rate': round((present_count / total_students * 100), 1) if total_students > 0 else 0,
                    'completion_rate': round((marked_count / total_students * 100), 1) if total_students > 0 else 0
                },
                'students': summary
            }
            
            return result, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500


attendance_service = AttendanceService()