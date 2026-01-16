# 日志功能使用指南

## 概述

系统已集成完整的操作日志（审计日志）功能，用于记录和追踪所有重要操作。

## 功能特性

### 1. 自动日志记录
系统会自动记录以下操作：
- ✅ 用户登录/登出
- ✅ 课程创建/更新/删除
- ✅ 任务创建/更新/删除
- ✅ 成绩录入/修改
- ✅ 权限授予/撤销
- ✅ 数据导入/导出

### 2. 日志内容
每条日志包含：
- **时间**：操作发生的时间
- **用户**：执行操作的用户
- **操作类型**：操作的动作（create/update/delete等）
- **资源类型**：操作的对象类型（course/task/grade等）
- **资源ID**：操作对象的ID
- **描述**：操作的详细描述
- **IP地址**：操作来源IP（可选）
- **User Agent**：浏览器信息（可选）

### 3. 日志查询
支持多种查询条件：
- 按用户筛选
- 按操作类型筛选
- 按资源类型筛选
- 按时间范围筛选（最近1小时/24小时/7天/30天）

### 4. 权限控制
- **超级管理员**：可以查看所有日志
- **学校管理员**：可以查看所有日志
- **教师**：可以查看自己的操作日志
- **助教/学生**：无权限查看日志

## 使用方法

### 查看日志
1. 登录系统
2. 在侧边栏选择「📋 操作日志」
3. 使用筛选条件查询日志
4. 查看日志详情表格

### 导出日志
1. 在日志页面设置筛选条件
2. 点击「📥 导出日志到Excel」
3. 下载Excel文件

## 日志记录示例

### 在代码中记录日志

```python
from modules.logging_module import AuditLogger

# 记录课程创建
AuditLogger.log_course_action(
    session, 'create', course_id,
    f"创建课程: {course_name}",
    user_id
)

# 记录成绩修改
AuditLogger.log_grade_action(
    session, 'update', grade_id,
    f"修改成绩: {old_score} -> {new_score}",
    user_id
)

# 记录通用操作
AuditLogger.log_action(
    session, 'export', user_id,
    resource_type='data',
    description='导出Excel数据'
)
```

## 日志数据表

日志存储在 `audit_logs` 表中，包含以下字段：
- `log_id` - 日志ID
- `user_id` - 用户ID
- `action` - 操作类型
- `resource_type` - 资源类型
- `resource_id` - 资源ID
- `description` - 描述
- `ip_address` - IP地址
- `user_agent` - 用户代理
- `created_at` - 创建时间

## 注意事项

1. **性能**：日志记录不会影响主业务性能（异步处理或快速写入）
2. **存储**：定期清理旧日志，避免数据库过大
3. **隐私**：日志可能包含敏感信息，需要权限控制
4. **备份**：日志数据建议定期备份

## 未来扩展

- [ ] 日志自动清理（保留最近N天）
- [ ] 日志统计分析
- [ ] 异常操作告警
- [ ] 日志导出格式优化

