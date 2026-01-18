import streamlit as st
import pandas as pd
import io
import os
import pickle
import re
from datetime import datetime
from pathlib import Path
from pypinyin import lazy_pinyin, Style

# 页面配置
st.set_page_config(
    page_title="CMIS数据合并工具",
    page_icon="📚",
    layout="wide"
)

# 数据文件路径
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "grades_data.pkl"

def save_data():
    """保存数据到本地文件"""
    try:
        # 确保数据目录存在
        DATA_DIR.mkdir(exist_ok=True)
        if st.session_state.get('grades_df') is not None:
            current_time = datetime.now().isoformat()
            data = {
                'students_df': st.session_state.get('students_df'),
                'grades_df': st.session_state.get('grades_df'),
                'last_saved': current_time
            }
            with open(DATA_FILE, 'wb') as f:
                pickle.dump(data, f)
            # 更新session state中的保存时间，以便立即显示
            st.session_state.last_saved_time = current_time
            st.session_state.data_loaded = True
            return True
        return False
    except Exception as e:
        # 在Streamlit上下文中才显示错误
        try:
            st.error(f"保存数据失败: {str(e)}")
        except:
            # 如果不在Streamlit上下文，只打印日志
            print(f"保存数据失败: {str(e)}")
        return False

def load_data():
    """从本地文件加载数据"""
    try:
        # 确保数据目录存在
        DATA_DIR.mkdir(exist_ok=True)
        if DATA_FILE.exists():
            with open(DATA_FILE, 'rb') as f:
                data = pickle.load(f)
            return data.get('students_df'), data.get('grades_df'), data.get('last_saved')
        return None, None, None
    except Exception as e:
        # 在Streamlit上下文中才显示错误
        try:
            st.error(f"加载数据失败: {str(e)}")
        except:
            # 如果不在Streamlit上下文，只打印日志
            print(f"加载数据失败: {str(e)}")
        return None, None, None

def update_data_and_save(func, *args, **kwargs):
    """执行数据更新函数并自动保存"""
    result = func(*args, **kwargs)
    save_data()
    return result

# 初始化session state的函数
# 将初始化移到main()函数内部，避免在模块导入时访问Streamlit上下文
def init_session_state():
    """初始化session state，避免在模块级别访问Streamlit上下文"""
    # Streamlit Cloud 部署时不自动加载本地数据文件，避免携带测试数据
    if 'students_df' not in st.session_state:
        # 检查是否在 Streamlit Cloud 环境（通过环境变量判断）
        is_streamlit_cloud = os.environ.get('STREAMLIT_SHARING_MODE') == 'true' or os.environ.get('STREAMLIT_SERVER_PORT')
        
        # 只在非 Streamlit Cloud 环境尝试加载已保存的数据
        if not is_streamlit_cloud:
            loaded_students, loaded_grades, last_saved = load_data()
            if loaded_students is not None and loaded_grades is not None:
                st.session_state.students_df = loaded_students
                st.session_state.grades_df = loaded_grades
                st.session_state.data_loaded = True
                st.session_state.last_saved_time = last_saved
            else:
                st.session_state.students_df = None
                st.session_state.grades_df = None
                st.session_state.data_loaded = False
        else:
            # Streamlit Cloud 环境，不加载本地数据
            st.session_state.students_df = None
            st.session_state.grades_df = None
            st.session_state.data_loaded = False

    if 'grades_df' not in st.session_state:
        st.session_state.grades_df = None

    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False

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

def split_name_id_column(df, col_name):
    """拆分"姓名 (学号)"格式的列为姓名和学号两列
    返回: (更新后的DataFrame, 姓名列名, 学号列名) 或 (原DataFrame, None, None)
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
        
        # 确定新列名（统一格式，便于匹配）
        # 如果原列名是"列X"格式，新列名保持"列X_姓名"格式
        # 否则使用原列名作为前缀
        if col_name.startswith('列') and col_name[1:].isdigit():
            # 原列名是"列X"格式
            name_col_name = f"{col_name}_姓名"
            id_col_name = f"{col_name}_学号"
        else:
            # 原列名是其他格式
            name_col_name = f"{col_name}_姓名" if f"{col_name}_姓名" not in df.columns else f"{col_name}_name"
            id_col_name = f"{col_name}_学号" if f"{col_name}_学号" not in df.columns else f"{col_name}_id"
        
        # 确保列名唯一
        counter = 1
        original_name_col = name_col_name
        original_id_col = id_col_name
        while name_col_name in df.columns:
            name_col_name = f"{original_name_col}_{counter}"
            counter += 1
        
        counter = 1
        while id_col_name in df.columns:
            id_col_name = f"{original_id_col}_{counter}"
            counter += 1
        
        # 添加新列
        df[name_col_name] = names
        df[id_col_name] = ids
        
        return df, name_col_name, id_col_name
    
    return df, None, None

def identify_columns(df):
    """智能识别Excel中的列，支持"姓名 (学号)"格式的自动拆分"""
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
                # 更新columns列表以反映新的列
                columns = df_result.columns.tolist()
                # 跳过后续的列识别，因为已经找到了
                break
    
    # 如果没有找到合并格式，则进行常规列识别
    if name_col is None:
        for col in columns:
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

def handle_duplicate_columns(df):
    """处理DataFrame中的重复列名，自动重命名重复的列
    返回: 处理后的DataFrame
    """
    df = df.copy()
    if df.columns.duplicated().any():
        # 有重复列名，需要处理
        new_columns = []
        column_counts = {}
        
        for col in df.columns:
            base_col_name = str(col)
            if base_col_name in new_columns:
                # 列名重复，添加后缀
                count = column_counts.get(base_col_name, 0) + 1
                column_counts[base_col_name] = count
                new_col_name = f"{base_col_name}_{count}"
                # 确保新名称也不重复
                while new_col_name in new_columns:
                    count += 1
                    new_col_name = f"{base_col_name}_{count}"
                new_columns.append(new_col_name)
            else:
                new_columns.append(base_col_name)
                column_counts[base_col_name] = 0
        
        df.columns = new_columns
    
    return df

def detect_numeric_text_column(df, col):
    """检测列是否包含可转换为数字的文本值
    返回: (是否为数字文本列, 可转换的比例)
    """
    if df[col].empty:
        return False, 0.0
    
    # 计算非空值数量
    non_null_count = df[col].notna().sum()
    if non_null_count == 0:
        return False, 0.0
    
    # 尝试转换所有非空值为数字
    numeric_count = 0
    sample_size = min(50, non_null_count)  # 只检查前50个值，提高性能
    
    for val in df[col].dropna().head(sample_size):
        try:
            # 去除空格和其他字符
            val_str = str(val).strip()
            # 尝试转换为数字（支持小数）
            float(val_str)
            numeric_count += 1
        except (ValueError, TypeError):
            pass
    
    # 如果超过70%的值可以转换为数字，认为这是数字文本列
    ratio = numeric_count / sample_size if sample_size > 0 else 0
    return ratio >= 0.7, ratio

def normalize_dataframe_types(df):
    """规范化DataFrame的数据类型，避免pyarrow类型错误
    保留数值列的类型，将文本格式的数字转换为数字类型
    对于文本类型的列（如学校、班级），保持为文本类型
    确保每列的类型一致性，避免混合类型导致的pyarrow错误
    """
    df = df.copy()
    
    # 首先统一所有列名为字符串类型，避免混合类型列名警告
    df.columns = [str(col) for col in df.columns]
    
    # 需要保留数值类型的列名关键词
    numeric_keywords = ['评分', '分数', 'score', '成绩', '总分', '平均分', '数量', 'count']
    # 文本类型的列名关键词（不应转换为数字）
    text_keywords = ['学校', '班级', 'class', 'school', '名称', 'name']
    
    for col in df.columns:
        col_str = str(col).lower()
        
        # 检查是否是文本类型列（如学校、班级等）
        is_text_col = any(keyword in col_str for keyword in text_keywords)
        
        # 检查是否是数值列（通过关键词）
        is_numeric_col = any(keyword in col_str for keyword in numeric_keywords)
        
        # 检查是否已经是数值类型
        is_already_numeric = pd.api.types.is_numeric_dtype(df[col])
        
        # 如果已经是数值类型，直接保留
        if is_already_numeric:
            continue
        
        # 对于文本类型列，确保全部转换为字符串类型（避免混合类型）
        if is_text_col and not is_numeric_col:
            try:
                # 统一转换为字符串类型，确保类型一致
                df[col] = df[col].astype(str)
                # 将字符串形式的NaN和空值统一处理
                df[col] = df[col].replace(['nan', 'None', 'NaN', 'NaT', 'NaT', '<NA>'], '')
                # 确保类型是object（字符串），避免pyarrow问题
                df[col] = df[col].astype('string')
            except Exception:
                # 如果转换失败，强制转换为字符串
                try:
                    df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN', 'NaT'], '')
                except:
                    pass
            continue
        
        # 如果通过关键词识别为数值列，或者检测到包含数字文本
        if is_numeric_col or (not is_already_numeric):
            # 检测该列是否包含可转换为数字的文本
            is_numeric_text, ratio = detect_numeric_text_column(df, col)
            
            if is_numeric_col or is_numeric_text:
                # 对于数值列或数字文本列，尝试转换为数值类型
                try:
                    # 先清理文本：去除空格、特殊字符等
                    if df[col].dtype == 'object':
                        # 对于文本类型，先尝试清理
                        cleaned = df[col].astype(str).str.strip()
                        # 将空字符串、'nan'等替换为NaN
                        cleaned = cleaned.replace(['', 'nan', 'None', 'NaN', 'NaT', '<NA>'], pd.NA)
                    else:
                        cleaned = df[col]
                    
                    # 转换为数字（coerce会将无法转换的值设为NaN）
                    df[col] = pd.to_numeric(cleaned, errors='coerce')
                    # 确保是float64类型，避免混合类型
                    df[col] = df[col].astype('float64')
                except Exception:
                    # 如果转换失败，转为字符串类型
                    try:
                        df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN', 'NaT'], '')
                    except:
                        pass
            else:
                # 对于非数值列，统一转换为字符串类型，避免混合类型
                try:
                    # 统一转换为字符串
                    df[col] = df[col].astype(str)
                    # 清理无效值
                    df[col] = df[col].replace(['nan', 'None', 'NaN', 'NaT', 'NaT', '<NA>'], '')
                    # 使用string类型确保一致性
                    df[col] = df[col].astype('string')
                except Exception:
                    # 如果转换失败，保持原样
                    pass
    
    return df

def load_student_list(uploaded_file, id_col=None, name_col=None, class_col=None, skiprows=0, skipfooter=0, sheet_name=None):
    """加载Excel学生名单
    参数:
        skiprows: 跳过前N行（默认0）
        skipfooter: 跳过尾部N行（默认0）
        sheet_name: 工作表名称（None表示读取所有工作表并合并）
    """
    try:
        # 确保skiprows和skipfooter是整数类型
        skiprows = int(skiprows) if skiprows else 0
        skipfooter = int(skipfooter) if skipfooter else 0
        
        # 支持.xlsx和.xls格式
        read_options = {}
        if skiprows and skiprows > 0:
            read_options['skiprows'] = int(skiprows)  # 确保是整数类型
            read_options['header'] = None  # 跳过后不使用第一行作为列名
        if skipfooter and skipfooter > 0:
            read_options['skipfooter'] = int(skipfooter)  # 确保是整数类型，跳过尾部行
        
        # 获取所有工作表名称
        if uploaded_file.name.endswith('.xlsx'):
            uploaded_file.seek(0)
            try:
                excel_file = pd.ExcelFile(uploaded_file, engine='openpyxl')
                sheet_names = excel_file.sheet_names
            except:
                uploaded_file.seek(0)
                excel_file = pd.ExcelFile(uploaded_file)
                sheet_names = excel_file.sheet_names
        elif uploaded_file.name.endswith('.xls'):
            uploaded_file.seek(0)
            excel_file = pd.ExcelFile(uploaded_file, engine='xlrd')
            sheet_names = excel_file.sheet_names
        else:
            st.error("请上传Excel文件（.xlsx或.xls格式）")
            return None
        
        # 读取数据
        all_dfs = []
        sheets_to_read = [sheet_name] if sheet_name else sheet_names
        
        for sheet in sheets_to_read:
            uploaded_file.seek(0)
            
            if uploaded_file.name.endswith('.xlsx'):
                uploaded_file.seek(0)
                try:
                    # 确保所有参数都是正确的类型
                    safe_read_opts = {}
                    if 'skiprows' in read_options:
                        safe_read_opts['skiprows'] = int(read_options['skiprows'])
                    if 'skipfooter' in read_options:
                        safe_read_opts['skipfooter'] = int(read_options['skipfooter'])
                    if 'header' in read_options:
                        safe_read_opts['header'] = read_options['header']
                    # openpyxl支持skipfooter参数
                    df = pd.read_excel(uploaded_file, sheet_name=sheet, engine='openpyxl', **safe_read_opts)
                except Exception as e:
                    # 如果失败，尝试手动处理skipfooter
                    uploaded_file.seek(0)
                    if 'skipfooter' in read_options:
                        skipfooter_val = int(read_options.pop('skipfooter', 0))
                        safe_read_opts = {}
                        if 'skiprows' in read_options:
                            safe_read_opts['skiprows'] = int(read_options['skiprows'])
                        if 'header' in read_options:
                            safe_read_opts['header'] = read_options['header']
                        df = pd.read_excel(uploaded_file, sheet_name=sheet, engine='openpyxl', **safe_read_opts)
                        # 手动删除尾部行
                        if skipfooter_val > 0 and len(df) > skipfooter_val:
                            df = df.iloc[:-skipfooter_val].reset_index(drop=True)
                    else:
                        safe_read_opts = {}
                        if 'skiprows' in read_options:
                            safe_read_opts['skiprows'] = int(read_options['skiprows'])
                        if 'header' in read_options:
                            safe_read_opts['header'] = read_options['header']
                        df = pd.read_excel(uploaded_file, sheet_name=sheet, **safe_read_opts)
            elif uploaded_file.name.endswith('.xls'):
                uploaded_file.seek(0)
                # xlrd引擎不支持skipfooter，需要手动处理
                if 'skipfooter' in read_options:
                    skipfooter_val = int(read_options.pop('skipfooter', 0))
                    safe_read_opts = {}
                    if 'skiprows' in read_options:
                        safe_read_opts['skiprows'] = int(read_options['skiprows'])
                    if 'header' in read_options:
                        safe_read_opts['header'] = read_options['header']
                    df = pd.read_excel(uploaded_file, sheet_name=sheet, engine='xlrd', **safe_read_opts)
                    # 手动删除尾部行
                    if skipfooter_val > 0 and len(df) > skipfooter_val:
                        df = df.iloc[:-skipfooter_val].reset_index(drop=True)
                else:
                    safe_read_opts = {}
                    if 'skiprows' in read_options:
                        safe_read_opts['skiprows'] = int(read_options['skiprows'])
                    if 'header' in read_options:
                        safe_read_opts['header'] = read_options['header']
                    df = pd.read_excel(uploaded_file, sheet_name=sheet, engine='xlrd', **safe_read_opts)
            
            # 如果读取多个工作表，从工作表名称提取班级信息
            if len(sheets_to_read) > 1:
                df['_工作表名称'] = sheet  # 临时列，用于标识来源工作表
            
            all_dfs.append(df)
        
        # 合并所有工作表
        if len(all_dfs) > 1:
            df = pd.concat(all_dfs, ignore_index=True)
            # 如果数据中没有班级列，尝试从工作表名称中提取
            if '_工作表名称' in df.columns:
                # 从工作表名称提取班级名（去除数字、特殊字符等）
                if class_col is None or class_col not in df.columns:
                    # 使用工作表名称作为班级
                    df['_班级_从工作表'] = df['_工作表名称']
                    if class_col is None:
                        class_col = '_班级_从工作表'
                # 移除临时列
                if '_工作表名称' in df.columns:
                    df = df.drop(columns=['_工作表名称'])
        else:
            df = all_dfs[0]
        
        # 处理重复列名（在设置列名之前先处理pandas读取时可能产生的重复）
        df = handle_duplicate_columns(df)
        
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
                    # 清理NaN值，替换为默认列名，并处理重复列名
                    new_columns = []
                    column_counts = {}  # 用于跟踪每个列名出现的次数
                    
                    for i, val in enumerate(df.iloc[0]):
                        val_str = str(val).strip()
                        if pd.isna(val) or val_str == '' or val_str.lower() in ['nan', 'none', 'nat']:
                            base_col_name = f"列{i+1}"
                        else:
                            base_col_name = val_str
                        
                        # 处理重复列名：如果列名已存在，添加后缀
                        if base_col_name in new_columns:
                            # 计算已使用的次数
                            count = column_counts.get(base_col_name, 0) + 1
                            column_counts[base_col_name] = count
                            new_col_name = f"{base_col_name}_{count}"
                            # 确保新名称也不重复
                            while new_col_name in new_columns:
                                count += 1
                                new_col_name = f"{base_col_name}_{count}"
                            new_columns.append(new_col_name)
                        else:
                            new_columns.append(base_col_name)
                            column_counts[base_col_name] = 0
                    
                    df.columns = new_columns
                    df = df[1:].reset_index(drop=True)
                else:
                    # 第一行看起来不像列名，生成默认列名
                    df.columns = [f"列{i+1}" for i in range(len(df.columns))]
        
        # 自动识别列（如果未手动指定）
        # 先尝试自动识别，即使某些列已经指定，也要检查是否需要拆分列
        auto_id_col, auto_name_col, auto_class_col, df = identify_columns(df)
        
        # 如果用户指定的列名不存在，尝试使用自动识别的结果
        if name_col and name_col not in df.columns:
            # 用户指定的列名不存在，使用自动识别的
            name_col = auto_name_col
        elif name_col is None:
            name_col = auto_name_col
        
        if id_col and id_col not in df.columns:
            id_col = auto_id_col
        elif id_col is None:
            id_col = auto_id_col
            
        if class_col and class_col not in df.columns:
            class_col = auto_class_col
        elif class_col is None:
            class_col = auto_class_col
        
        # 验证必需的列
        if name_col is None or name_col not in df.columns:
            # 尝试模糊匹配：查找包含"姓名"的列
            name_candidates = [col for col in df.columns if '姓名' in str(col) or 'name' in str(col).lower()]
            if name_candidates:
                name_col = name_candidates[0]
                st.warning(f"⚠️ 自动使用列 '{name_col}' 作为姓名列")
            else:
                # 显示所有可用的列名，帮助调试
                available_cols = ", ".join([f"'{str(col)}'" for col in df.columns[:15]])
                if len(df.columns) > 15:
                    available_cols += f" ... 共{len(df.columns)}列"
                error_msg = f"无法识别姓名列，请确保Excel文件包含姓名信息。\n\n当前可用列名：\n{available_cols}"
                if name_col:
                    error_msg += f"\n\n⚠️ 指定的列名 '{name_col}' 不存在。"
                    error_msg += "\n\n💡 提示：请检查列名是否正确，或者重新选择列映射。"
                st.error(error_msg)
                return None
        
        # 处理学号列
        if id_col and id_col in df.columns:
            # 有学号列，直接使用
            student_id = df[id_col].astype(str).str.strip()
        else:
            # 没有学号列，生成唯一标识符
            # 如果有班级，使用：班级_序号；否则使用：序号
            if class_col and class_col in df.columns:
                class_data = df[class_col].astype(str).str.strip()
                # 生成：班级_序号 格式的ID
                student_id = class_data + '_' + (df.index + 1).astype(str).str.zfill(3)
            else:
                # 只使用序号
                student_id = 'STU_' + (df.index + 1).astype(str).str.zfill(4)
        
        # 创建标准化的学生名单，保留所有原始列
        student_df = df.copy()
        
        # 确保学号列存在（使用标准列名）
        student_df['学号'] = student_id
        
        # 确保姓名列存在（使用标准列名，如果原列名不同则重命名）
        if name_col != '姓名':
            student_df['姓名'] = df[name_col].astype(str).str.strip()
            # 删除原列名（如果不同）
            if name_col in student_df.columns and name_col != '姓名':
                student_df = student_df.drop(columns=[name_col])
        else:
            student_df['姓名'] = student_df['姓名'].astype(str).str.strip()
        
        # 确保班级列存在（使用标准列名）
        if class_col and class_col in df.columns:
            if class_col != '班级':
                student_df['班级'] = df[class_col].astype(str).str.strip()
                # 删除原列名（如果不同）
                if class_col in student_df.columns and class_col != '班级':
                    student_df = student_df.drop(columns=[class_col])
            else:
                student_df['班级'] = student_df['班级'].astype(str).str.strip()
        else:
            student_df['班级'] = ''
        
        # 移除空行
        student_df = student_df[student_df['姓名'].notna() & (student_df['姓名'].str.strip() != '')]
        student_df = student_df.reset_index(drop=True)
        
        # 只保留班级、姓名、学号这三列，删除其他所有列（包括作业状态、评分、备注等）
        required_cols = ['学号', '姓名', '班级']
        available_cols = [col for col in required_cols if col in student_df.columns]
        student_df = student_df[available_cols].copy()
        
        # 规范化数据类型，避免pyarrow错误
        student_df = normalize_dataframe_types(student_df)
        
        return student_df
            
    except Exception as e:
        st.error(f"读取Excel文件时出错: {str(e)}")
        return None

def main():
    # 初始化session state（必须在Streamlit上下文中执行）
    init_session_state()
    
    # 使用自定义CSS美化界面
    st.markdown("""
    <style>
    /* 标题样式 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* 卡片样式 */
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin: 1.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 按钮样式 - 统一美观的样式 */
    .stButton > button {
        border-radius: 6px;
        padding: 0.5rem 1.2rem !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease;
        margin: 0.3rem 0 !important;
        white-space: nowrap;
        width: 100% !important;
        min-height: 2.5rem !important;
        height: 2.5rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.3rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* 主要按钮样式 - 使用Streamlit的data-testid属性 */
    .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
    }
    
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #5568d3 0%, #653a91 100%) !important;
    }
    
    /* 下载按钮样式 - 与普通按钮完全统一 */
    .stDownloadButton > button {
        border-radius: 6px;
        padding: 0.5rem 1.2rem !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease;
        white-space: nowrap;
        width: 100% !important;
        min-height: 2.5rem !important;
        height: 2.5rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.3rem;
        margin: 0.3rem 0 !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }
    
    /* 确保按钮容器对齐 */
    .stButton,
    .stDownloadButton {
        display: flex;
        align-items: stretch;
    }
    
    /* 确保列中的按钮容器对齐 */
    [data-testid="column"] .stButton,
    [data-testid="column"] .stDownloadButton {
        display: flex;
        align-items: stretch;
        height: 100%;
    }
    
    /* 指标卡片样式 */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    
    /* 输入框样式 */
    .stNumberInput, .stSelectbox, .stTextInput, .stMultiselect {
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    /* 确保数字输入框显示 +/- 按钮（让浏览器使用默认样式，不覆盖） */
    /* 只在必要时确保按钮可见，不强制改变样式 */
    .stNumberInput input[type='number'] {
        /* 不设置 -webkit-appearance: none，保持默认行为 */
    }
    
    /* 确保 spin 按钮始终可见（不隐藏） */
    .stNumberInput input[type='number']::-webkit-inner-spin-button,
    .stNumberInput input[type='number']::-webkit-outer-spin-button {
        opacity: 1 !important;
        display: block !important;
    }
    
    /* 悬停和聚焦时也保持可见 */
    .stNumberInput input[type='number']:hover::-webkit-inner-spin-button,
    .stNumberInput input[type='number']:hover::-webkit-outer-spin-button,
    .stNumberInput input[type='number']:focus::-webkit-inner-spin-button,
    .stNumberInput input[type='number']:focus::-webkit-outer-spin-button {
        opacity: 1 !important;
        display: block !important;
    }
    
    /* 表格样式 */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    /* 信息框样式 */
    .stInfo, .stSuccess, .stWarning, .stError {
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stInfo {
        border-left: 4px solid #667eea;
    }
    
    /* 子标题间距 */
    h3 {
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h4 {
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    
    /* 段落间距 */
    .element-container {
        margin-bottom: 1.5rem;
    }
    
    /* 文件上传器样式 */
    .stFileUploader {
        margin: 1rem 0;
    }
    
    /* Selectbox和Multiselect间距 */
    [data-baseweb="select"] {
        margin-bottom: 1.5rem;
    }
    
    /* 分隔线 */
    hr {
        margin: 2.5rem 0;
        border: none;
        border-top: 2px solid #e0e0e0;
    }
    
    /* 侧边栏间距 */
    .sidebar .element-container {
        margin-bottom: 1.5rem;
    }
    
    /* 表格容器间距 */
    [data-testid="stDataFrameContainer"] {
        margin: 1.5rem 0;
    }
    
    /* 确保列容器使用flex布局，使同一行的列高度一致 */
    .row-widget.stHorizontal {
        display: flex !important;
        align-items: stretch !important;
    }
    
    /* 确保列中的卡片高度一致 */
    [data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: stretch !important;
    }
    
    [data-testid="column"] > div {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 !important;
        min-height: 100% !important;
    }
    
    /* 确保卡片容器高度一致 */
    [data-testid="column"] .element-container {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 !important;
        min-height: 100% !important;
    }
    
    /* 确保markdown卡片高度一致并填充容器 */
    [data-testid="column"] [data-testid="stMarkdownContainer"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 !important;
        min-height: 100% !important;
    }
    
    [data-testid="column"] [data-testid="stMarkdownContainer"] > div {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 !important;
        min-height: 100% !important;
    }
    
    /* 确保markdown卡片内的div也使用flex填充 */
    [data-testid="column"] [data-testid="stMarkdownContainer"] > div > div {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 !important;
        min-height: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 标题区域 - 只在没有加载学生名单时显示（起始页面）
    if st.session_state.students_df is None:
        col_title1, col_title2, col_title3 = st.columns([1, 3, 1])
        with col_title2:
            st.markdown('<h1 class="main-title">📚 CMIS数据合并工具</h1>', unsafe_allow_html=True)
            st.markdown('<p style="text-align: center; color: #666; margin-bottom: 2rem;">快速、便捷地将两个Excel文件中顺序不同的数据合并起来，根据姓名或学号自动匹配，即使顺序不同也能正确合并。<br>开源地址：<a href="https://github.com/vanstoneniming/cmis_app.git" target="_blank" style="color: #667eea; text-decoration: none;">https://github.com/vanstoneniming/cmis_app.git</a></p>', unsafe_allow_html=True)
        
        st.markdown("---")
    
    # 侧边栏 - 文件上传
    with st.sidebar:
        st.markdown("### 📁 导入学生名单")
        st.markdown("---")
        uploaded_file = st.file_uploader(
            "上传Excel学生名单",
            type=['xlsx', 'xls'],
            help="支持.xlsx和.xls格式，文件应包含姓名列（学号和班级列可选）"
        )
        
        if uploaded_file is not None:
            # 预览文件列
            try:
                # 获取所有工作表名称
                try:
                    if uploaded_file.name.endswith('.xlsx'):
                        uploaded_file.seek(0)
                        try:
                            excel_file = pd.ExcelFile(uploaded_file, engine='openpyxl')
                            sheet_names = excel_file.sheet_names
                        except:
                            uploaded_file.seek(0)
                            excel_file = pd.ExcelFile(uploaded_file)
                            sheet_names = excel_file.sheet_names
                    elif uploaded_file.name.endswith('.xls'):
                        uploaded_file.seek(0)
                        excel_file = pd.ExcelFile(uploaded_file, engine='xlrd')
                        sheet_names = excel_file.sheet_names
                    else:
                        sheet_names = []
                    
                    # 工作表选择
                    if len(sheet_names) > 1:
                        st.subheader("📑 工作表选择")
                        sheet_option = st.radio(
                            "选择导入方式",
                            ["导入所有工作表（每个工作表一个班级）", "选择特定工作表"],
                            key="sheet_selection"
                        )
                        
                        if sheet_option == "导入所有工作表（每个工作表一个班级）":
                            selected_sheet = None  # None表示读取所有
                            st.info(f"💡 将读取所有 {len(sheet_names)} 个工作表：{', '.join(str(s) for s in sheet_names)}")
                        else:
                            selected_sheet = st.selectbox(
                                "选择要导入的工作表",
                                options=sheet_names,
                                key="selected_sheet"
                            )
                    else:
                        selected_sheet = sheet_names[0] if sheet_names else None
                        st.info(f"📑 检测到1个工作表：{selected_sheet}")
                except Exception as e:
                    st.warning(f"无法读取工作表信息: {str(e)}，将使用默认工作表")
                    selected_sheet = None
                    sheet_names = []
                
                # 跳过行数设置（先设置，用于预览）
                col_skip1, col_skip2 = st.columns(2)
                with col_skip1:
                    skiprows = st.number_input(
                        "跳过前N行（顶部无用行）",
                        min_value=0,
                        max_value=20,
                        value=0,
                        step=1,
                        help="跳过文件顶部的无用行（如标题、说明等）",
                        key="student_import_skiprows"
                    )
                with col_skip2:
                    skipfooter = st.number_input(
                        "跳过尾部N行（底部无用行）",
                        min_value=0,
                        max_value=50,
                        value=0,
                        step=1,
                        help="跳过文件尾部的无用行（如汇总、统计等）",
                        key="student_import_skipfooter"
                    )
                
                # 读取预览数据（考虑跳过行数、尾部行数和工作表）
                # 确保skiprows和skipfooter是整数类型
                skiprows = int(skiprows) if skiprows else 0
                skipfooter = int(skipfooter) if skipfooter else 0
                
                read_opts = {}
                if skiprows > 0:
                    read_opts['skiprows'] = int(skiprows)  # 确保是整数类型
                    read_opts['header'] = None
                # 预览时也考虑跳过尾部行（用于显示准确的数据）
                if skipfooter > 0:
                    read_opts['skipfooter'] = int(skipfooter)  # 确保是整数类型
                
                # 再次确保 read_opts 中所有数值都是整数类型（双重保险）
                if 'skiprows' in read_opts:
                    read_opts['skiprows'] = int(read_opts['skiprows'])
                if 'skipfooter' in read_opts:
                    read_opts['skipfooter'] = int(read_opts['skipfooter'])
                
                # 选择用于预览的工作表
                preview_sheet = selected_sheet if selected_sheet else (sheet_names[0] if sheet_names else None)
                
                if uploaded_file.name.endswith('.xlsx'):
                    uploaded_file.seek(0)
                    try:
                        # 注意：nrows和skipfooter可能冲突，所以先读取更多行，再处理skipfooter
                        if 'skipfooter' in read_opts and 'nrows' in read_opts:
                            # 先读取更多行，然后手动处理
                            skipfooter_val = int(read_opts.pop('skipfooter', 0))
                            nrows_val = int(read_opts.pop('nrows', 15))
                            # 确保 read_opts 中所有参数都是正确的类型
                            safe_opts = {}
                            if 'skiprows' in read_opts:
                                safe_opts['skiprows'] = int(read_opts['skiprows'])
                            if 'header' in read_opts:
                                safe_opts['header'] = read_opts['header']
                            temp_df = pd.read_excel(uploaded_file, sheet_name=preview_sheet, engine='openpyxl', **safe_opts)
                            # 删除尾部行
                            if skipfooter_val > 0 and len(temp_df) > skipfooter_val:
                                temp_df = temp_df.iloc[:-skipfooter_val].reset_index(drop=True)
                            # 取前nrows行
                            preview_df = temp_df.head(nrows_val)
                        else:
                            # 确保 read_opts 中所有参数都是正确的类型
                            safe_opts = {}
                            if 'skiprows' in read_opts:
                                safe_opts['skiprows'] = int(read_opts['skiprows'])
                            if 'header' in read_opts:
                                safe_opts['header'] = read_opts['header']
                            preview_df = pd.read_excel(uploaded_file, sheet_name=preview_sheet, engine='openpyxl', nrows=15, **safe_opts)
                    except Exception as e:
                        uploaded_file.seek(0)
                        # 如果失败，手动处理skipfooter
                        if 'skipfooter' in read_opts:
                            skipfooter_val = int(read_opts.pop('skipfooter', 0))
                            # 确保 read_opts 中所有参数都是正确的类型
                            safe_opts = {}
                            if 'skiprows' in read_opts:
                                safe_opts['skiprows'] = int(read_opts['skiprows'])
                            if 'header' in read_opts:
                                safe_opts['header'] = read_opts['header']
                            preview_df = pd.read_excel(uploaded_file, sheet_name=preview_sheet, engine='openpyxl', nrows=20, **safe_opts)
                            if skipfooter_val > 0 and len(preview_df) > skipfooter_val:
                                preview_df = preview_df.iloc[:-skipfooter_val].head(15).reset_index(drop=True)
                        else:
                            # 确保 read_opts 中所有参数都是正确的类型
                            safe_opts = {}
                            if 'skiprows' in read_opts:
                                safe_opts['skiprows'] = int(read_opts['skiprows'])
                            if 'header' in read_opts:
                                safe_opts['header'] = read_opts['header']
                            preview_df = pd.read_excel(uploaded_file, sheet_name=preview_sheet, engine='openpyxl', nrows=15, **safe_opts)
                elif uploaded_file.name.endswith('.xls'):
                    uploaded_file.seek(0)
                    # xlrd不支持skipfooter，需要手动处理
                    if 'skipfooter' in read_opts:
                        skipfooter_val = int(read_opts.pop('skipfooter', 0))
                        # 确保 read_opts 中所有参数都是正确的类型
                        safe_opts = {}
                        if 'skiprows' in read_opts:
                            safe_opts['skiprows'] = int(read_opts['skiprows'])
                        if 'header' in read_opts:
                            safe_opts['header'] = read_opts['header']
                        # 先读取更多行，然后删除尾部行
                        preview_df = pd.read_excel(uploaded_file, sheet_name=preview_sheet, engine='xlrd', nrows=20, **safe_opts)
                        if skipfooter_val > 0 and len(preview_df) > skipfooter_val:
                            preview_df = preview_df.iloc[:-skipfooter_val].head(15).reset_index(drop=True)
                        else:
                            preview_df = preview_df.head(15)
                    else:
                        # 确保 read_opts 中所有参数都是正确的类型
                        safe_opts = {}
                        if 'skiprows' in read_opts:
                            safe_opts['skiprows'] = int(read_opts['skiprows'])
                        if 'header' in read_opts:
                            safe_opts['header'] = read_opts['header']
                        preview_df = pd.read_excel(uploaded_file, sheet_name=preview_sheet, engine='xlrd', nrows=15, **safe_opts)
                else:
                    preview_df = None
                
                if preview_df is not None:
                    # 如果跳过了行，处理列名
                    if skiprows > 0 and len(preview_df) > 0:
                        first_row = preview_df.iloc[0].astype(str).tolist()
                        has_keywords = any(
                            any(keyword in str(cell).lower() for keyword in ['姓名', '名字', 'name', '学号', 'id', '编号'])
                            for cell in first_row
                        )
                        if has_keywords:
                            # 清理NaN值，替换为默认列名
                            new_columns = []
                            for i, val in enumerate(preview_df.iloc[0]):
                                val_str = str(val).strip()
                                if pd.isna(val) or val_str == '' or val_str.lower() in ['nan', 'none', 'nat']:
                                    new_columns.append(f"列{i+1}")
                                else:
                                    new_columns.append(val_str)
                            preview_df.columns = new_columns
                            preview_df = preview_df[1:].reset_index(drop=True)
                        else:
                            preview_df.columns = [f"列{i+1}" for i in range(len(preview_df.columns))]
                    
                    # 规范化数据类型，避免pyarrow错误
                    preview_df = normalize_dataframe_types(preview_df)
                    
                    st.markdown("---")
                    st.markdown("#### 📋 文件预览（前10行）")
                    st.dataframe(preview_df, width='stretch')
                    st.caption("💡 如果顶部有无用的行（如标题、说明等），请在上方设置跳过行数")
                    
                    st.markdown("")  # 增加间距
                    st.markdown("#### ⚙️ 列映射设置")
                    
                    # 对预览数据进行列识别（包括拆分"姓名 (学号)"格式）
                    auto_id, auto_name, auto_class, preview_df = identify_columns(preview_df)
                    columns = preview_df.columns.tolist()
                    
                    col_name = st.selectbox(
                        "姓名列 *",
                        options=columns,
                        index=columns.index(auto_name) if auto_name and auto_name in columns else 0,
                        help="必须选择姓名列。如果文件中有'姓名 (学号)'格式的列，系统会自动拆分",
                        label_visibility="visible"
                    )
                    
                    col_id = st.selectbox(
                        "学号列（可选）",
                        options=["自动识别"] + columns,
                        index=0 if not auto_id or auto_id not in columns else columns.index(auto_id) + 1,
                        help="如果没有学号列，系统将自动生成唯一标识符",
                        label_visibility="visible"
                    )
                    
                    col_class = st.selectbox(
                        "班级列（可选）",
                        options=["自动识别"] + columns,
                        index=0 if not auto_class or auto_class not in columns else columns.index(auto_class) + 1,
                        help="如果有班级列，将显示在列表中",
                        label_visibility="visible"
                    )
                    
                    id_col = None if col_id == "自动识别" else col_id
                    name_col = col_name
                    class_col = None if col_class == "自动识别" else col_class
                    
                    st.markdown("")
                    if st.button("✅ 加载学生名单", type="primary", use_container_width=True):
                            pass
                            # 重置文件指针
                            uploaded_file.seek(0)
                            df = load_student_list(uploaded_file, id_col, name_col, class_col, skiprows=skiprows, skipfooter=skipfooter, sheet_name=selected_sheet)
                            if df is not None:
                                st.session_state.students_df = df
                                st.session_state.grades_df = df.copy()
                                
                                # 统计加载的信息
                                loaded_info = [f"✅ 成功加载 {len(df)} 名学生！"]
                                
                                # 统计班级
                                if '班级' in df.columns and df['班级'].notna().any():
                                    class_count = df[df['班级'] != '']['班级'].nunique()
                                    loaded_info.append(f"📚 {class_count} 个班级")
                                
                                # 统计加载的列数
                                total_cols = len(df.columns)
                                loaded_info.append(f"📋 {total_cols} 列数据")
                                
                                # 将加载消息保存到session_state，以便在rerun后显示
                                st.session_state.load_success_message = " | ".join(loaded_info)
                                st.session_state.load_info_message = "💡 已加载基准文件，可以在主界面中上传第二个Excel文件进行合并"
                                
                                save_data()  # 自动保存
                                st.rerun()
            except Exception as e:
                st.error(f"预览文件时出错: {str(e)}")
        
        st.markdown("---")
        st.header("💾 数据管理")
        
        if st.session_state.grades_df is not None:
            # 显示保存状态
            if st.session_state.get('last_saved_time'):
                try:
                    saved_time = datetime.fromisoformat(st.session_state.get('last_saved_time', ''))
                    time_str = saved_time.strftime("%m-%d %H:%M")
                    st.caption(f"📂 最后保存: {time_str}")
                except:
                    pass
            
            # 清除数据按钮
            st.markdown("---")
            if st.button("🗑️ 清除所有数据", use_container_width=True, help="清除数据和本地文件"):
                if DATA_FILE.exists():
                    os.remove(DATA_FILE)
                st.session_state.students_df = None
                st.session_state.grades_df = None
                st.session_state.data_loaded = False
                st.success("✅ 数据已清除")
                st.rerun()
            
    
    # 主内容区域
    if st.session_state.students_df is None:
        # 如果有加载成功的消息，先显示它
        if st.session_state.get('load_success_message'):
            st.success(st.session_state.load_success_message)
            # 显示一次后清除，避免每次都显示
            del st.session_state.load_success_message
        if st.session_state.get('load_info_message'):
            st.info(st.session_state.load_info_message)
            # 显示一次后清除
            del st.session_state.load_info_message
        
        st.info("👈 请在左侧上传Excel学生名单文件开始使用")
        # 使用更美观的说明卡片
        st.markdown("""
        <div style="margin-bottom: 2rem;">
            <h3 style="color: #2c3e50; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.5em;">📖</span> 使用指南
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 快速开始 - 浅蓝色背景，火箭图标
        st.markdown("""
        <div style="background: #f8f9fa; 
                    padding: 1.8rem; 
                    border-radius: 15px; 
                    border-left: 4px solid #667eea;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    margin-bottom: 1.5rem;
                    transition: transform 0.2s ease;">
            <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem;">
                <span style="font-size: 2.2em;">🚀</span>
                <h4 style="color: #667eea; margin: 0; font-size: 1.3em; font-weight: 600;">快速开始</h4>
            </div>
            <ul style="line-height: 2.2; color: #495057; margin: 0; padding-left: 1.5rem; font-size: 0.95em; list-style: none;">
                <li style="margin-bottom: 0.8rem;">📤 <strong>上传基准文件</strong>：在左侧上传第一个Excel文件（作为基准顺序）</li>
                <li style="margin-bottom: 0.8rem;">⚙️ <strong>列映射设置</strong>：系统会自动识别列，也可以手动选择</li>
                <li style="margin-bottom: 0.8rem;">📥 <strong>导入并合并</strong>：上传第二个Excel文件，选择匹配列和要合并的列</li>
                <li>✏️ <strong>编辑数据</strong>：在表格中直接编辑数据</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 智能识别功能 - 浅蓝绿色背景，闪烁星星图标
        st.markdown("""
        <div style="background: #d1ecf1; 
                    padding: 1.8rem; 
                    border-radius: 15px; 
                    border-left: 4px solid #0c5460;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem;">
                <span style="font-size: 2.2em;">✨</span>
                <h4 style="color: #0c5460; margin: 0; font-size: 1.3em; font-weight: 600;">智能识别功能</h4>
            </div>
            <ul style="line-height: 2.2; color: #0c5460; margin: 0; padding-left: 1.5rem; font-size: 0.95em; list-style: none;">
                <li style="margin-bottom: 0.8rem;">🔍 <strong>自动识别</strong>姓名列、学号列、班级列</li>
                <li style="margin-bottom: 0.8rem;">🆔 <strong>自动生成</strong>学号（格式：班级_序号 或 STU_序号）</li>
                <li style="margin-bottom: 0.8rem;">📊 <strong>班级统计</strong>支持按班级进行筛选和统计</li>
                <li>🎯 <strong>姓名匹配</strong>支持"姓名 (学号)"格式自动拆分</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 文件格式要求 - 浅黄/橙色背景，文档图标
        st.markdown("""
        <div style="background: #fff3cd; 
                    padding: 1.8rem; 
                    border-radius: 15px; 
                    border-left: 4px solid #ffc107;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem;">
                <span style="font-size: 2.2em;">📋</span>
                <h4 style="color: #856404; margin: 0; font-size: 1.3em; font-weight: 600;">文件格式要求</h4>
            </div>
            <ul style="line-height: 2.2; color: #856404; margin: 0; padding-left: 1.5rem; font-size: 0.95em; list-style: none;">
                <li style="margin-bottom: 0.8rem;">✅ <strong>必须包含</strong>："姓名"列（或"Name"、"名字"）</li>
                <li style="margin-bottom: 0.8rem;">📝 <strong>可选包含</strong>："学号"列（自动生成唯一标识符）</li>
                <li style="margin-bottom: 0.8rem;">📚 <strong>可选包含</strong>："班级"列（支持按班级统计）</li>
                <li>💾 支持 <code style="background: rgba(255,255,255,0.8); padding: 2px 6px; border-radius: 4px;">.xlsx</code> 和 <code style="background: rgba(255,255,255,0.8); padding: 2px 6px; border-radius: 4px;">.xls</code> 格式</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 使用技巧 - 浅绿色背景，灯泡图标
        st.markdown("""
        <div style="background: #d4edda; 
                    padding: 1.8rem; 
                    border-radius: 15px; 
                    border-left: 4px solid #28a745;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem;">
                <span style="font-size: 2.2em;">💡</span>
                <h4 style="color: #155724; margin: 0; font-size: 1.3em; font-weight: 600;">使用技巧</h4>
            </div>
            <ul style="line-height: 2.2; color: #155724; margin: 0; padding-left: 1.5rem; font-size: 0.95em; list-style: none;">
                <li style="margin-bottom: 0.8rem;">⌨️ 使用 <kbd style="background: rgba(255,255,255,0.8); padding: 3px 8px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">Tab</kbd> 键快速切换单元格</li>
                <li style="margin-bottom: 0.8rem;">📊 批量导入时支持选择多个数据列</li>
                <li style="margin-bottom: 0.8rem;">💾 数据会自动保存，无需担心丢失</li>
                <li>⏭️ 支持跳过文件头部和尾部的无用行</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 有数据时，不再显示标题和描述
        # 如果有加载成功的消息，先显示它
        if st.session_state.get('load_success_message'):
            st.success(st.session_state.load_success_message)
            # 显示一次后清除，避免每次都显示
            del st.session_state.load_success_message
        if st.session_state.get('load_info_message'):
            st.info(st.session_state.load_info_message)
            # 显示一次后清除
            del st.session_state.load_info_message
        
        # 批量导入数据列（直接展开，不使用折叠面板）
        st.markdown("**📥 从Excel导入数据列**")
        st.info("💡 上传第二个Excel文件，系统会根据匹配列自动匹配并导入数据列")
        
        score_file = st.file_uploader(
            "上传Excel文件",
            type=['xlsx', 'xls'],
            help="Excel至少应包含姓名或学号列（用于匹配），以及至少一个要合并的数据列",
            key="score_upload"
        )
        
        if score_file is not None:
            try:
                # 跳过行数设置
                col_skip1, col_skip2 = st.columns(2)
                with col_skip1:
                    score_skiprows = st.number_input(
                        "跳过前N行（顶部无用行）",
                        min_value=0,
                        max_value=20,
                        value=0,
                        step=1,
                        key="score_import_skiprows",
                        help="跳过文件顶部的无用行（如标题、说明等）"
                    )
                with col_skip2:
                    score_skipfooter = st.number_input(
                        "跳过尾部N行（底部无用行）",
                        min_value=0,
                        max_value=50,
                        value=0,
                        step=1,
                        key="score_import_skipfooter",
                        help="跳过文件尾部的无用行（如汇总、统计等）"
                    )
                
                # 确保skiprows和skipfooter是整数类型
                score_skiprows = int(score_skiprows) if score_skiprows else 0
                score_skipfooter = int(score_skipfooter) if score_skipfooter else 0
                
                read_score_opts = {}
                if score_skiprows > 0:
                    read_score_opts['skiprows'] = int(score_skiprows)  # 确保是整数类型
                    read_score_opts['header'] = None
                if score_skipfooter > 0:
                    read_score_opts['skipfooter'] = int(score_skipfooter)  # 确保是整数类型
                
                if score_file.name.endswith('.xlsx'):
                    score_file.seek(0)
                    try:
                        # 确保所有参数都是正确的类型
                        safe_score_opts = {}
                        if 'skiprows' in read_score_opts:
                            safe_score_opts['skiprows'] = int(read_score_opts['skiprows'])
                        if 'skipfooter' in read_score_opts:
                            safe_score_opts['skipfooter'] = int(read_score_opts['skipfooter'])
                        if 'header' in read_score_opts:
                            safe_score_opts['header'] = read_score_opts['header']
                        # openpyxl支持skipfooter参数
                        score_df = pd.read_excel(score_file, engine='openpyxl', **safe_score_opts)
                    except Exception as e:
                        score_file.seek(0)
                        # 如果失败，尝试手动处理skipfooter
                        if 'skipfooter' in read_score_opts:
                            skipfooter_val = int(read_score_opts.pop('skipfooter', 0))
                            safe_score_opts = {}
                            if 'skiprows' in read_score_opts:
                                safe_score_opts['skiprows'] = int(read_score_opts['skiprows'])
                            if 'header' in read_score_opts:
                                safe_score_opts['header'] = read_score_opts['header']
                            score_df = pd.read_excel(score_file, engine='openpyxl', **safe_score_opts)
                            # 手动删除尾部行
                            if skipfooter_val > 0 and len(score_df) > skipfooter_val:
                                score_df = score_df.iloc[:-skipfooter_val].reset_index(drop=True)
                        else:
                            safe_score_opts = {}
                            if 'skiprows' in read_score_opts:
                                safe_score_opts['skiprows'] = int(read_score_opts['skiprows'])
                            if 'header' in read_score_opts:
                                safe_score_opts['header'] = read_score_opts['header']
                            score_df = pd.read_excel(score_file, **safe_score_opts)
                else:
                    score_file.seek(0)
                    # xlrd引擎不支持skipfooter，需要手动处理
                    if 'skipfooter' in read_score_opts:
                        skipfooter_val = int(read_score_opts.pop('skipfooter', 0))
                        safe_score_opts = {}
                        if 'skiprows' in read_score_opts:
                            safe_score_opts['skiprows'] = int(read_score_opts['skiprows'])
                        if 'header' in read_score_opts:
                            safe_score_opts['header'] = read_score_opts['header']
                        score_df = pd.read_excel(score_file, engine='xlrd', **safe_score_opts)
                        # 手动删除尾部行
                        if skipfooter_val > 0 and len(score_df) > skipfooter_val:
                            score_df = score_df.iloc[:-skipfooter_val].reset_index(drop=True)
                    else:
                        safe_score_opts = {}
                        if 'skiprows' in read_score_opts:
                            safe_score_opts['skiprows'] = int(read_score_opts['skiprows'])
                        if 'header' in read_score_opts:
                            safe_score_opts['header'] = read_score_opts['header']
                        score_df = pd.read_excel(score_file, engine='xlrd', **safe_score_opts)
                
                # 如果跳过了行，处理列名
                if score_skiprows > 0 and len(score_df) > 0:
                    first_row = score_df.iloc[0].astype(str).tolist()
                    has_keywords = any(
                        any(keyword in str(cell).lower() for keyword in ['姓名', '名字', 'name', '成绩', '分数', 'score'])
                        for cell in first_row
                    )
                    if has_keywords:
                        # 清理NaN值，替换为默认列名，并处理重复列名
                        new_columns = []
                        column_counts = {}  # 用于跟踪每个列名出现的次数
                        
                        for i, val in enumerate(score_df.iloc[0]):
                            val_str = str(val).strip()
                            if pd.isna(val) or val_str == '' or val_str.lower() in ['nan', 'none', 'nat']:
                                base_col_name = f"列{i+1}"
                            else:
                                base_col_name = val_str
                            
                            # 处理重复列名：如果列名已存在，添加后缀
                            if base_col_name in new_columns:
                                # 计算已使用的次数
                                count = column_counts.get(base_col_name, 0) + 1
                                column_counts[base_col_name] = count
                                new_col_name = f"{base_col_name}_{count}"
                                # 确保新名称也不重复
                                while new_col_name in new_columns:
                                    count += 1
                                    new_col_name = f"{base_col_name}_{count}"
                                new_columns.append(new_col_name)
                            else:
                                new_columns.append(base_col_name)
                                column_counts[base_col_name] = 0
                        
                        score_df.columns = new_columns
                        score_df = score_df[1:].reset_index(drop=True)
                    else:
                        score_df.columns = [f"列{i+1}" for i in range(len(score_df.columns))]
                
                # 无论是否跳行，都统一将所有列名转换为字符串类型
                # 这样可以避免数字列名（如 56）与字符串列名（如 "56"）不匹配的问题
                score_df.columns = [str(col) for col in score_df.columns]
                
                # 处理重复列名（这会将所有列名统一为字符串）
                score_df = handle_duplicate_columns(score_df)
                
                # 规范化数据类型，避免pyarrow错误
                score_df = normalize_dataframe_types(score_df)
                
                st.dataframe(score_df.head(15), width='stretch')
                st.caption(f"显示前15行数据，共 {len(score_df)} 行")
                
                # 识别匹配列（姓名或学号）
                # 自动识别学号列（优先推荐）
                id_cols = [col for col in score_df.columns if any(keyword in str(col).lower() for keyword in ['学号', 'id', '编号', 'student_id', '考号'])]
                default_index = 0
                if id_cols:
                    # 如果有学号列，默认选择第一个学号列
                    default_index = score_df.columns.tolist().index(id_cols[0])
                
                match_col = st.selectbox(
                    "选择匹配列（用于匹配学生）*", 
                    score_df.columns.tolist(),
                    index=default_index,
                    key="match_col_select",
                    help="💡 建议选择学号列进行匹配，可避免重名问题。如果选择姓名列且存在重名，系统会使用第一个匹配的学生并给出警告。"
                )
                
                # 多选数据列
                st.markdown("#### 选择数据列（可多选）")
                st.caption("💡 每个数据列将作为独立列添加到基准文件中")
                
                # 自动识别可能的成绩列（排除匹配列）
                # 先获取已经是数字类型的列
                numeric_cols = score_df.select_dtypes(include=['number']).columns.tolist()
                
                # 检测文本列中哪些可能是数字文本（成绩列）
                text_cols = score_df.select_dtypes(include=['object']).columns.tolist()
                numeric_text_cols = []
                
                for col in text_cols:
                    if col == match_col:
                        continue
                    is_numeric_text, ratio = detect_numeric_text_column(score_df, col)
                    if is_numeric_text:
                        numeric_text_cols.append(col)
                
                # 合并所有可能的成绩列（数字类型 + 数字文本类型）
                all_numeric_cols = list(set(numeric_cols + numeric_text_cols))
                other_cols = [col for col in score_df.columns if col != match_col and col not in all_numeric_cols]
                score_candidates = [col for col in all_numeric_cols if col != match_col]
                
                # 显示所有可选的列（数值列优先）
                score_options = score_candidates + [col for col in other_cols if col != match_col]
                
                selected_score_cols = st.multiselect(
                    "选择数据列（可多选，每个列将作为独立列添加）*",
                    options=score_options,
                    default=score_candidates if score_candidates else None,
                    help="可以选择多个数据列，每个列都会作为独立的列添加到基准文件中",
                    label_visibility="visible"
                )
                
                # 在导入前，只保留匹配列和选择的成绩列
                # 先保存完整的score_df用于重名检查时的显示
                score_df_full_for_dup = score_df.copy()
                
                if selected_score_cols and match_col:
                    # 只保留匹配列和选择的成绩列，删除其他列
                    keep_cols = [match_col] + selected_score_cols
                    score_df = score_df[keep_cols].copy()
                
                if selected_score_cols:
                    st.markdown("")  # 增加间距
                    # 显示预览
                    st.markdown("#### 📋 导入预览")
                    preview_info = []
                    for score_col in selected_score_cols:
                        non_null_count = score_df[score_col].notna().sum()
                        preview_info.append(f"- **{str(score_col)}**: {non_null_count} 个有效成绩")
                    st.info("\n".join(preview_info))
                    st.info(f"💡 已过滤数据：仅保留匹配列 '{match_col}' 和 {len(selected_score_cols)} 个数据列")
                    
                    st.markdown("")  # 按钮前增加间距
                
                # 在导入前，检查是否有重名情况
                if selected_score_cols and match_col:
                    # 检查匹配列中是否有重复值（可能的重名情况）
                    match_col_lower = str(match_col).lower()
                    is_name_col = any(keyword in match_col_lower for keyword in ['姓名', 'name', '名字'])
                    
                    if is_name_col and 'grades_df' in st.session_state and st.session_state.grades_df is not None:
                        # 收集所有重名情况（包括成绩文件中的重复和名单中的重复）
                        duplicate_cases = {}  # {name: [{'row_idx': idx, 'score_row': row, 'matched_students': df}]}
                        
                        # 使用完整的score_df来获取所有列的信息（score_df_full_for_dup在过滤前已保存）
                        for idx, row in score_df_full_for_dup.iterrows():
                            match_value = str(row[match_col]).strip()
                            if pd.isna(match_value) or match_value == '':
                                continue
                            
                            if '姓名' in st.session_state.grades_df.columns:
                                name_matches = st.session_state.grades_df['姓名'].astype(str).str.strip() == match_value
                                match_count = name_matches.sum()
                                if match_count > 1:
                                    # 发现重名
                                    if match_value not in duplicate_cases:
                                        duplicate_cases[match_value] = []
                                    
                                    matched_students = st.session_state.grades_df[name_matches].copy()
                                    duplicate_cases[match_value].append({
                                        'row_idx': idx,
                                        'score_row': row.to_dict(),  # 转换为字典以便访问
                                        'matched_students': matched_students
                                    })
                        
                        # 如果有重名，统一显示并处理
                        if duplicate_cases:
                            st.warning(f"⚠️ 发现 {len(duplicate_cases)} 个重名情况，共 {sum(len(cases) for cases in duplicate_cases.values())} 行需要手动选择对应的学生")
                            # 存储重名映射到session state
                            if 'duplicate_mappings' not in st.session_state:
                                st.session_state.duplicate_mappings = {}
                            
                            # 按姓名分组显示所有重名情况
                            for name, cases in duplicate_cases.items():
                                st.markdown(f"### 📋 姓名：{name} （{len(cases)} 行）")
                                
                                # 显示成绩文件中的相关信息
                                for case_idx, case in enumerate(cases):
                                    row_idx = case['row_idx']
                                    score_row = case['score_row']
                                    matched_students = case['matched_students']
                                    
                                    st.markdown(f"**成绩文件第 {row_idx+1} 行数据：**")
                                    
                                    # 显示成绩文件该行的详细信息（使用表格形式，更清晰）
                                    # 从保存的完整score_df获取该行的完整数据（score_df_full_for_dup包含所有列）
                                    if row_idx < len(score_df_full_for_dup):
                                        original_row = score_df_full_for_dup.iloc[row_idx]
                                        
                                        # 构建显示用的DataFrame（显示该行的所有列，完整数据）
                                        score_display_data = {}
                                        for col in score_df_full_for_dup.columns:
                                            val = original_row[col]
                                            if pd.notna(val):
                                                # 保留原始格式，如果是数字且是整数，不显示.0
                                                if isinstance(val, (int, float)):
                                                    # 如果是整数（float但值是整数），显示为整数
                                                    if isinstance(val, float) and val.is_integer():
                                                        score_display_data[col] = int(val)
                                                    else:
                                                        score_display_data[col] = val
                                                else:
                                                    val_str = str(val).strip()
                                                    if val_str != '' and val_str.lower() not in ['nan', 'none', 'nat']:
                                                        score_display_data[col] = val_str
                                            else:
                                                # 即使为空也显示，用空字符串表示
                                                score_display_data[col] = ''
                                        
                                        if score_display_data:
                                            # 使用表格显示完整的一行数据（所有列）
                                            score_display_df = pd.DataFrame([score_display_data])
                                            st.dataframe(score_display_df, width='stretch', hide_index=True)
                                        else:
                                            st.caption("💡 该行没有数据")
                                    else:
                                        st.caption("⚠️ 无法获取该行数据")
                                    
                                    # 显示匹配到的学生列表（详细信息）
                                    st.markdown("**学生名单中匹配到的学生：**")
                                    
                                    # 构建学生选择选项，显示详细信息
                                    display_options = []
                                    for student_idx in matched_students.index:
                                        student = matched_students.loc[student_idx]
                                        student_id = student.get('学号', 'N/A')
                                        class_name = student.get('班级', 'N/A')
                                        
                                        # 格式化学号：如果是数字且是整数，不显示.0
                                        if isinstance(student_id, (int, float)):
                                            if isinstance(student_id, float) and student_id.is_integer():
                                                student_id = int(student_id)
                                            student_id_str = str(student_id)
                                        else:
                                            student_id_str = str(student_id)
                                        
                                        # 收集学生的其他信息
                                        student_info_parts = [f"学号：{student_id_str}"]
                                        if pd.notna(class_name) and str(class_name) != '':
                                            student_info_parts.append(f"班级：{class_name}")
                                        
                                        # 添加学生的其他列信息（如果有）
                                        for col in matched_students.columns:
                                            if col not in ['学号', '姓名', '班级']:
                                                val = student.get(col, None)
                                                if pd.notna(val):
                                                    # 格式化值：如果是数字且是整数，不显示.0
                                                    if isinstance(val, (int, float)):
                                                        if isinstance(val, float) and val.is_integer():
                                                            val_str = str(int(val))
                                                        else:
                                                            val_str = str(val)
                                                    else:
                                                        val_str = str(val).strip()
                                                    
                                                    if val_str != '':
                                                        student_info_parts.append(f"{col}：{val_str}")
                                        
                                        option_text = " | ".join(student_info_parts)
                                        display_options.append((student_idx, option_text, student))
                                    
                                    # 使用表格显示学生信息，更清晰
                                    if len(display_options) > 0:
                                        # 构建显示用的DataFrame
                                        display_df_data = []
                                        for opt_idx, (student_idx, option_text, student) in enumerate(display_options):
                                            # 格式化学号
                                            student_id_val = student.get('学号', 'N/A')
                                            if isinstance(student_id_val, (int, float)):
                                                if isinstance(student_id_val, float) and student_id_val.is_integer():
                                                    student_id_display = int(student_id_val)
                                                else:
                                                    student_id_display = student_id_val
                                            else:
                                                student_id_display = student_id_val
                                            
                                            row_data = {
                                                '选项': opt_idx,
                                                '学号': student_id_display,
                                                '班级': student.get('班级', 'N/A') if pd.notna(student.get('班级', None)) else 'N/A'
                                            }
                                            # 添加其他列（保持原始格式）
                                            for col in matched_students.columns:
                                                if col not in ['学号', '姓名', '班级']:
                                                    val = student.get(col, None)
                                                    if pd.notna(val):
                                                        # 格式化值：如果是数字且是整数，不显示.0
                                                        if isinstance(val, (int, float)):
                                                            if isinstance(val, float) and val.is_integer():
                                                                row_data[col] = int(val)
                                                            else:
                                                                row_data[col] = val
                                                        else:
                                                            row_data[col] = val
                                                    else:
                                                        row_data[col] = 'N/A'
                                            display_df_data.append(row_data)
                                        
                                        if display_df_data:
                                            display_df = pd.DataFrame(display_df_data)
                                            st.dataframe(display_df, width='stretch', hide_index=True)
                                    
                                    # 让用户选择
                                    selected_option = st.radio(
                                        f"选择对应的学生（成绩文件第 {row_idx+1} 行）",
                                        options=[opt[0] for opt in display_options],
                                        format_func=lambda x: next(f"选项 {display_options.index([opt for opt in display_options if opt[0] == x][0])} - {opt[1]}" for opt in display_options if opt[0] == x),
                                        key=f"dup_select_{name}_{row_idx}_{case_idx}",
                                        horizontal=False
                                    )
                                    st.session_state.duplicate_mappings[f"{name}_{row_idx}"] = selected_option
                                    
                                    if case_idx < len(cases) - 1:
                                        st.markdown("---")
                                
                                st.markdown("---")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    if st.button("✅ 导入数据列", type="primary", use_container_width=True):
                        if not selected_score_cols:
                            st.error("⚠️ 请至少选择一个数据列")
                        elif not match_col:
                            st.error("⚠️ 请选择匹配列（姓名或学号列）")
                        else:
                            matched_count = 0
                            updated_count = 0
                            added_cols = []
                            unmatched_rows = []
                            
                            # 确保grades_df存在
                            if 'grades_df' not in st.session_state or st.session_state.grades_df is None:
                                st.error("请先导入学生名单")
                            else:
                                # 只保留匹配列和选择的成绩列，删除其他列
                                keep_cols = [match_col] + selected_score_cols
                                score_df_filtered = score_df[keep_cols].copy()
                                
                                # 对每个选中的成绩列进行处理
                                for score_col in selected_score_cols:
                                    col_added = False
                                    
                                    # 处理列名重复：如果列名已存在，自动重命名
                                    final_col_name = str(score_col)
                                    if final_col_name in st.session_state.grades_df.columns:
                                        # 列已存在，自动添加后缀重命名
                                        counter = 1
                                        while f"{final_col_name}_{counter}" in st.session_state.grades_df.columns:
                                            counter += 1
                                        final_col_name = f"{final_col_name}_{counter}"
                                        st.warning(f"⚠️ 列名 '{score_col}' 已存在，自动重命名为 '{final_col_name}'")
                                    
                                    # 如果列名不同，需要创建新列
                                    if final_col_name != str(score_col):
                                        # 需要重命名，先创建新列
                                        st.session_state.grades_df[final_col_name] = None
                                        col_added = True
                                        added_cols.append(final_col_name)
                                    elif final_col_name not in st.session_state.grades_df.columns:
                                        # 新建列，初始值为None
                                        st.session_state.grades_df[final_col_name] = None
                                        col_added = True
                                        added_cols.append(final_col_name)
                                    else:
                                        # 列已存在，直接更新
                                        col_added = True
                                    
                                    # 导入数据（使用过滤后的数据框，只包含匹配列和选择的成绩列）
                                    for idx, row in score_df_filtered.iterrows():
                                        match_value = str(row[match_col]).strip()
                                        if pd.isna(match_value) or match_value == '':
                                            continue
                                        
                                        # 使用原始的score_col从数据框中获取值
                                        # 确保score_col是字符串类型，因为列名已经统一转换为字符串类型
                                        score_col_str = str(score_col)
                                        try:
                                            score_value = row[score_col_str]
                                        except KeyError:
                                            # 如果字符串列名不存在，尝试使用原始列名（向后兼容）
                                            try:
                                                score_value = row[score_col]
                                            except KeyError:
                                                # 列名不存在，跳过此行
                                                unmatched_rows.append(f"第{idx+1}行：列 '{score_col}' 不存在")
                                                continue
                                        
                                        # 根据用户选择的匹配列进行精确匹配（严格按选择的列匹配，不做自动转换）
                                        match_mask = None
                                        
                                        # 判断匹配列的类型
                                        match_col_lower = str(match_col).lower()
                                        is_id_col = any(keyword in match_col_lower for keyword in ['学号', 'id', '编号', 'student_id', '考号'])
                                        is_name_col = any(keyword in match_col_lower for keyword in ['姓名', 'name', '名字'])
                                        
                                        if is_id_col:
                                            # 如果匹配列是学号类列（如"考号"），匹配学生数据中的"学号"列
                                            # 注意：考号和学号可能不一致，但这里按匹配列的值匹配学号列
                                            if '学号' in st.session_state.grades_df.columns:
                                                match_mask = st.session_state.grades_df['学号'].astype(str).str.strip() == match_value
                                                if not match_mask.any():
                                                    unmatched_rows.append(f"第{idx+1}行：未找到学号 '{match_value}' 的学生")
                                                    continue
                                        elif is_name_col:
                                            # 如果匹配列是姓名列，匹配学生数据中的"姓名"列
                                            if '姓名' in st.session_state.grades_df.columns:
                                                name_matches = st.session_state.grades_df['姓名'].astype(str).str.strip() == match_value
                                                match_count = name_matches.sum()
                                                if match_count == 1:
                                                    # 只有一个匹配，使用它
                                                    match_mask = name_matches
                                                elif match_count > 1:
                                                    # 有多个重名，检查用户是否已选择
                                                    mapping_key = f"{match_value}_{idx}"
                                                    if mapping_key in st.session_state.get('duplicate_mappings', {}):
                                                        # 用户已选择，使用选择的索引
                                                        selected_idx = st.session_state.duplicate_mappings[mapping_key]
                                                        match_mask = pd.Series([False] * len(st.session_state.grades_df), index=st.session_state.grades_df.index)
                                                        match_mask.loc[selected_idx] = True
                                                    else:
                                                        # 用户未选择，跳过此行
                                                        unmatched_rows.append(f"第{idx+1}行：'{match_value}' 有 {match_count} 个重名，请在上方选择对应的学生")
                                                        continue
                                                else:
                                                    # 没有匹配
                                                    unmatched_rows.append(f"第{idx+1}行：未找到姓名 '{match_value}' 的学生")
                                                    continue
                                        
                                        if match_mask is not None and match_mask.any():
                                            matched_count += 1
                                            
                                            # 检查列名，判断是否是文本类型的列（如学校、班级等）
                                            col_lower = str(score_col).lower()
                                            is_text_column = any(keyword in col_lower for keyword in ['学校', '班级', 'class', 'school', '名称', 'name'])
                                            
                                            # 对于文本列，处理方式不同
                                            if is_text_column:
                                                # 文本列：直接使用原始值，不需要转换
                                                if pd.notna(score_value):
                                                    # 转换为字符串并清理
                                                    score_str = str(score_value).strip()
                                                    # 如果转换后是无效字符串，设为None
                                                    if score_str in ['', 'nan', 'None', 'NaN', 'NaT']:
                                                        final_value = None
                                                    else:
                                                        final_value = score_str
                                                    st.session_state.grades_df.loc[match_mask, final_col_name] = final_value
                                                    updated_count += 1
                                                else:
                                                    # 如果是NaN，直接设为None
                                                    st.session_state.grades_df.loc[match_mask, final_col_name] = None
                                            else:
                                                # 数值列：尝试转换为数字
                                                if pd.notna(score_value):
                                                    score_str = str(score_value).strip()
                                                    try:
                                                        score_float = float(score_str)
                                                        st.session_state.grades_df.loc[match_mask, final_col_name] = score_float
                                                        updated_count += 1
                                                    except (ValueError, TypeError):
                                                        # 如果无法转换为数字，但仍保留文本值（而不是跳过）
                                                        # 这样可以支持混合类型的列
                                                        final_value = score_str if score_str not in ['', 'nan', 'None', 'NaN', 'NaT'] else None
                                                        st.session_state.grades_df.loc[match_mask, final_col_name] = final_value
                                                        updated_count += 1
                                                else:
                                                    # 如果是NaN，保持为None
                                                    st.session_state.grades_df.loc[match_mask, final_col_name] = None
                                
                                # 不再设置作业状态（已移除作业状态列）
                                
                                save_data()  # 自动保存
                                
                                success_msg = f"✅ 成功匹配 {matched_count} 名学生，更新 {updated_count} 条数据记录！"
                                if added_cols:
                                    success_msg += f"\n新增数据列：{', '.join(str(col) for col in added_cols)}"
                                
                                if unmatched_rows:
                                    success_msg += f"\n\n⚠️ 未匹配 {len(unmatched_rows)} 行："
                                    for msg in unmatched_rows[:10]:  # 只显示前10个
                                        success_msg += f"\n- {msg}"
                                    if len(unmatched_rows) > 10:
                                        success_msg += f"\n... 还有 {len(unmatched_rows) - 10} 行未匹配"
                                
                                st.success(success_msg)
                                # 不清除重名映射，保留用户的选择以便下次查看或重新导入时记住选择
                                # 如果需要清除，可以在用户明确要求时清除
                                st.rerun()
                
            except Exception as e:
                st.error(f"导入失败：{str(e)}")
        
        # 表格编辑
        st.markdown("---")
        # 统计记录数量，并整合数据加载信息
        total_records = len(st.session_state.grades_df)
        
        # 获取保存时间信息
        saved_info = ""
        last_saved = st.session_state.get('last_saved_time', '')
        if last_saved:
            try:
                saved_time = datetime.fromisoformat(last_saved)
                time_str = saved_time.strftime("%Y-%m-%d %H:%M:%S")
                saved_info = f" | 最后保存：{time_str}"
            except:
                saved_info = " | 已自动加载保存的数据"
        
        st.markdown(f"### ✏️ 数据编辑（共 {total_records} 条记录{saved_info}）")
        
        display_df = st.session_state.grades_df.copy()
        
        # 快捷提示 - 使用更好的样式，更通用的描述
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 1.5rem;">
            <strong>💡 编辑技巧</strong>：在表格中可以直接编辑数据，使用 <kbd>Tab</kbd> 键切换单元格，输入后按 <kbd>Enter</kbd> 保存。数值列支持直接输入数字，文本列支持输入文本。
        </div>
        """, unsafe_allow_html=True)
        
        # 动态构建column_config（只包含基础列和导入的成绩列）
        column_config_dict = {
        "学号": st.column_config.TextColumn("学号", disabled=True),
        "姓名": st.column_config.TextColumn("姓名", disabled=True)
        }
            
        # 添加所有数值列作为可编辑的成绩列
        numeric_cols = display_df.select_dtypes(include=['number']).columns.tolist()
            
        # 文本类型列（如学校、班级等）使用文本列配置
        text_cols = ['学校', '班级']  # 明确指定文本列
        for col in display_df.columns:
            if col in ['学号', '姓名', '班级']:  # 这些列已经配置过了
                continue
            
            col_lower = str(col).lower()
            is_text_col = any(keyword in col_lower for keyword in ['学校', '班级', 'class', 'school'])
            
            if is_text_col:
                # 文本列：使用文本列配置（可编辑）
                if col not in column_config_dict:
                    column_config_dict[col] = st.column_config.TextColumn(
                        col,
                        help=f"编辑{col}信息"
                    )
            elif col in numeric_cols:
                # 数值列：使用数字列配置（不限制范围，适应一般情况）
                if col not in column_config_dict:
                    column_config_dict[col] = st.column_config.NumberColumn(
                        col,
                        step=0.01,
                        format="%.2f",
                        help=f"编辑{col}的数值"
                    )
            
        # 如果有班级列，添加班级列配置
        if '班级' in display_df.columns:
            column_config_dict["班级"] = st.column_config.TextColumn("班级", disabled=True)
            
        # 表格编辑器
        edited_df = st.data_editor(
            display_df,
            column_config=column_config_dict,
            hide_index=True,
            num_rows="fixed",
            width='stretch',
            key="grade_editor"
        )
        
        # 保存和导出按钮 - 使用更好的布局，确保对齐
        st.markdown("")
        col_save1, col_save2, col_save3, col_save4 = st.columns([1, 1, 1, 1])
        
        with col_save2:
            if st.button("💾 保存更改", type="primary", use_container_width=True):
                st.session_state.grades_df = edited_df
                save_data()  # 自动保存
                st.success("✅ 保存成功！数据已自动保存")
                st.rerun()
        
        with col_save3:
            # 导出为Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.grades_df.to_excel(writer, index=False, sheet_name='数据统计')
            output.seek(0)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 导出Excel",
                data=output,
                file_name=f"数据统计_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# 在文件末尾调用 main() 函数
# Streamlit 会从上到下执行所有代码，包括这个函数调用
# 注意：必须使用 streamlit run app.py 命令启动，不能直接用 python app.py
main()

