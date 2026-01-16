"""
数据库管理工具
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pandas as pd
from pathlib import Path
import shutil

from config import DATABASE_PATH, BACKUP_DIR
from database.models import Base, Course, Student, Task, Grade, User, School, Semester, UserCourse, StudentCourse, init_database, get_session

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        self.engine = create_engine(f'sqlite:///{DATABASE_PATH}', echo=False)
        
        # 如果数据库已存在，先执行迁移
        if DATABASE_PATH.exists():
            from database.migrate_db import migrate_database
            migrate_database()
        
        # 确保创建所有表（对于新表）
        from database.models import Base
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.Session()
    
    def backup_database(self):
        """备份数据库"""
        if DATABASE_PATH.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = BACKUP_DIR / f"backup_{timestamp}.db"
            shutil.copy2(DATABASE_PATH, backup_file)
            return backup_file
        return None
    
    def restore_database(self, backup_file):
        """恢复数据库"""
        if Path(backup_file).exists():
            shutil.copy2(backup_file, DATABASE_PATH)
            self._init_db()
            return True
        return False
    
    def export_to_excel(self, output_path, course_id=None):
        """导出数据到Excel"""
        session = self.get_session()
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 导出课程
                courses = session.query(Course).all()
                if courses:
                    courses_data = [{
                        '课程ID': c.course_id,
                        '课程名称': c.course_name,
                        '学期': c.semester or '',
                        '教师': c.teacher or '',
                        '创建时间': c.created_at
                    } for c in courses]
                    pd.DataFrame(courses_data).to_excel(writer, sheet_name='课程', index=False)
                
                # 导出学生
                students = session.query(Student).all()
                if students:
                    students_data = [{
                        '学号': s.student_id,
                        '姓名': s.name,
                        '班级': s.class_name or '',
                        '拼音首字母': s.pinyin_initials or ''
                    } for s in students]
                    pd.DataFrame(students_data).to_excel(writer, sheet_name='学生', index=False)
                
                # 导出任务和成绩
                tasks_query = session.query(Task)
                if course_id:
                    tasks_query = tasks_query.filter(Task.course_id == course_id)
                
                tasks = tasks_query.all()
                for task in tasks:
                    grades = session.query(Grade).filter(Grade.task_id == task.task_id).all()
                    if grades:
                        grades_data = [{
                            '学号': g.student_id,
                            '姓名': g.student.name,
                            '班级': g.student.class_name or '',
                            '分数': g.score if g.score is not None else '',
                            '状态': g.status,
                            '备注': g.remark or '',
                            '提交时间': g.submitted_at if g.submitted_at else '',
                            '评分时间': g.graded_at if g.graded_at else ''
                        } for g in grades]
                        sheet_name = f"{task.task_name[:30]}"  # Excel sheet名称限制31字符
                        pd.DataFrame(grades_data).to_excel(writer, sheet_name=sheet_name, index=False)
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False
        finally:
            session.close()

# 全局数据库管理器实例
db_manager = DatabaseManager()

