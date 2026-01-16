"""
拼音工具模块
"""
from pypinyin import lazy_pinyin, Style

def get_pinyin_initials(name):
    """获取姓名的拼音首字母"""
    try:
        pinyin_list = lazy_pinyin(name, style=Style.FIRST_LETTER)
        return ''.join(pinyin_list).upper()
    except:
        return ''

