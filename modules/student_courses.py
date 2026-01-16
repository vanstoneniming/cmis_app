"""
学生-课程关联管理模块
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database.models import StudentCourse, Student, Course
from typing import List, Optional, Tuple

def enroll_student_to_course(session: Session, student_id: str, course_id: int) -> Tuple[bool, str]:
    """将学生添加到课程"""
    # 检查学生是否存在
    student = session.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        return False, "学生不存在"
    
    # 检查课程是否存在
    course = session.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        return False, "课程不存在"
    
    # 检查是否已经关联
    existing = session.query(StudentCourse).filter(
        and_(
            StudentCourse.student_id == student_id,
            StudentCourse.course_id == course_id
        )
    ).first()
    
    if existing:
        return False, "学生已在该课程中"
    
    # 创建关联
    enrollment = StudentCourse(
        student_id=student_id,
        course_id=course_id
    )
    session.add(enrollment)
    session.commit()
    
    return True, None

def remove_student_from_course(session: Session, student_id: str, course_id: int) -> bool:
    """从课程中移除学生"""
    enrollment = session.query(StudentCourse).filter(
        and_(
            StudentCourse.student_id == student_id,
            StudentCourse.course_id == course_id
        )
    ).first()
    
    if enrollment:
        session.delete(enrollment)
        session.commit()
        return True
    return False

def get_course_students(session: Session, course_id: int) -> List[Student]:
    """获取课程的所有学生"""
    enrollments = session.query(StudentCourse).filter(StudentCourse.course_id == course_id).all()
    student_ids = [e.student_id for e in enrollments]
    if student_ids:
        return session.query(Student).filter(Student.student_id.in_(student_ids)).order_by(Student.class_name, Student.name).all()
    return []

def get_student_courses(session: Session, student_id: str) -> List[Course]:
    """获取学生的所有课程"""
    enrollments = session.query(StudentCourse).filter(StudentCourse.student_id == student_id).all()
    course_ids = [e.course_id for e in enrollments]
    if course_ids:
        return session.query(Course).filter(Course.course_id.in_(course_ids)).all()
    return []

def is_student_enrolled(session: Session, student_id: str, course_id: int) -> bool:
    """检查学生是否已选课"""
    enrollment = session.query(StudentCourse).filter(
        and_(
            StudentCourse.student_id == student_id,
            StudentCourse.course_id == course_id
        )
    ).first()
    return enrollment is not None

def bulk_enroll_students(session: Session, student_ids: List[str], course_id: int) -> Tuple[int, int, List[str]]:
    """批量将学生添加到课程
    返回: (成功数量, 失败数量, 错误信息列表)
    """
    success_count = 0
    fail_count = 0
    errors = []
    
    for student_id in student_ids:
        success, error = enroll_student_to_course(session, student_id, course_id)
        if success:
            success_count += 1
        else:
            fail_count += 1
            if error and error != "学生已在该课程中":  # 已存在不算错误
                errors.append(f"{student_id}: {error}")
    
    return success_count, fail_count, errors
