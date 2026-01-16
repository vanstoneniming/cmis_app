"""
学生管理模块
"""
from sqlalchemy.orm import Session
from database.models import Student
from typing import List, Optional, Tuple
from utils.pinyin_utils import get_pinyin_initials
from utils.excel_handler import load_students_from_excel, identify_columns
import pandas as pd

def create_student(session: Session, student_id: str, name: str, 
                   class_name: str = None, pinyin_initials: str = None) -> Student:
    """创建学生"""
    if pinyin_initials is None:
        pinyin_initials = get_pinyin_initials(name)
    
    student = Student(
        student_id=student_id,
        name=name,
        class_name=class_name,
        pinyin_initials=pinyin_initials
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student

def get_student_by_id(session: Session, student_id: str) -> Optional[Student]:
    """根据学号获取学生"""
    return session.query(Student).filter(Student.student_id == student_id).first()

def get_all_students(session: Session) -> List[Student]:
    """获取所有学生"""
    return session.query(Student).order_by(Student.class_name, Student.name).all()

def update_student(session: Session, student_id: str, **kwargs) -> Optional[Student]:
    """更新学生信息"""
    student = get_student_by_id(session, student_id)
    if student:
        for key, value in kwargs.items():
            if hasattr(student, key) and value is not None:
                setattr(student, key, value)
        
        # 如果更新了姓名，自动更新拼音首字母
        if 'name' in kwargs and kwargs['name']:
            student.pinyin_initials = get_pinyin_initials(student.name)
        
        session.commit()
        session.refresh(student)
    return student

def import_students_from_excel(session: Session, uploaded_file, 
                                id_col=None, name_col=None, class_col=None, skiprows=0) -> Tuple[int, int, List[str]]:
    """从Excel导入学生
    参数:
        skiprows: 跳过前N行（默认0）
    返回: (成功数量, 失败数量, 错误信息列表)
    """
    # 读取Excel文件
    df, error = load_students_from_excel(uploaded_file, id_col, name_col, class_col, skiprows=skiprows)
    if error:
        return 0, 0, [error]
    
    # 自动识别列（如果未指定）
    if id_col is None or name_col is None:
        auto_id_col, auto_name_col, auto_class_col, df = identify_columns(df)
        if id_col is None:
            id_col = auto_id_col
        if name_col is None:
            name_col = auto_name_col
        if class_col is None:
            class_col = auto_class_col
    
    # 验证必需的列
    if name_col is None or name_col not in df.columns:
        return 0, 0, ["无法识别姓名列，请确保Excel文件包含姓名信息"]
    
    success_count = 0
    fail_count = 0
    errors = []
    
    # 处理每行数据
    for idx, row in df.iterrows():
        try:
            name = str(row[name_col]).strip()
            if pd.isna(name) or name == '':
                continue
            
            # 处理学号
            if id_col and id_col in df.columns:
                id_value = row[id_col]
                if pd.notna(id_value) and str(id_value).strip() != '':
                    student_id = str(id_value).strip()
                else:
                    # 如果学号列为空，生成学号
                    if class_col and class_col in df.columns and not pd.isna(row[class_col]):
                        class_name = str(row[class_col]).strip()
                        student_id = f"{class_name}_{idx+1:03d}"
                    else:
                        student_id = f"STU_{idx+1:04d}"
            else:
                # 没有学号列，生成学号
                if class_col and class_col in df.columns and not pd.isna(row[class_col]):
                    class_name = str(row[class_col]).strip()
                    student_id = f"{class_name}_{idx+1:03d}"
                else:
                    student_id = f"STU_{idx+1:04d}"
            
            # 处理班级
            class_name = None
            if class_col and class_col in df.columns and not pd.isna(row[class_col]):
                class_name = str(row[class_col]).strip()
            
            # 检查学生是否已存在（优先按学号，如果没有学号则按姓名）
            existing = None
            if id_col and id_col in df.columns and pd.notna(row[id_col]) and str(row[id_col]).strip() != '':
                existing = get_student_by_id(session, student_id)
            
            if existing:
                # 更新现有学生
                update_student(session, student_id, name=name, class_name=class_name)
                success_count += 1
            else:
                # 创建新学生
                create_student(session, student_id, name, class_name)
                success_count += 1
        except Exception as e:
            fail_count += 1
            errors.append(f"第{idx+2}行处理失败: {str(e)}")
            continue
    
    return success_count, fail_count, errors

def search_students(session: Session, keyword: str = None, class_name: str = None) -> List[Student]:
    """搜索学生"""
    query = session.query(Student)
    
    if keyword:
        # 支持拼音首字母搜索
        keyword_upper = keyword.upper()
        query = query.filter(
            (Student.name.contains(keyword)) |
            (Student.student_id.contains(keyword)) |
            (Student.pinyin_initials.contains(keyword_upper))
        )
    
    if class_name:
        query = query.filter(Student.class_name == class_name)
    
    return query.order_by(Student.class_name, Student.name).all()
