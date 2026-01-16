# CMIS成绩处理辅助工具 - 系统设计文档

## 系统概述

CMIS成绩处理辅助工具，支持：
- 多门课程管理
- 多种作业/考试类型
- 成绩统计分析
- 数据报表生成
- 历史记录追踪

## 核心功能模块

### 1. 课程管理模块
- 创建/编辑/删除课程
- 课程基本信息（课程名称、学期、教师等）
- 课程下的学生管理

### 2. 任务管理模块（作业/考试）
- 创建任务（作业或考试）
- 任务属性：
  - 类型：作业/考试
  - 名称、描述
  - 截止日期
  - 总分、权重
  - 状态（进行中/已截止/已归档）

### 3. 成绩录入模块
- 快速录入界面（保留现有功能）
- 批量导入成绩
- 成绩修改历史记录

### 4. 统计分析模块
- 学生个人成绩分析
- 班级成绩对比
- 任务完成率统计
- 成绩趋势分析
- 可视化报表

### 5. 数据管理模块
- 数据导入/导出
- 数据备份/恢复
- 历史版本管理

## 数据模型设计

### 课程表 (Courses)
- course_id: 课程ID
- course_name: 课程名称
- semester: 学期
- teacher: 授课教师
- created_at: 创建时间

### 学生表 (Students)
- student_id: 学号
- name: 姓名
- class: 班级
- pinyin_initials: 拼音首字母

### 任务表 (Tasks)
- task_id: 任务ID
- course_id: 所属课程
- task_name: 任务名称
- task_type: 类型（作业/考试）
- total_score: 总分
- weight: 权重
- deadline: 截止日期
- status: 状态
- created_at: 创建时间

### 成绩表 (Grades)
- grade_id: 成绩ID
- task_id: 任务ID
- student_id: 学生ID
- score: 分数
- status: 提交状态
- remark: 备注
- submitted_at: 提交时间
- graded_at: 评分时间

## 技术架构

### 前端
- Streamlit（Web界面）
- 多页面架构（使用Streamlit的页面路由）

### 数据存储
- SQLite数据库（轻量级，适合单用户/小团队）
- 可选升级：PostgreSQL/MySQL（多用户场景）

### 数据分析
- Pandas（数据处理）
- Plotly/Altair（图表可视化）

## 实施计划

### Phase 1: 基础架构重构
1. 设计数据库模型
2. 实现数据访问层
3. 重构现有功能到新架构

### Phase 2: 核心功能实现
1. 课程管理
2. 任务管理
3. 成绩录入（迁移现有功能）

### Phase 3: 高级功能
1. 统计分析增强
2. 报表生成
3. 数据导入/导出优化

### Phase 4: 用户体验优化
1. UI/UX改进
2. 性能优化
3. 文档完善

## 文件结构

```
oa/
├── app.py                 # 主应用入口
├── config.py              # 配置文件
├── database/
│   ├── models.py          # 数据模型定义
│   ├── db_manager.py      # 数据库管理
│   └── migrations/        # 数据库迁移脚本
├── modules/
│   ├── courses.py         # 课程管理模块
│   ├── tasks.py           # 任务管理模块
│   ├── grades.py          # 成绩管理模块
│   ├── statistics.py      # 统计分析模块
│   └── reports.py         # 报表生成模块
├── utils/
│   ├── excel_handler.py   # Excel处理工具
│   ├── pinyin_utils.py    # 拼音工具
│   └── validators.py      # 数据验证
├── pages/                 # Streamlit多页面
│   ├── 1_课程管理.py
│   ├── 2_任务管理.py
│   ├── 3_成绩录入.py
│   └── 4_统计分析.py
├── data/                  # 数据目录
│   └── database.db        # SQLite数据库
└── requirements.txt       # 依赖列表
```

