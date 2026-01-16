"""
创建示例学生名单Excel文件
"""
import pandas as pd

# 创建示例数据
data = {
    '学号': ['2021001', '2021002', '2021003', '2021004', '2021005'],
    '姓名': ['张三', '李四', '王五', '赵六', '钱七']
}

df = pd.DataFrame(data)
df.to_excel('sample_students.xlsx', index=False, engine='openpyxl')
print("已创建示例文件: sample_students.xlsx")

