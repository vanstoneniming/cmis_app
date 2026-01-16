"""
学校管理模块
"""
from sqlalchemy.orm import Session
from database.models import School, User, Course, Student, Semester
from typing import List, Optional

def create_school(session: Session, school_name: str, domain: str = None, settings: str = None) -> School:
    """创建学校"""
    school = School(
        school_name=school_name,
        domain=domain,
        settings=settings
    )
    session.add(school)
    session.commit()
    session.refresh(school)
    return school

def get_school_by_id(session: Session, school_id: int) -> Optional[School]:
    """根据ID获取学校"""
    return session.query(School).filter(School.school_id == school_id).first()

def get_all_schools(session: Session) -> List[School]:
    """获取所有学校"""
    return session.query(School).order_by(School.school_name).all()

def update_school(session: Session, school_id: int, **kwargs) -> Optional[School]:
    """更新学校信息"""
    school = get_school_by_id(session, school_id)
    if school:
        for key, value in kwargs.items():
            if hasattr(school, key) and value is not None:
                setattr(school, key, value)
        
        session.commit()
        session.refresh(school)
    return school

def delete_school(session: Session, school_id: int) -> bool:
    """删除学校（需要先删除该学校下的所有关联数据）"""
    school = get_school_by_id(session, school_id)
    if school:
        # 检查是否有用户、课程、学生、学期关联
        user_count = session.query(User).filter(User.school_id == school_id).count()
        course_count = session.query(Course).filter(Course.school_id == school_id).count()
        student_count = session.query(Student).filter(Student.school_id == school_id).count()
        semester_count = session.query(Semester).filter(Semester.school_id == school_id).count()
        
        if user_count > 0 or course_count > 0 or student_count > 0 or semester_count > 0:
            return False  # 不能删除有关联数据的学校
        
        session.delete(school)
        session.commit()
        return True
    return False

def get_school_statistics(session: Session, school_id: int) -> dict:
    """获取学校的统计信息"""
    user_count = session.query(User).filter(User.school_id == school_id).count()
    course_count = session.query(Course).filter(Course.school_id == school_id).count()
    student_count = session.query(Student).filter(Student.school_id == school_id).count()
    semester_count = session.query(Semester).filter(Semester.school_id == school_id).count()
    
    return {
        'users': user_count,
        'courses': course_count,
        'students': student_count,
        'semesters': semester_count
    }