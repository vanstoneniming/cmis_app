#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查依赖版本是否符合要求
用于验证虚拟环境中的库版本是否正确
"""

import sys

def check_dependency(package_name, min_version, installed_version):
    """检查单个依赖版本"""
    try:
        from packaging import version
    except ImportError:
        print("⚠️  需要安装 packaging: pip install packaging")
        return False
    
    try:
        min_ver = version.parse(min_version)
        installed_ver = version.parse(installed_version)
        if installed_ver >= min_ver:
            print(f"✅ {package_name}: {installed_version} >= {min_version}")
            return True
        else:
            print(f"❌ {package_name}: {installed_version} < {min_version} (需要 >= {min_version})")
            return False
    except Exception as e:
        print(f"⚠️  {package_name}: 无法比较版本 ({e})")
        return False

def main():
    """主函数：检查所有依赖版本"""
    print("=" * 60)
    print("检查依赖版本...")
    print("=" * 60)
    print()
    
    # 依赖要求
    requirements = {
        'streamlit': '1.28.0',
        'pandas': '2.0.0',
        'openpyxl': '3.1.0',
        'xlrd': '2.0.1',
        'pypinyin': '0.49.0',
        'sqlalchemy': '2.0.0',
        'plotly': '5.18.0',
        'bcrypt': '4.0.0',
    }
    
    all_ok = True
    
    for package, min_version in requirements.items():
        try:
            mod = __import__(package)
            installed_version = getattr(mod, '__version__', 'unknown')
            if not check_dependency(package, min_version, installed_version):
                all_ok = False
        except ImportError:
            print(f"❌ {package}: 未安装")
            all_ok = False
        except Exception as e:
            print(f"⚠️  {package}: 检查失败 ({e})")
            all_ok = False
    
    print()
    print("=" * 60)
    if all_ok:
        print("✅ 所有依赖版本符合要求！")
        sys.exit(0)
    else:
        print("❌ 部分依赖版本不符合要求，请重新安装依赖：")
        print()
        print("   在虚拟环境中运行：")
        print("   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()

