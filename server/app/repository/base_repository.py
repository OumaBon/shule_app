from app import db
from typing import List, Optional, Dict, Any, TypeVar, Generic, Tuple
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, or_, desc, asc
from flask_sqlalchemy import Pagination

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: T):
        self.model = model
    
    def create(self, **kwargs) -> Optional[T]:
        """Create a new record"""
        try:
            instance = self.model(**kwargs)
            db.session.add(instance)
            db.session.commit()
            return instance
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Bulk create records"""
        try:
            instances = [self.model(**item) for item in items]
            db.session.bulk_save_objects(instances)
            db.session.commit()
            return instances
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get record by ID"""
        return self.model.query.get(id)
    
    def get_by_ids(self, ids: List[int]) -> List[T]:
        """Get multiple records by IDs"""
        return self.model.query.filter(self.model.id.in_(ids)).all()
    
    def get_all(self, limit: int = None, offset: int = None, order_by: str = None, 
                order_direction: str = 'asc') -> List[T]:
        """Get all records with pagination and ordering"""
        query = self.model.query
        
        if order_by:
            column = getattr(self.model, order_by)
            if order_direction == 'desc':
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
            
        return query.all()
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        """Update a record"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            db.session.commit()
            return instance
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def update_by_filters(self, filters: Dict[str, Any], **kwargs) -> int:
        """Update multiple records matching filters"""
        try:
            query = self.model.query
            for key, value in filters.items():
                query = query.filter(getattr(self.model, key) == value)
            
            count = query.update(kwargs, synchronize_session=False)
            db.session.commit()
            return count
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def delete(self, id: int, soft_delete: bool = False, active_field: str = 'is_active') -> bool:
        """Delete or soft delete a record"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False
            if soft_delete and hasattr(instance, active_field):
                setattr(instance, active_field, False)
                db.session.commit()
            else:
                db.session.delete(instance)
                db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def permanent_delete(self, id: int) -> bool:
        """Permanently delete a record (hard delete)"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False
            db.session.delete(instance)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def exists(self, **filters) -> bool:
        """Check if record exists with given filters"""
        query = self.model.query
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.first() is not None
    
    def count(self, **filters) -> int:
        """Count records with optional filters"""
        query = self.model.query
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.count()
    
    def filter_by(self, **filters) -> List[T]:
        """Filter records by exact matches"""
        query = self.model.query
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.all()
    
    def filter_by_conditions(self, conditions: List[Tuple[str, str, Any]]) -> List[T]:
        """Filter records with multiple conditions (field, operator, value)"""
        query = self.model.query
        operator_map = {
            'eq': lambda f, v: f == v,
            'ne': lambda f, v: f != v,
            'lt': lambda f, v: f < v,
            'le': lambda f, v: f <= v,
            'gt': lambda f, v: f > v,
            'ge': lambda f, v: f >= v,
            'like': lambda f, v: f.like(f'%{v}%'),
            'ilike': lambda f, v: f.ilike(f'%{v}%'),
            'in': lambda f, v: f.in_(v),
            'not_in': lambda f, v: ~f.in_(v)
        }
        
        for field, operator, value in conditions:
            column = getattr(self.model, field)
            filter_func = operator_map.get(operator)
            if filter_func:
                query = query.filter(filter_func(column, value))
        return query.all()
    
    def paginate(self, page: int = 1, per_page: int = 20, **filters) -> Pagination:
        """Paginate results with filters"""
        query = self.model.query
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    def first_or_create(self, defaults: Dict = None, **filters) -> Tuple[T, bool]:
        """Get first record matching filters or create if not exists"""
        instance = self.filter_by(**filters)
        if instance:
            return instance[0], False
        if defaults:
            filters.update(defaults)
        return self.create(**filters), True
    
    def get_or_create(self, **kwargs) -> Tuple[T, bool]:
        """Get or create a record"""
        instance = self.filter_by(**kwargs)
        if instance:
            return instance[0], False
        return self.create(**kwargs), True
    
    def bulk_update(self, updates: Dict[int, Dict[str, Any]]) -> int:
        """Bulk update multiple records"""
        try:
            count = 0
            for record_id, update_data in updates.items():
                instance = self.get_by_id(record_id)
                if instance:
                    for key, value in update_data.items():
                        if hasattr(instance, key):
                            setattr(instance, key, value)
                    count += 1
            db.session.commit()
            return count
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def get_random(self, limit: int = 1) -> List[T]:
        """Get random records"""
        return self.model.query.order_by(func.random()).limit(limit).all()