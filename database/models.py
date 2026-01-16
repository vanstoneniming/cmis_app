"""
数据库模型定义
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum
from config import DATABASE_PATH

Base = declarative_base()

class UserRole(enum.Enum):
    """用户角色枚举"""
    SUPER_ADMIN = "super_admin"      # 超级管理员
    SCHOOL_ADMIN = "school_admin"    # 学校管理员
    TEACHER = "teacher"              # 教师
    TA = "ta"                        # 助教
    STUDENT = "student"              # 学生

class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, comment='邮箱')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    real_name = Column(String(100), comment='真实姓名')
    role = Column(String(20), nullable=False, default='teacher', comment='角色')
    school_id = Column(Integer, ForeignKey('schools.school_id'), comment='所属学校ID')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    last_login = Column(DateTime, comment='最后登录时间')
    
    # 关系
    school = relationship("School", back_populates="users")
    created_courses = relationship("Course", back_populates="creator", foreign_keys="Course.creator_id")
    course_permissions = relationship("UserCourse", back_populates="user", foreign_keys="UserCourse.user_id")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', role='{self.role}')>"

class School(Base):
    """学校表"""
    __tablename__ = 'schools'
    
    school_id = Column(Integer, primary_key=True, autoincrement=True)
    school_name = Column(String(200), nullable=False, comment='学校名称')
    domain = Column(String(100), comment='学校域名')
    settings = Column(Text, comment='学校配置（JSON格式）')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    users = relationship("User", back_populates="school")
    courses = relationship("Course", back_populates="school")
    semesters = relationship("Semester", back_populates="school", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="school")
    
    def __repr__(self):
        return f"<School(school_id={self.school_id}, school_name='{self.school_name}')>"

class Semester(Base):
    """学期表"""
    __tablename__ = 'semesters'
    
    semester_id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey('schools.school_id'), nullable=False, comment='所属学校ID')
    semester_name = Column(String(100), nullable=False, comment='学期名称，如：2024-2025学年第一学期')
    semester_code = Column(String(50), comment='学期代码，如：2024-2025-1')
    start_date = Column(DateTime, comment='开始日期')
    end_date = Column(DateTime, comment='结束日期')
    is_active = Column(Boolean, default=True, comment='是否当前学期')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    school = relationship("School", back_populates="semesters")
    courses = relationship("Course", back_populates="semester_obj", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Semester(semester_id={self.semester_id}, semester_name='{self.semester_name}')>"

class Course(Base):
    """课程表"""
    __tablename__ = 'courses'
    
    course_id = Column(Integer, primary_key=True, autoincrement=True)
    course_name = Column(String(200), nullable=False, comment='课程名称')
    course_code = Column(String(50), comment='课程代码')
    semester_id = Column(Integer, ForeignKey('semesters.semester_id'), nullable=True, comment='所属学期ID')
    semester = Column(String(50), comment='学期（保留，向后兼容）')
    teacher = Column(String(100), comment='授课教师（保留，向后兼容）')
    description = Column(Text, comment='课程描述')
    creator_id = Column(Integer, ForeignKey('users.user_id'), nullable=True, comment='创建者ID（主教师）')
    school_id = Column(Integer, ForeignKey('schools.school_id'), comment='所属学校ID')
    is_public = Column(Boolean, default=False, comment='是否公开')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    creator = relationship("User", back_populates="created_courses", foreign_keys=[creator_id])
    school = relationship("School", back_populates="courses")
    semester_obj = relationship("Semester", back_populates="courses", foreign_keys=[semester_id])
    tasks = relationship("Task", back_populates="course", cascade="all, delete-orphan")
    user_permissions = relationship("UserCourse", back_populates="course", cascade="all, delete-orphan")
    student_enrollments = relationship("StudentCourse", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Course(course_id={self.course_id}, course_name='{self.course_name}')>"

class UserCourse(Base):
    """用户-课程关联表（权限管理）"""
    __tablename__ = 'user_courses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, comment='用户ID')
    course_id = Column(Integer, ForeignKey('courses.course_id'), nullable=False, comment='课程ID')
    role = Column(String(20), nullable=False, default='ta', comment='在课程中的角色（teacher/ta）')
    is_primary = Column(Boolean, default=False, comment='是否为主教师（课程创建者）')
    granted_by = Column(Integer, ForeignKey('users.user_id'), comment='授权人ID')
    granted_at = Column(DateTime, default=datetime.now, comment='授权时间')
    
    # 关系
    user = relationship("User", back_populates="course_permissions", foreign_keys=[user_id])
    course = relationship("Course", back_populates="user_permissions")
    granter = relationship("User", foreign_keys=[granted_by], viewonly=True)  # viewonly避免循环引用
    
    def __repr__(self):
        return f"<UserCourse(user_id={self.user_id}, course_id={self.course_id}, role='{self.role}', is_primary={self.is_primary})>"

class Student(Base):
    """学生表"""
    __tablename__ = 'students'
    
    student_id = Column(String(50), primary_key=True, comment='学号')
    name = Column(String(100), nullable=False, comment='姓名')
    class_name = Column(String(100), comment='班级')
    pinyin_initials = Column(String(50), comment='拼音首字母')
    school_id = Column(Integer, ForeignKey('schools.school_id'), nullable=True, comment='所属学校ID')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    school = relationship("School", back_populates="students")
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")
    course_enrollments = relationship("StudentCourse", back_populates="student", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Student(student_id='{self.student_id}', name='{self.name}')>"

class StudentCourse(Base):
    """学生-课程关联表（选课关系）"""
    __tablename__ = 'student_courses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey('students.student_id'), nullable=False, comment='学号')
    course_id = Column(Integer, ForeignKey('courses.course_id'), nullable=False, comment='课程ID')
    enrollment_status = Column(String(20), default='enrolled', comment='选课状态：enrolled已选/dropped退选')
    enrolled_at = Column(DateTime, default=datetime.now, comment='选课时间')
    dropped_at = Column(DateTime, comment='退课时间')
    
    # 关系
    student = relationship("Student", back_populates="course_enrollments")
    course = relationship("Course", back_populates="student_enrollments")
    
    def __repr__(self):
        return f"<StudentCourse(student_id='{self.student_id}', course_id={self.course_id}, status='{self.enrollment_status}')>"

class Task(Base):
    """任务表（作业/考试）"""
    __tablename__ = 'tasks'
    
    task_id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.course_id'), nullable=False, comment='课程ID')
    task_name = Column(String(200), nullable=False, comment='任务名称')
    task_type = Column(String(20), nullable=False, comment='任务类型（作业/考试）')
    total_score = Column(Float, default=100.0, comment='总分')
    weight = Column(Float, default=1.0, comment='权重')
    deadline = Column(DateTime, comment='截止日期')
    status = Column(String(20), default='进行中', comment='状态')
    description = Column(Text, comment='任务描述')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    course = relationship("Course", back_populates="tasks")
    grades = relationship("Grade", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(task_id={self.task_id}, task_name='{self.task_name}', type='{self.task_type}')>"

class Grade(Base):
    """成绩表"""
    __tablename__ = 'grades'
    
    grade_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.task_id'), nullable=False, comment='任务ID')
    student_id = Column(String(50), ForeignKey('students.student_id'), nullable=False, comment='学号')
    score = Column(Float, comment='分数')
    status = Column(String(20), default='未提交', comment='提交状态')
    remark = Column(Text, comment='备注')
    submitted_at = Column(DateTime, comment='提交时间')
    graded_at = Column(DateTime, comment='评分时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    task = relationship("Task", back_populates="grades")
    student = relationship("Student", back_populates="grades")
    
    def __repr__(self):
        return f"<Grade(grade_id={self.grade_id}, task_id={self.task_id}, student_id='{self.student_id}', score={self.score})>"

class AuditLog(Base):
    """审计日志表"""
    __tablename__ = 'audit_logs'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), comment='操作用户ID')
    action = Column(String(50), nullable=False, comment='操作类型')
    resource_type = Column(String(50), comment='资源类型（course/task/grade/user等）')
    resource_id = Column(Integer, comment='资源ID')
    description = Column(Text, comment='操作描述')
    ip_address = Column(String(50), comment='IP地址')
    user_agent = Column(String(500), comment='用户代理')
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment='操作时间')
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<AuditLog(log_id={self.log_id}, user_id={self.user_id}, action='{self.action}', created_at='{self.created_at}')>"

# 创建数据库引擎
def create_engine_instance():
    """创建数据库引擎"""
    engine = create_engine(f'sqlite:///{DATABASE_PATH}', echo=False)
    return engine

def init_database():
    """初始化数据库，创建所有表"""
    engine = create_engine_instance()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """获取数据库会话"""
    engine = create_engine_instance()
    Session = sessionmaker(bind=engine)
    return Session()

