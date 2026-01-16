"""
课程管理模块
"""
from sqlalchemy.orm import Session
from database.models import Course
from typing import List, Optional
from modules.logging_module import AuditLogger
import streamlit as st

def create_course(session: Session, course_name: str, semester: str = None, 
                 teacher: str = None, description: str = None, creator_id: int = None,
                 semester_id: int = None, school_id: int = None, course_code: str = None) -> Course:
    """创建新课程"""
    # 从session state获取creator_id（如果未提供）
    if creator_id is None:
        creator_id = st.session_state.get('user_id')
    
    # 如果没有用户ID，尝试获取或创建默认用户
    if creator_id is None:
        try:
            from database.models import User
            # 检查用户表是否存在数据
            user_count = session.query(User).count()
            if user_count > 0:
                # 尝试获取第一个管理员用户
                admin_user = session.query(User).filter(
                    User.role.in_(['super_admin', 'school_admin'])
                ).first()
                if admin_user:
                    creator_id = admin_user.user_id
                else:
                    # 使用第一个用户
                    first_user = session.query(User).first()
                    creator_id = first_user.user_id if first_user else None
            else:
                # 创建默认管理员用户
                try:
                    from modules.auth import create_user
                    default_user, error = create_user(
                        session, 'admin', 'admin123', 
                        role='super_admin', real_name='系统管理员'
                    )
                    if default_user and not error:
                        creator_id = default_user.user_id
                    else:
                        creator_id = None  # 如果创建失败，使用NULL（字段已允许NULL）
                except Exception as e:
                    # 如果创建用户失败（可能是表不存在），使用None
                    creator_id = None
        except Exception as e:
            # 如果用户表不存在或查询失败，使用None
            creator_id = None
    
    # 如果没有指定school_id，尝试从creator获取
    if school_id is None and creator_id:
        try:
            from database.models import User
            creator = session.query(User).filter(User.user_id == creator_id).first()
            if creator and creator.school_id:
                school_id = creator.school_id
        except:
            pass
    
    course = Course(
        course_name=course_name,
        course_code=course_code,
        semester_id=semester_id,
        semester=semester,  # 保留，向后兼容
        teacher=teacher,  # 保留，向后兼容
        description=description,
        creator_id=creator_id,
        school_id=school_id
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    
    # 记录日志（如果日志模块可用）
    try:
        AuditLogger.log_course_action(
            session, 'create', course.course_id,
            f"创建课程: {course_name}",
            creator_id
        )
    except Exception as e:
        # 日志记录失败不影响主业务
        pass
    
    return course

def get_all_courses(session: Session) -> List[Course]:
    """获取所有课程"""
    return session.query(Course).order_by(Course.created_at.desc()).all()

def get_course_by_id(session: Session, course_id: int) -> Optional[Course]:
    """根据ID获取课程"""
    return session.query(Course).filter(Course.course_id == course_id).first()

def update_course(session: Session, course_id: int, **kwargs) -> Optional[Course]:
    """更新课程信息"""
    course = get_course_by_id(session, course_id)
    if course:
        changes = []
        for key, value in kwargs.items():
            if hasattr(course, key) and value is not None:
                old_value = getattr(course, key)
                setattr(course, key, value)
                changes.append(f"{key}: {old_value} -> {value}")
        
        if changes:
            session.commit()
            session.refresh(course)
            
            # 记录日志（如果日志模块可用）
            try:
                user_id = st.session_state.get('user_id')
                AuditLogger.log_course_action(
                    session, 'update', course_id,
                    f"更新课程: {', '.join(changes)}",
                    user_id
                )
            except Exception as e:
                print(f"日志记录失败: {e}")
    
    return course

def delete_course(session: Session, course_id: int) -> bool:
    """删除课程（级联删除相关任务和成绩）"""
    course = get_course_by_id(session, course_id)
    if course:
        course_name = course.course_name
        session.delete(course)
        session.commit()
        
        # 记录日志（如果日志模块可用）
        try:
            user_id = st.session_state.get('user_id')
            AuditLogger.log_course_action(
                session, 'delete', course_id,
                f"删除课程: {course_name}",
                user_id
            )
        except Exception as e:
            print(f"日志记录失败: {e}")
        
        return True
    return False

