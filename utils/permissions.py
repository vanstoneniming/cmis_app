"""
权限检查工具
"""
from typing import Optional

# 权限定义
PERMISSIONS = {
    'user_management': ['super_admin', 'school_admin'],
    'course_create': ['super_admin', 'school_admin', 'teacher'],
    'course_manage_all': ['super_admin', 'school_admin'],
    'task_create': ['super_admin', 'school_admin', 'teacher', 'ta'],  # ta需要课程权限
    'grade_manage': ['super_admin', 'school_admin', 'teacher', 'ta'],  # ta需要课程权限
    'grade_view_all': ['super_admin', 'school_admin', 'teacher'],  # ta只能看授权的课程
    'grade_view_own': ['super_admin', 'school_admin', 'teacher', 'ta', 'student'],
    'data_export': ['super_admin', 'school_admin', 'teacher', 'ta'],  # ta需要课程权限
    'system_settings': ['super_admin'],
}

def has_permission(role: str, permission: str) -> bool:
    """检查角色是否有某个权限"""
    if role not in PERMISSIONS.get(permission, []):
        return False
    return True

def can_manage_users(role: str) -> bool:
    """是否可以管理用户"""
    return has_permission(role, 'user_management')

def can_create_course(role: str) -> bool:
    """是否可以创建课程"""
    return has_permission(role, 'course_create')

def can_manage_all_courses(role: str) -> bool:
    """是否可以管理所有课程"""
    return has_permission(role, 'course_manage_all')

def can_view_own_grades(role: str) -> bool:
    """是否可以查看自己的成绩"""
    return has_permission(role, 'grade_view_own')

def can_manage_grades(role: str) -> bool:
    """是否可以管理成绩"""
    return has_permission(role, 'grade_manage')

def is_admin(role: str) -> bool:
    """是否是管理员"""
    return role in ['super_admin', 'school_admin']

def is_teacher_or_above(role: str) -> bool:
    """是否是教师或以上"""
    return role in ['super_admin', 'school_admin', 'teacher']

