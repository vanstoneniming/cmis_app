"""
学期管理模块
"""
from sqlalchemy.orm import Session
from database.models import Semester, Course, School
from typing import List, Optional
from datetime import datetime

def create_semester(session: Session, school_id: int, semester_name: str,
                   semester_code: str = None, start_date: datetime = None,
                   end_date: datetime = None, is_active: bool = False) -> Semester:
    """创建学期"""
    # 如果设置为当前学期，先将其他学期设为非当前
    if is_active:
        session.query(Semester).filter(
            Semester.school_id == school_id,
            Semester.is_active == True
        ).update({'is_active': False})
    
    semester = Semester(
        school_id=school_id,
        semester_name=semester_name,
        semester_code=semester_code,
        start_date=start_date,
        end_date=end_date,
        is_active=is_active
    )
    session.add(semester)
    session.commit()
    session.refresh(semester)
    return semester

def get_all_semesters(session: Session, school_id: int = None) -> List[Semester]:
    """获取所有学期（可指定学校）"""
    query = session.query(Semester)
    if school_id:
        query = query.filter(Semester.school_id == school_id)
    return query.order_by(Semester.start_date.desc(), Semester.created_at.desc()).all()

def get_semester_by_id(session: Session, semester_id: int) -> Optional[Semester]:
    """根据ID获取学期"""
    return session.query(Semester).filter(Semester.semester_id == semester_id).first()

def get_active_semester(session: Session, school_id: int = None) -> Optional[Semester]:
    """获取当前活跃学期"""
    query = session.query(Semester).filter(Semester.is_active == True)
    if school_id:
        query = query.filter(Semester.school_id == school_id)
    return query.first()

def update_semester(session: Session, semester_id: int, **kwargs) -> Optional[Semester]:
    """更新学期信息"""
    semester = get_semester_by_id(session, semester_id)
    if semester:
        # 如果设置为当前学期，先将其他学期设为非当前
        if kwargs.get('is_active') is True:
            session.query(Semester).filter(
                Semester.school_id == semester.school_id,
                Semester.is_active == True,
                Semester.semester_id != semester_id
            ).update({'is_active': False})
        
        for key, value in kwargs.items():
            if hasattr(semester, key) and value is not None:
                setattr(semester, key, value)
        
        session.commit()
        session.refresh(semester)
    return semester

def delete_semester(session: Session, semester_id: int) -> bool:
    """删除学期（需要先删除该学期下的所有课程）"""
    semester = get_semester_by_id(session, semester_id)
    if semester:
        # 检查是否有课程关联
        course_count = session.query(Course).filter(Course.semester_id == semester_id).count()
        if course_count > 0:
            return False  # 不能删除有关联课程的学期
        
        session.delete(semester)
        session.commit()
        return True
    return False

def get_semester_courses(session: Session, semester_id: int) -> List[Course]:
    """获取学期的所有课程"""
    return session.query(Course).filter(Course.semester_id == semester_id).all()
