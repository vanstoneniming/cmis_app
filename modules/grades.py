"""
成绩管理模块
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database.models import Grade, Task, Student
from typing import List, Optional, Tuple
from modules.logging_module import AuditLogger
import streamlit as st
from datetime import datetime

def create_or_update_grade(session: Session, task_id: int, student_id: str, 
                          score: float = None, status: str = '未提交', 
                          remark: str = None) -> Grade:
    """创建或更新成绩记录"""
    # 检查成绩是否已存在
    grade = session.query(Grade).filter(
        and_(
            Grade.task_id == task_id,
            Grade.student_id == student_id
        )
    ).first()
    
    if grade:
        # 更新现有成绩
        if score is not None:
            grade.score = score
            grade.status = '已提交' if status == '已提交' else grade.status
            grade.graded_at = datetime.now()
        if status:
            grade.status = status
            if status == '已提交' and not grade.submitted_at:
                grade.submitted_at = datetime.now()
        if remark is not None:
            grade.remark = remark
        grade.updated_at = datetime.now()
    else:
        # 创建新成绩
        grade = Grade(
            task_id=task_id,
            student_id=student_id,
            score=score,
            status=status,
            remark=remark
        )
        if status == '已提交':
            grade.submitted_at = datetime.now()
        if score is not None:
            grade.graded_at = datetime.now()
        session.add(grade)
    
    session.commit()
    session.refresh(grade)
    return grade

def get_grade_by_id(session: Session, grade_id: int) -> Optional[Grade]:
    """根据ID获取成绩"""
    return session.query(Grade).filter(Grade.grade_id == grade_id).first()

def get_grades_by_task(session: Session, task_id: int) -> List[Grade]:
    """获取指定任务的所有成绩"""
    return session.query(Grade).filter(Grade.task_id == task_id).all()

def get_student_grades(session: Session, student_id: str, course_id: int = None) -> List[Grade]:
    """获取学生的成绩列表（可指定课程）"""
    query = session.query(Grade).filter(Grade.student_id == student_id)
    
    if course_id:
        # 通过Task关联到Course
        query = query.join(Task).filter(Task.course_id == course_id)
    
    return query.all()

def delete_grade(session: Session, grade_id: int) -> bool:
    """删除成绩记录"""
    grade = get_grade_by_id(session, grade_id)
    if grade:
        session.delete(grade)
        session.commit()
        return True
    return False

def bulk_update_grades(session: Session, task_id: int, grade_data: List[dict]) -> Tuple[int, int]:
    """批量更新成绩
    返回: (成功数量, 失败数量)
    """
    success_count = 0
    fail_count = 0
    
    for data in grade_data:
        try:
            student_id = data.get('student_id')
            score = data.get('score')
            status = data.get('status', '未提交')
            remark = data.get('remark')
            
            if student_id:
                create_or_update_grade(
                    session, task_id, student_id,
                    score=score, status=status, remark=remark
                )
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            fail_count += 1
            continue
    
    return success_count, fail_count

def import_grades_from_excel(session: Session, course_id: int, df, name_col: str, score_cols: List[str], task_type: str = '作业') -> Tuple[int, int, int, List[str]]:
    """从Excel导入成绩（每个成绩列创建独立任务）
    参数:
        session: 数据库会话
        course_id: 课程ID（用于创建任务）
        df: Excel数据的DataFrame
        name_col: 姓名列名（用于匹配学生）
        score_cols: 成绩列名列表（每个列将创建一个独立任务）
        task_type: 任务类型（默认为'作业'）
    返回: (创建任务数, 成功数量, 失败数量, 错误信息列表)
    """
    from database.models import Student, Task
    from modules.tasks import create_task, get_tasks_by_course
    
    if name_col not in df.columns:
        return 0, 0, 0, [f"姓名列 '{name_col}' 不存在于Excel文件中"]
    
    # 验证成绩列
    missing_cols = [col for col in score_cols if col not in df.columns]
    if missing_cols:
        return 0, 0, 0, [f"成绩列不存在: {', '.join(missing_cols)}"]
    
    # 获取所有学生（创建姓名到学生ID的映射，处理重名情况）
    all_students = session.query(Student).all()
    name_to_students = {}  # 姓名 -> [学生列表]（可能有重名）
    for student in all_students:
        name = student.name.strip()
        if name not in name_to_students:
            name_to_students[name] = []
        name_to_students[name].append(student)
    
    # 获取课程的所有现有任务，用于检查任务是否已存在
    existing_tasks = get_tasks_by_course(session, course_id)
    task_name_to_id = {task.task_name: task.task_id for task in existing_tasks}
    
    # 为每个成绩列创建或获取任务
    score_col_to_task_id = {}
    created_task_count = 0
    errors = []
    
    for score_col in score_cols:
        task_name = str(score_col).strip()
        
        # 检查任务是否已存在
        if task_name in task_name_to_id:
            score_col_to_task_id[score_col] = task_name_to_id[task_name]
        else:
            # 计算该列的最大值作为总分（可选：默认为100）
            max_score = 100.0
            for idx, row in df.iterrows():
                try:
                    score_val = row[score_col]
                    if pd.notna(score_val):
                        score_float = float(score_val)
                        if score_float > max_score:
                            max_score = score_float
                except (ValueError, TypeError):
                    continue
            
            # 创建新任务
            new_task = create_task(
                session, course_id, task_name, task_type,
                total_score=max_score * 1.2 if max_score > 0 else 100.0,  # 留20%余量
                status='进行中'
            )
            if new_task:
                score_col_to_task_id[score_col] = new_task.task_id
                task_name_to_id[task_name] = new_task.task_id
                created_task_count += 1
            else:
                errors.append(f"创建任务 '{task_name}' 失败")
    
    success_count = 0
    fail_count = 0
    
    # 为每个成绩列导入成绩
    for score_col in score_cols:
        if score_col not in score_col_to_task_id:
            continue
        
        task_id = score_col_to_task_id[score_col]
        
        # 处理每一行
        for idx, row in df.iterrows():
            try:
                name = str(row[name_col]).strip()
                if pd.isna(name) or name == '':
                    continue
                
                # 根据姓名查找学生
                if name not in name_to_students:
                    fail_count += 1
                    errors.append(f"第{idx+2}行 [{score_col}]: 未找到姓名为 '{name}' 的学生")
                    continue
                
                # 如果有重名，使用第一个
                matched_students = name_to_students[name]
                if len(matched_students) > 1:
                    errors.append(f"第{idx+2}行 [{score_col}]: 姓名为 '{name}' 的学生有多个匹配，使用第一个（学号: {matched_students[0].student_id}）")
                
                student = matched_students[0]
                
                # 获取成绩值
                score_val = row[score_col]
                score_float = None
                
                if pd.notna(score_val):
                    try:
                        score_float = float(score_val)
                    except (ValueError, TypeError):
                        fail_count += 1
                        errors.append(f"第{idx+2}行 [{score_col}]: 成绩值 '{score_val}' 无法转换为数字")
                        continue
                
                # 如果找到成绩，更新状态为已提交
                status = '已提交' if score_float is not None else '未提交'
                
                # 创建或更新成绩
                create_or_update_grade(
                    session, task_id, student.student_id,
                    score=score_float, status=status
                )
                success_count += 1
                
            except Exception as e:
                fail_count += 1
                errors.append(f"第{idx+2}行 [{score_col}] 处理失败: {str(e)}")
                continue
    
    return created_task_count, success_count, fail_count, errors
