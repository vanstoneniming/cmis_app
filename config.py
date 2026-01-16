"""
系统配置文件
"""
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# 数据库文件路径
DATABASE_PATH = DATA_DIR / "student_management.db"

# 备份目录
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# 默认配置
DEFAULT_SCORE_MAX = 100.0
DEFAULT_SCORE_MIN = 0.0

# 任务类型
TASK_TYPE_HOMEWORK = "作业"
TASK_TYPE_EXAM = "考试"

TASK_TYPES = [TASK_TYPE_HOMEWORK, TASK_TYPE_EXAM]

# 任务状态
TASK_STATUS_ONGOING = "进行中"
TASK_STATUS_CLOSED = "已截止"
TASK_STATUS_ARCHIVED = "已归档"

TASK_STATUSES = [TASK_STATUS_ONGOING, TASK_STATUS_CLOSED, TASK_STATUS_ARCHIVED]

# 提交状态
SUBMIT_STATUS_NOT_SUBMITTED = "未提交"
SUBMIT_STATUS_SUBMITTED = "已提交"

SUBMIT_STATUSES = [SUBMIT_STATUS_NOT_SUBMITTED, SUBMIT_STATUS_SUBMITTED]

# 用户角色
ROLE_SUPER_ADMIN = "super_admin"
ROLE_SCHOOL_ADMIN = "school_admin"
ROLE_TEACHER = "teacher"
ROLE_TA = "ta"
ROLE_STUDENT = "student"

ROLES = {
    ROLE_SUPER_ADMIN: "超级管理员",
    ROLE_SCHOOL_ADMIN: "学校管理员",
    ROLE_TEACHER: "教师",
    ROLE_TA: "助教",
    ROLE_STUDENT: "学生"
}

