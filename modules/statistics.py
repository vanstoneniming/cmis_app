"""
统计分析模块
"""
from sqlalchemy.orm import Session
from database.models import Course, Task, Grade, Student
from typing import Dict, List, Optional
from sqlalchemy import func
import pandas as pd

def get_course_statistics(session: Session, course_id: int) -> Dict:
    """获取课程统计信息"""
    course = session.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        return None
    
    # 任务数量
    task_count = session.query(Task).filter(Task.course_id == course_id).count()
    
    # 成绩统计
    tasks = session.query(Task).filter(Task.course_id == course_id).all()
    task_ids = [t.task_id for t in tasks]
    
    if task_ids:
        total_grades = session.query(Grade).filter(Grade.task_id.in_(task_ids)).count()
        submitted_count = session.query(Grade).filter(
            Grade.task_id.in_(task_ids),
            Grade.status == '已提交'
        ).count()
        
        # 平均分
        avg_score = session.query(func.avg(Grade.score)).filter(
            Grade.task_id.in_(task_ids),
            Grade.score.isnot(None)
        ).scalar()
        avg_score = float(avg_score) if avg_score else 0.0
    else:
        total_grades = 0
        submitted_count = 0
        avg_score = 0.0
    
    return {
        'course_id': course_id,
        'course_name': course.course_name,
        'task_count': task_count,
        'total_grades': total_grades,
        'submitted_count': submitted_count,
        'submission_rate': (submitted_count / total_grades * 100) if total_grades > 0 else 0.0,
        'avg_score': avg_score
    }

def get_task_statistics(session: Session, task_id: int) -> Dict:
    """获取任务统计信息"""
    task = session.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        return None
    
    # 成绩统计
    grades = session.query(Grade).filter(Grade.task_id == task_id).all()
    total_count = len(grades)
    submitted_count = len([g for g in grades if g.status == '已提交'])
    scored_count = len([g for g in grades if g.score is not None])
    
    # 分数统计
    scores = [g.score for g in grades if g.score is not None]
    if scores:
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
    else:
        avg_score = 0.0
        max_score = 0.0
        min_score = 0.0
    
    # 分数分布
    score_distribution = {}
    if scores:
        for score in scores:
            range_key = f"{(int(score) // 10) * 10}-{(int(score) // 10) * 10 + 9}"
            score_distribution[range_key] = score_distribution.get(range_key, 0) + 1
    
    return {
        'task_id': task_id,
        'task_name': task.task_name,
        'total_count': total_count,
        'submitted_count': submitted_count,
        'submission_rate': (submitted_count / total_count * 100) if total_count > 0 else 0.0,
        'scored_count': scored_count,
        'avg_score': avg_score,
        'max_score': max_score,
        'min_score': min_score,
        'score_distribution': score_distribution
    }

def get_student_statistics(session: Session, student_id: str, course_id: int = None) -> Dict:
    """获取学生统计信息"""
    student = session.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        return None
    
    # 获取成绩
    if course_id:
        query = session.query(Grade).join(Task).filter(
            Grade.student_id == student_id,
            Task.course_id == course_id
        )
    else:
        query = session.query(Grade).filter(Grade.student_id == student_id)
    
    grades = query.all()
    
    total_count = len(grades)
    submitted_count = len([g for g in grades if g.status == '已提交'])
    scores = [g.score for g in grades if g.score is not None]
    
    if scores:
        avg_score = sum(scores) / len(scores)
    else:
        avg_score = 0.0
    
    return {
        'student_id': student_id,
        'student_name': student.name,
        'total_count': total_count,
        'submitted_count': submitted_count,
        'avg_score': avg_score
    }

def get_overall_statistics(session: Session, user_id: int, user_role: str) -> Dict:
    """获取整体统计信息"""
    from modules.auth import get_user_courses
    
    if user_role in ['super_admin', 'school_admin']:
        # 管理员看到全部数据
        total_courses = session.query(Course).count()
        total_tasks = session.query(Task).count()
        total_students = session.query(Student).count()
        total_grades = session.query(Grade).count()
    else:
        # 普通用户只看到自己的数据
        user_courses = get_user_courses(session, user_id, include_created=True)
        course_ids = [c.course_id for c in user_courses]
        total_courses = len(course_ids)
        
        if course_ids:
            total_tasks = session.query(Task).filter(Task.course_id.in_(course_ids)).count()
            task_ids = [t.task_id for t in session.query(Task).filter(Task.course_id.in_(course_ids)).all()]
            total_grades = session.query(Grade).filter(Grade.task_id.in_(task_ids)).count() if task_ids else 0
        else:
            total_tasks = 0
            total_grades = 0
        total_students = session.query(Student).count()
    
    return {
        'total_courses': total_courses,
        'total_tasks': total_tasks,
        'total_students': total_students,
        'total_grades': total_grades
    }
