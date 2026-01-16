"""
数据库迁移脚本 - 添加新列到现有表
"""
import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_PATH

def migrate_database():
    """迁移数据库，添加新列"""
    if not DATABASE_PATH.exists():
        print("数据库不存在，将在首次使用时自动创建")
        return True
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查courses表是否存在creator_id列
        cursor.execute("PRAGMA table_info(courses)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations_applied = []
        
        # 迁移1: 添加creator_id到courses表
        if 'creator_id' not in columns:
            try:
                cursor.execute("ALTER TABLE courses ADD COLUMN creator_id INTEGER")
                migrations_applied.append("Added creator_id to courses")
                print("✅ 添加 creator_id 列到 courses 表")
            except Exception as e:
                print(f"⚠️ 添加 creator_id 列失败（可能已存在）: {e}")
        
        # 迁移2: 添加school_id到courses表
        if 'school_id' not in columns:
            try:
                cursor.execute("ALTER TABLE courses ADD COLUMN school_id INTEGER")
                migrations_applied.append("Added school_id to courses")
                print("✅ 添加 school_id 列到 courses 表")
            except Exception as e:
                print(f"⚠️ 添加 school_id 列失败（可能已存在）: {e}")
        
        # 迁移3: 添加is_public到courses表
        if 'is_public' not in columns:
            try:
                cursor.execute("ALTER TABLE courses ADD COLUMN is_public BOOLEAN DEFAULT 0")
                migrations_applied.append("Added is_public to courses")
                print("✅ 添加 is_public 列到 courses 表")
            except Exception as e:
                print(f"⚠️ 添加 is_public 列失败（可能已存在）: {e}")
        
        # 检查并创建新表（users, schools, user_courses, audit_logs）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        # 创建users表（如果不存在）
        if 'users' not in existing_tables:
            cursor.execute("""
                CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    real_name VARCHAR(100),
                    role VARCHAR(20) NOT NULL DEFAULT 'teacher',
                    school_id INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    FOREIGN KEY(school_id) REFERENCES schools(school_id)
                )
            """)
            print("✅ 创建 users 表")
        
        # 创建schools表（如果不存在）
        if 'schools' not in existing_tables:
            cursor.execute("""
                CREATE TABLE schools (
                    school_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_name VARCHAR(200) NOT NULL,
                    domain VARCHAR(100),
                    settings TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ 创建 schools 表")
        
        # 创建user_courses表（如果不存在）
        if 'user_courses' not in existing_tables:
            cursor.execute("""
                CREATE TABLE user_courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    course_id INTEGER NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'ta',
                    granted_by INTEGER,
                    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(course_id) REFERENCES courses(course_id),
                    FOREIGN KEY(granted_by) REFERENCES users(user_id)
                )
            """)
            print("✅ 创建 user_courses 表")
        
        # 创建audit_logs表（如果不存在）
        if 'audit_logs' not in existing_tables:
            cursor.execute("""
                CREATE TABLE audit_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action VARCHAR(50) NOT NULL,
                    resource_type VARCHAR(50),
                    resource_id INTEGER,
                    description TEXT,
                    ip_address VARCHAR(50),
                    user_agent VARCHAR(500),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)
            print("✅ 创建 audit_logs 表")
        
        conn.commit()
        
        if migrations_applied:
            print(f"\n✅ 数据库迁移完成！应用了 {len(migrations_applied)} 个迁移")
        else:
            print("\n✅ 数据库已是最新版本，无需迁移")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

