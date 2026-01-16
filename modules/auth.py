"""
用户认证和授权模块
"""
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database.models import User, UserRole, UserCourse, Course
from datetime import datetime
from typing import Optional, Tuple

def hash_password(password: str) -> str:
    """加密密码"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_user(session: Session, username: str, password: str, email: str = None,
                real_name: str = None, role: str = 'teacher', school_id: int = None) -> Tuple[User, str]:
    """创建新用户"""
    # 检查用户名是否已存在
    if session.query(User).filter(User.username == username).first():
        return None, "用户名已存在"
    
    # 检查邮箱是否已存在
    if email and session.query(User).filter(User.email == email).first():
        return None, "邮箱已被注册"
    
    password_hash = hash_password(password)
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        real_name=real_name or username,
        role=role,
        school_id=school_id,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user, None

def authenticate_user(session: Session, username: str, password: str) -> Tuple[Optional[User], str]:
    """用户认证"""
    user = session.query(User).filter(User.username == username).first()
    
    if not user:
        return None, "用户名或密码错误"
    
    if not user.is_active:
        return None, "账户已被禁用"
    
    if not verify_password(password, user.password_hash):
        return None, "用户名或密码错误"
    
    # 更新最后登录时间
    user.last_login = datetime.now()
    session.commit()
    
    # 记录登录日志
    from modules.logging_module import AuditLogger
    AuditLogger.log_login(session, user.user_id, user.username, success=True)
    
    return user, None

def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return session.query(User).filter(User.user_id == user_id).first()

def get_user_by_username(session: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return session.query(User).filter(User.username == username).first()

def update_user_password(session: Session, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
    """更新用户密码"""
    user = get_user_by_id(session, user_id)
    if not user:
        return False, "用户不存在"
    
    if not verify_password(old_password, user.password_hash):
        return False, "原密码错误"
    
    user.password_hash = hash_password(new_password)
    session.commit()
    return True, None

def can_user_access_course(session: Session, user_id: int, course_id: int) -> bool:
    """检查用户是否有权限访问课程"""
    user = get_user_by_id(session, user_id)
    if not user:
        return False
    
    # 超级管理员和学校管理员可以访问所有课程
    if user.role in ['super_admin', 'school_admin']:
        return True
    
    # 检查是否是课程创建者
    course = session.query(Course).filter(Course.course_id == course_id).first()
    if course and course.creator_id == user_id:
        return True
    
    # 检查是否有授权
    permission = session.query(UserCourse).filter(
        and_(
            UserCourse.user_id == user_id,
            UserCourse.course_id == course_id
        )
    ).first()
    
    return permission is not None

def can_user_manage_course(session: Session, user_id: int, course_id: int) -> bool:
    """检查用户是否可以管理课程（创建任务、录入成绩等）"""
    user = get_user_by_id(session, user_id)
    if not user:
        return False
    
    # 超级管理员和学校管理员可以管理所有课程
    if user.role in ['super_admin', 'school_admin']:
        return True
    
    # 检查是否是课程创建者
    course = session.query(Course).filter(Course.course_id == course_id).first()
    if course and course.creator_id == user_id:
        return True
    
    # 检查是否有教师或助教权限
    permission = session.query(UserCourse).filter(
        and_(
            UserCourse.user_id == user_id,
            UserCourse.course_id == course_id,
            UserCourse.role.in_(['teacher', 'ta'])
        )
    ).first()
    
    return permission is not None

def grant_course_permission(session: Session, user_id: int, course_id: int, 
                            role: str, granted_by: int) -> Tuple[bool, str]:
    """授予用户课程权限"""
    # 检查权限是否存在
    existing = session.query(UserCourse).filter(
        and_(
            UserCourse.user_id == user_id,
            UserCourse.course_id == course_id
        )
    ).first()
    
    if existing:
        existing.role = role
        existing.granted_by = granted_by
        existing.granted_at = datetime.now()
    else:
        permission = UserCourse(
            user_id=user_id,
            course_id=course_id,
            role=role,
            granted_by=granted_by
        )
        session.add(permission)
    
    session.commit()
    return True, None

def revoke_course_permission(session: Session, user_id: int, course_id: int) -> bool:
    """撤销用户课程权限"""
    permission = session.query(UserCourse).filter(
        and_(
            UserCourse.user_id == user_id,
            UserCourse.course_id == course_id
        )
    ).first()
    
    if permission:
        session.delete(permission)
        session.commit()
        return True
    return False

def get_user_courses(session: Session, user_id: int, include_created: bool = True):
    """获取用户可以访问的课程列表"""
    user = get_user_by_id(session, user_id)
    if not user:
        return []
    
    # 超级管理员和学校管理员可以看到所有课程
    if user.role in ['super_admin', 'school_admin']:
        return session.query(Course).all()
    
    courses = []
    
    # 获取创建的课程
    if include_created:
        created_courses = session.query(Course).filter(Course.creator_id == user_id).all()
        courses.extend(created_courses)
    
    # 获取有权限的课程
    permissions = session.query(UserCourse).filter(UserCourse.user_id == user_id).all()
    for perm in permissions:
        course = session.query(Course).filter(Course.course_id == perm.course_id).first()
        if course and course not in courses:
            courses.append(course)
    
    return courses

