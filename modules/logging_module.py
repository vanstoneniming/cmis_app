"""
日志记录模块
"""
from sqlalchemy.orm import Session
from database.models import AuditLog
from datetime import datetime
from typing import Optional
import streamlit as st

class AuditLogger:
    """审计日志记录器"""
    
    @staticmethod
    def log_action(session: Session, action: str, user_id: Optional[int] = None,
                  resource_type: Optional[str] = None, resource_id: Optional[int] = None,
                  description: Optional[str] = None, ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None):
        """记录操作日志"""
        try:
            # 从session state获取用户ID（如果未提供）
            if user_id is None:
                user_id = st.session_state.get('user_id')
            
            # 获取IP和User Agent（如果可用）
            if ip_address is None:
                # Streamlit中可以通过request获取，这里简化处理
                ip_address = None
            
            log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.now()
            )
            session.add(log)
            session.commit()
            return log
        except Exception as e:
            # 日志记录失败不应该影响主业务
            session.rollback()
            print(f"日志记录失败: {e}")
            return None
    
    @staticmethod
    def log_user_action(session: Session, action: str, user_id: int, description: str):
        """记录用户相关操作"""
        return AuditLogger.log_action(
            session, action, user_id,
            resource_type='user',
            resource_id=user_id,
            description=description
        )
    
    @staticmethod
    def log_course_action(session: Session, action: str, course_id: int, description: str, user_id: Optional[int] = None):
        """记录课程相关操作"""
        return AuditLogger.log_action(
            session, action, user_id,
            resource_type='course',
            resource_id=course_id,
            description=description
        )
    
    @staticmethod
    def log_task_action(session: Session, action: str, task_id: int, description: str, user_id: Optional[int] = None):
        """记录任务相关操作"""
        return AuditLogger.log_action(
            session, action, user_id,
            resource_type='task',
            resource_id=task_id,
            description=description
        )
    
    @staticmethod
    def log_grade_action(session: Session, action: str, grade_id: int, description: str, user_id: Optional[int] = None):
        """记录成绩相关操作"""
        return AuditLogger.log_action(
            session, action, user_id,
            resource_type='grade',
            resource_id=grade_id,
            description=description
        )
    
    @staticmethod
    def log_login(session: Session, user_id: int, username: str, success: bool = True):
        """记录登录操作"""
        description = f"用户 {username} {'登录成功' if success else '登录失败'}"
        return AuditLogger.log_user_action(
            session, 'login' if success else 'login_failed', user_id, description
        )
    
    @staticmethod
    def log_logout(session: Session, user_id: int, username: str):
        """记录登出操作"""
        description = f"用户 {username} 登出"
        return AuditLogger.log_user_action(session, 'logout', user_id, description)
    
    @staticmethod
    def get_logs(session: Session, user_id: Optional[int] = None, 
                action: Optional[str] = None, resource_type: Optional[str] = None,
                limit: int = 100, offset: int = 0):
        """查询日志"""
        query = session.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_user_logs(session: Session, user_id: int, limit: int = 50):
        """获取用户的最近操作日志"""
        return AuditLogger.get_logs(session, user_id=user_id, limit=limit)

