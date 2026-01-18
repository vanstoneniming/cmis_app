#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查依赖版本是否符合要求
用于验证虚拟环境中的库版本是否正确
"""

from __future__ import print_function
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
            print("✅ {}: {} >= {}".format(package_name, installed_version, min_version))
            return True
        else:
            print("❌ {}: {} < {} (需要 >= {})".format(package_name, installed_version, min_version, min_version))
            return False
    except Exception as e:
        print("⚠️  {}: 无法比较版本 ({})".format(package_name, e))
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
            print("❌ {}: 未安装".format(package))
            all_ok = False
        except Exception as e:
            print("⚠️  {}: 检查失败 ({})".format(package, e))
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

