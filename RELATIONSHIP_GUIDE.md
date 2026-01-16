# 数据关系使用指南

## 数据模型关系说明

本文档说明系统中各实体之间的关系，以及如何正确使用这些关系进行数据查询和操作。

## 层级关系图

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

## 核心关系说明

### 1. 学校 → 学期 → 课程

**关系路径：**
- `School.semesters` → `Semester.courses` → `Course`

**使用示例：**
```python
# 获取学校的所有学期
school = session.query(School).first()
semesters = school.semesters

# 获取学期的所有课程
semester = session.query(Semester).first()
courses = semester.courses

# 获取课程所属的学期
course = session.query(Course).first()
semester = course.semester_obj
```

### 2. 课程 → 教师

**关系路径：**
- 主教师：`Course.creator` (通过 `creator_id`)
- 助教：`Course.user_permissions` (通过 `UserCourse`)

**使用示例：**
```python
# 获取课程的主教师
course = session.query(Course).first()
primary_teacher = course.creator

# 获取课程的所有教师（包括主教师和助教）
from modules.auth import get_course_teachers
teachers = get_course_teachers(session, course.course_id)
```

### 3. 课程 → 学生

**关系路径：**
- `Course.student_enrollments` → `StudentCourse.student`

**使用示例：**
```python
# 获取课程的所有学生
from modules.student_courses import get_course_students
students = get_course_students(session, course_id)

# 获取学生的所有课程
from modules.student_courses import get_student_courses
courses = get_student_courses(session, student_id)
```

### 4. 课程 → 任务 → 成绩

**关系路径：**
- `Course.tasks` → `Task.grades` → `Grade`

**使用示例：**
```python
# 获取课程的所有任务
course = session.query(Course).first()
tasks = course.tasks

# 获取任务的所有成绩
task = session.query(Task).first()
grades = task.grades

# 获取学生的成绩
student = session.query(Student).first()
grades = student.grades
```

## 权限和录入关系

### 教师权限

1. **主教师（课程创建者）**
   - 可以管理课程的所有信息
   - 可以创建任务
   - 可以录入成绩
   - 可以管理学生选课

2. **助教（通过UserCourse授权）**
   - 可以创建任务（根据授权）
   - 可以录入成绩（根据授权）
   - 可以查看学生信息（根据授权）

### 学生权限

1. **选课学生**
   - 可以查看自己的成绩
   - 可以查看任务信息

### 管理员权限

1. **学校管理员**
   - 可以查看所有数据
   - 可以管理学期
   - 可以管理课程

2. **超级管理员**
   - 所有权限

## 数据查询最佳实践

### 1. 按学期查询课程

```python
from modules.semesters import get_semester_courses

# 获取指定学期的所有课程
semester_id = 1
courses = get_semester_courses(session, semester_id)
```

### 2. 按课程查询学生

```python
from modules.student_courses import get_course_students

# 获取课程的所有学生（只包括已选课状态）
course_id = 1
students = get_course_students(session, course_id)
```

### 3. 按任务查询成绩

```python
from modules.grades import get_grades_by_task

# 获取任务的所有成绩
task_id = 1
grades = get_grades_by_task(session, task_id)
```

### 4. 获取课程的所有教师

```python
# 主教师
course = session.query(Course).first()
primary_teacher = course.creator

# 所有教师（包括助教）
from modules.auth import get_course_teachers
all_teachers = get_course_teachers(session, course.course_id)
```

## 数据录入流程

### 1. 创建课程流程

1. 选择或创建学期
2. 创建课程（指定学期、主教师）
3. 添加学生到课程
4. 创建任务
5. 录入成绩

### 2. 成绩录入流程

1. 选择课程
2. 选择任务
3. 系统自动显示该课程的所有学生
4. 录入成绩（基于课程学生列表）

## 注意事项

1. **学期管理**：课程必须属于一个学期，建议先创建学期再创建课程
2. **学生选课**：学生必须先添加到课程，才能为该课程的任务录入成绩
3. **权限检查**：所有操作都应该检查用户权限
4. **数据完整性**：删除操作要考虑级联关系（如删除课程会删除相关任务和成绩）
