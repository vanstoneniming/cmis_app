"""
Excel处理工具
"""
import pandas as pd
import re
from typing import Optional, Tuple

def detect_name_id_format(value):
    """检测值是否为"姓名 (学号)"格式
    返回: (是否匹配, 姓名, 学号) 或 (False, None, None)
    """
    if pd.isna(value):
        return False, None, None
    
    value_str = str(value).strip()
    # 匹配格式：姓名 (学号) 或 姓名(学号)
    # 支持中英文括号
    pattern = r'^(.+?)\s*[（(]\s*(\d+)\s*[)）]$'
    match = re.match(pattern, value_str)
    
    if match:
        name = match.group(1).strip()
        student_id = match.group(2).strip()
        return True, name, student_id
    
    return False, None, None

def split_name_id_column(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """拆分"姓名 (学号)"格式的列为姓名和学号两列
    返回: 更新后的DataFrame
    """
    df = df.copy()
    
    # 检查列中是否有符合格式的数据
    matched_count = 0
    for idx, value in df[col_name].items():
        is_match, _, _ = detect_name_id_format(value)
        if is_match:
            matched_count += 1
    
    # 如果超过50%的数据符合格式，则进行拆分
    if matched_count > len(df) * 0.5:
        # 创建姓名和学号列
        names = []
        ids = []
        
        for idx, value in df[col_name].items():
            is_match, name, student_id = detect_name_id_format(value)
            if is_match:
                names.append(name)
                ids.append(student_id)
            else:
                # 如果不符合格式，保留原值作为姓名，学号为空
                names.append(str(value).strip() if not pd.isna(value) else '')
                ids.append('')
        
        # 确定新列名
        name_col_name = f"{col_name}_姓名" if f"{col_name}_姓名" not in df.columns else f"{col_name}_name"
        id_col_name = f"{col_name}_学号" if f"{col_name}_学号" not in df.columns else f"{col_name}_id"
        
        # 添加新列
        df[name_col_name] = names
        df[id_col_name] = ids
        
        return df, name_col_name, id_col_name
    
    return df, None, None

def identify_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], Optional[str], pd.DataFrame]:
    """智能识别Excel中的列
    返回: (id_col, name_col, class_col, 更新后的DataFrame)
    """
    columns = df.columns.tolist()
    df_result = df.copy()
    
    id_col = None
    name_col = None
    class_col = None
    
    # 首先检查是否有"姓名 (学号)"格式的列
    for col in columns:
        # 检查该列是否符合"姓名 (学号)"格式
        matched_count = 0
        for idx, value in df_result[col].items():
            is_match, _, _ = detect_name_id_format(value)
            if is_match:
                matched_count += 1
                if matched_count >= 2:  # 至少找到2个匹配才认为该列需要拆分
                    break
        
        if matched_count >= 2:
            # 自动拆分该列
            df_result, new_name_col, new_id_col = split_name_id_column(df_result, col)
            if new_name_col and new_id_col:
                name_col = new_name_col
                id_col = new_id_col
                # 跳过后续的列识别，因为已经找到了
                break
    
    # 如果没有找到合并格式，则进行常规列识别
    if name_col is None:
        for col in df_result.columns:
            col_str = str(col).strip()
            col_lower = col_str.lower()
            
            # 识别学号列（优先级最高）
            if id_col is None:
                if any(keyword in col_str for keyword in ['学号', '学生编号', '编号', 'ID', 'id', 'student_id', 'studentid']):
                    if not any(exclude in col_lower for exclude in ['班级', 'class']):
                        id_col = col
            
            # 识别姓名列
            if name_col is None:
                if any(keyword in col_str for keyword in ['姓名', '名字', 'name', '学生姓名', '学生名字']):
                    name_col = col
            
            # 识别班级列
            if class_col is None:
                if any(keyword in col_str for keyword in ['班级', 'class', '班', '教学班', '行政班']):
                    class_col = col
    
    return id_col, name_col, class_col, df_result

def load_students_from_excel(file_path_or_buffer, id_col=None, name_col=None, class_col=None, skiprows=0):
    """从Excel加载学生数据，自动识别并拆分"姓名 (学号)"格式
    参数:
        skiprows: 跳过前N行（默认0）
    """
    try:
        # 支持.xlsx和.xls格式
        read_options = {}
        if skiprows and skiprows > 0:
            read_options['skiprows'] = skiprows
            # 不使用header，因为跳过后需要重新识别
            read_options['header'] = None
        
        if hasattr(file_path_or_buffer, 'name'):
            filename = file_path_or_buffer.name
            if filename.endswith('.xlsx'):
                # 重置文件指针（如果需要多次读取）
                file_path_or_buffer.seek(0)
                # 使用openpyxl引擎，避免pyarrow类型错误
                try:
                    df = pd.read_excel(file_path_or_buffer, engine='openpyxl', **read_options)
                except Exception as e:
                    # 如果失败，尝试不使用引擎
                    file_path_or_buffer.seek(0)
                    df = pd.read_excel(file_path_or_buffer, **read_options)
            elif filename.endswith('.xls'):
                file_path_or_buffer.seek(0)
                df = pd.read_excel(file_path_or_buffer, engine='xlrd', **read_options)
            else:
                return None, "请上传Excel文件（.xlsx或.xls格式）"
        else:
            # 直接是文件路径
            if str(file_path_or_buffer).endswith('.xlsx'):
                try:
                    df = pd.read_excel(file_path_or_buffer, engine='openpyxl', **read_options)
                except Exception as e:
                    df = pd.read_excel(file_path_or_buffer, **read_options)
            elif str(file_path_or_buffer).endswith('.xls'):
                df = pd.read_excel(file_path_or_buffer, engine='xlrd', **read_options)
            else:
                return None, "文件格式不支持"
        
        # 如果跳过了行，需要重新设置列名
        if skiprows and skiprows > 0:
            # 尝试将第一行作为列名
            if len(df) > 0:
                # 检查第一行是否像列名（包含"姓名"、"学号"等关键词）
                first_row = df.iloc[0].astype(str).tolist()
                has_name_keywords = any(
                    any(keyword in str(cell).lower() for keyword in ['姓名', '名字', 'name', '学号', 'id', '编号'])
                    for cell in first_row
                )
                
                if has_name_keywords:
                    # 第一行看起来像列名，使用它作为列名
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)
                else:
                    # 第一行看起来不像列名，生成默认列名
                    df.columns = [f"列{i+1}" for i in range(len(df.columns))]
        
        # 首先检查是否有需要拆分的列（"姓名 (学号)"格式）
        for col in df.columns:
            matched_count = 0
            for idx, value in df[col].items():
                is_match, _, _ = detect_name_id_format(value)
                if is_match:
                    matched_count += 1
                    if matched_count >= 2:  # 至少找到2个匹配才认为该列需要拆分
                        break
            
            if matched_count >= 2:
                # 拆分该列
                df, new_name_col, new_id_col = split_name_id_column(df, col)
                if new_name_col and new_id_col:
                    # 如果用户未指定列，使用拆分后的列
                    if name_col is None:
                        name_col = new_name_col
                    if id_col is None:
                        id_col = new_id_col
                    break
        
        # 自动识别列（如果未手动指定）
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
            return None, "无法识别姓名列，请确保Excel文件包含姓名信息"
        
        return df, None
        
    except Exception as e:
        return None, f"读取Excel文件时出错: {str(e)}"

