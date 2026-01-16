"""
任务管理模块
"""
from sqlalchemy.orm import Session
from database.models import Task, Course
from typing import List, Optional
from modules.logging_module import AuditLogger
import streamlit as st
from datetime import datetime

def create_task(session: Session, course_id: int, task_name: str, task_type: str,
                total_score: float = 100.0, weight: float = 1.0, deadline: datetime = None,
                description: str = None, status: str = '进行中') -> Optional[Task]:
    """创建新任务"""
    # 验证课程是否存在
    course = session.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        return None
    
    task = Task(
        course_id=course_id,
        task_name=task_name,
        task_type=task_type,
        total_score=total_score,
        weight=weight,
        deadline=deadline,
        description=description,
        status=status
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    # 记录日志
    try:
        user_id = st.session_state.get('user_id')
        AuditLogger.log_action(
            session, user_id, 'create', 'task', task.task_id,
            f"创建任务: {task_name} (课程: {course.course_name})"
        )
    except Exception as e:
        pass
    
    return task

def get_tasks_by_course(session: Session, course_id: int) -> List[Task]:
    """获取指定课程的所有任务"""
    return session.query(Task).filter(Task.course_id == course_id).order_by(Task.created_at.desc()).all()

def get_task_by_id(session: Session, task_id: int) -> Optional[Task]:
    """根据ID获取任务"""
    return session.query(Task).filter(Task.task_id == task_id).first()

def update_task(session: Session, task_id: int, **kwargs) -> Optional[Task]:
    """更新任务信息"""
    task = get_task_by_id(session, task_id)
    if task:
        changes = []
        for key, value in kwargs.items():
            if hasattr(task, key) and value is not None:
                old_value = getattr(task, key)
                setattr(task, key, value)
                changes.append(f"{key}: {old_value} -> {value}")
        
        if changes:
            session.commit()
            session.refresh(task)
            
            # 记录日志
            try:
                user_id = st.session_state.get('user_id')
                AuditLogger.log_action(
                    session, user_id, 'update', 'task', task_id,
                    f"更新任务: {', '.join(changes)}"
                )
            except Exception as e:
                pass
    
    return task

def delete_task(session: Session, task_id: int) -> bool:
    """删除任务（级联删除相关成绩）"""
    task = get_task_by_id(session, task_id)
    if task:
        task_name = task.task_name
        session.delete(task)
        session.commit()
        
        # 记录日志
        try:
            user_id = st.session_state.get('user_id')
            AuditLogger.log_action(
                session, user_id, 'delete', 'task', task_id,
                f"删除任务: {task_name}"
            )
        except Exception as e:
            pass
        
        return True
    return False

def get_user_tasks(session: Session, user_id: int, user_role: str) -> List[Task]:
    """根据用户角色获取任务列表"""
    from modules.auth import get_user_courses
    
    if user_role in ['super_admin', 'school_admin']:
        # 管理员可以看到所有任务
        return session.query(Task).order_by(Task.created_at.desc()).all()
    else:
        # 普通用户只能看到自己有权限的课程的任务
        user_courses = get_user_courses(session, user_id, include_created=True)
        course_ids = [c.course_id for c in user_courses]
        if course_ids:
            return session.query(Task).filter(Task.course_id.in_(course_ids)).order_by(Task.created_at.desc()).all()
        else:
            return []
