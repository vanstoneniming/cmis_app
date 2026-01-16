# 数据模型设计文档

## 设计目标

优化课程、学生、任务、教师、学期等关系，使其更清晰、更易维护，支持相关人员录入和查看。

## 层级关系

```
学校 (School)
  ├── 学期 (Semester)
  │     └── 课程 (Course)
  │           ├── 任务 (Task)
  │           │     └── 成绩 (Grade)
  │           ├── 教师 (User via UserCourse)
  │           └── 学生 (Student via StudentCourse)
  ├── 教师 (User - Teacher)
  └── 学生 (Student)
```

## 核心实体关系

### 1. 学校 (School)
- 顶层实体
- 包含多个学期、教师、学生

### 2. 学期 (Semester) - **新增**
- 属于学校
- 包含多个课程
- 有开始和结束时间
- 例如：2024-2025学年第一学期

### 3. 课程 (Course)
- 属于学期（通过semester_id关联）
- 有主教师（creator_id）
- 可以有多个助教（通过UserCourse）
- 包含多个任务
- 包含多个学生（通过StudentCourse）

### 4. 教师 (User)
- 属于学校
- 可以创建课程（creator_id）
- 可以被授权管理课程（UserCourse）
- 角色：主教师（creator）或助教（UserCourse.role='ta'）

### 5. 学生 (Student)
- 属于学校（通过school_id关联）
- 可以选多个课程（StudentCourse）
- 有成绩记录（Grade）

### 6. 任务 (Task)
- 属于课程
- 包含多个成绩记录

### 7. 成绩 (Grade)
- 属于任务
- 属于学生
- 记录分数和状态

## 关联关系表

### UserCourse（用户-课程关联）
- 用途：教师和助教与课程的关联
- 字段：
  - user_id: 用户ID
  - course_id: 课程ID
  - role: 角色（'teacher'主教师/'ta'助教）
  - is_primary: 是否为主教师（新增）
  - granted_by: 授权人
  - granted_at: 授权时间

### StudentCourse（学生-课程关联）
- 用途：学生选课关系
- 字段：
  - student_id: 学号
  - course_id: 课程ID
  - enrollment_status: 选课状态（'enrolled'已选/'dropped'退选）
  - enrolled_at: 选课时间

## 优化点

1. **学期独立管理**
   - 创建学期表，学期信息不再只是字符串
   - 支持学期开始/结束时间
   - 支持按学期筛选课程

2. **教师角色明确**
   - 主教师：课程的创建者（creator_id）
   - 助教：通过UserCourse授权
   - 在UserCourse中增加is_primary字段区分主教师和助教

3. **学生选课状态**
   - 在StudentCourse中增加enrollment_status字段
   - 支持学生退选、重新选课

4. **数据完整性**
   - 所有实体都关联到学校
   - 课程必须属于一个学期
   - 任务必须属于一个课程
   - 成绩必须属于一个任务和一个学生

## 权限设计

### 录入权限
- **课程创建者（主教师）**：可以管理课程、创建任务、录入成绩、管理学生
- **助教**：可以创建任务、录入成绩、查看学生（根据授权）
- **学校管理员**：可以查看所有数据、管理学期

### 查看权限
- **教师**：可以查看自己管理的课程的所有数据
- **学生**：可以查看自己的成绩
- **管理员**：可以查看所有数据
