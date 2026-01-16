"""
日志查看模块
"""
import streamlit as st
import pandas as pd
import io
from sqlalchemy.orm import Session
from database.models import AuditLog, User
from modules.logging_module import AuditLogger
from datetime import datetime, timedelta
from utils.permissions import is_admin

def show_logs_page(session: Session):
    """显示日志查看页面"""
    st.header("📋 操作日志")
    
    # 检查权限
    user_role = st.session_state.get('user_role', '')
    user_id = st.session_state.get('user_id')
    
    if not is_admin(user_role) and user_role != 'teacher':
        st.warning("⚠️ 您没有权限查看日志")
        return
    
    # 筛选选项
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 操作类型筛选
        actions = ['全部'] + [
            'login', 'logout', 'create', 'update', 'delete',
            'grant_permission', 'revoke_permission'
        ]
        selected_action = st.selectbox("操作类型", actions)
        action_filter = None if selected_action == '全部' else selected_action
    
    with col2:
        # 资源类型筛选
        resource_types = ['全部', 'user', 'course', 'task', 'grade']
        selected_resource = st.selectbox("资源类型", resource_types)
        resource_filter = None if selected_resource == '全部' else selected_resource
    
    with col3:
        # 时间范围筛选
        time_ranges = ['最近1小时', '最近24小时', '最近7天', '最近30天', '全部']
        selected_time = st.selectbox("时间范围", time_ranges)
    
    # 用户筛选（仅管理员）
    user_filter = None
    if is_admin(user_role):
        st.markdown("---")
        all_users = session.query(User).all()
        user_options = ['全部用户'] + [f"{u.username} ({u.real_name})" for u in all_users]
        selected_user = st.selectbox("操作用户", user_options)
        
        if selected_user != '全部用户':
            # 提取用户名
            username = selected_user.split(' ')[0]
            user_obj = session.query(User).filter(User.username == username).first()
            if user_obj:
                user_filter = user_obj.user_id
    else:
        # 非管理员只能看自己的日志
        user_filter = user_id
    
    # 构建查询
    query = session.query(AuditLog)
    
    if user_filter:
        query = query.filter(AuditLog.user_id == user_filter)
    
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    
    if resource_filter:
        query = query.filter(AuditLog.resource_type == resource_filter)
    
    # 时间范围筛选
    if selected_time != '全部':
        now = datetime.now()
        if selected_time == '最近1小时':
            start_time = now - timedelta(hours=1)
        elif selected_time == '最近24小时':
            start_time = now - timedelta(days=1)
        elif selected_time == '最近7天':
            start_time = now - timedelta(days=7)
        elif selected_time == '最近30天':
            start_time = now - timedelta(days=30)
        else:
            start_time = None
        
        if start_time:
            query = query.filter(AuditLog.created_at >= start_time)
    
    # 获取日志
    logs = query.order_by(AuditLog.created_at.desc()).limit(500).all()
    
    if logs:
        st.info(f"📊 找到 {len(logs)} 条日志记录")
        
        # 显示统计信息
        st.markdown("### 📈 操作统计")
        col1, col2, col3, col4 = st.columns(4)
        
        action_counts = {}
        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
        
        with col1:
            st.metric("总操作数", len(logs))
        with col2:
            st.metric("操作类型数", len(action_counts))
        with col3:
            unique_users = len(set(log.user_id for log in logs if log.user_id))
            st.metric("操作用户数", unique_users)
        with col4:
            if logs:
                latest_time = max(log.created_at for log in logs)
                st.metric("最新记录", latest_time.strftime("%H:%M"))
        
        st.markdown("---")
        
        # 显示日志表格
        st.markdown("### 📋 日志详情")
        
        log_data = []
        for log in logs:
            username = "系统" if not log.user else (log.user.username or "未知")
            log_data.append({
                '时间': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                '用户': username,
                '操作': log.action,
                '资源类型': log.resource_type or '-',
                '资源ID': log.resource_id or '-',
                '描述': log.description or '-',
            })
        
        df = pd.DataFrame(log_data)
        st.dataframe(df, width='stretch', hide_index=True, height=400)
        
        # 导出日志
        if st.button("📥 导出日志到Excel"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='操作日志')
            output.seek(0)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 下载Excel",
                data=output,
                file_name=f"操作日志_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("📭 没有找到符合条件的日志记录")

