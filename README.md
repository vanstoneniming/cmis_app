# CMIS 数据合并台

基于 **Vue 3 + TypeScript** 的 Excel 名单合并工具。把两份顺序不同的 Excel 按姓名或学号合并成一张表，解析、编辑、导出全部在浏览器里完成，不上传服务器。

## 功能

- 导入 `.xlsx` / `.xls` 基准名单，自动识别姓名、学号、班级列
- 自动拆分「姓名 (学号)」格式，没有学号时生成唯一标识
- 自动跳过学生块之外的标题行、统计行（及格率、满分、成绩权值等）
- 导入前可预览识别出的学号/姓名/班级，确认后再加载
- 多工作表导入，可按工作表名补充班级
- 导入第二份 Excel，自动推荐与基准名单匹配率最高的姓名/学号列
- 基准名单中没有的学号/姓名会自动忽略，不影响其余数据导入
- 重名时按班级预选，并支持逐条核对，避免张冠李戴
- 宽成绩表默认只勾选「总分」等主要成绩列，也可手动扩展或全选数值列
- 表格内直接编辑；学号、姓名、班级为锁定字段
- 按原文件的工作表（班级）分组，一键把数据复制成制表符表格，直接粘回受保护的原始文件
- 导出 `.xlsx` 时按基础文件的工作表拆分，表名与顺序与原文件一致
- 工具只处理数据，不回写原始文件
- 数据保存在当前浏览器标签页的 `sessionStorage`，刷新不丢失，关闭标签页后清空

## 快速开始

需要 Node.js 20 或更高版本。

```bash
npm install
npm run dev
```

然后打开终端提示的地址（默认 `http://localhost:5173`）。也可以直接运行：

```bash
./start_vue.sh
```

## 常用命令

| 命令 | 作用 |
| --- | --- |
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 类型检查并构建到 `frontend/dist` |
| `npm run preview` | 预览生产构建 |
| `npm run typecheck` | 只做 TypeScript 类型检查 |
| `npm test` | 运行 Vitest 单元测试 |

## 项目结构

```text
cmis_app/
├── frontend/                  # Vue 3 + TypeScript 前端
│   ├── public/samples/        # 示例名单 / 成绩表
│   ├── src/
│   │   ├── components/        # 工作台、导入面板、数据表
│   │   ├── lib/               # Excel 读写、行列识别、合并算法
│   │   ├── stores/            # 会话数据、通知
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   └── vite.config.ts
├── app.py                     # 旧版 Streamlit 入口（保留）
├── modules/ database/ utils/  # 旧版 Python 模块（保留）
├── package.json               # npm workspace 与脚本
└── start_vue.sh               # Vue 版启动脚本
```

更细的前端结构说明见 [frontend/README.md](frontend/README.md)。

## 使用流程

1. **导入名单**：上传作为基准的 Excel，确认姓名列；学号、班级没有也可以，系统会自动生成学号。
2. **合并数据**：上传第二份 Excel。系统会根据与基准名单的重合率自动推荐姓名/学号匹配列；基准名单里没有的记录会自动忽略，不影响其余数据导入。重名时按班级预选，也可逐条核对。
3. **校对导出**：在数据表中直接修改数据列，学号、姓名、班级不可编辑。确认无误后可以：
   - **按工作表复制**：选工作表（班级）和要复制的列，复制成制表符表格，回到原 Excel 从第一名学生的单元格粘贴，原文件格式和单元格保护都不用动；
   - **导出 Excel**：生成新文件，工作表按基础文件拆开，顺序和表名与原文件对应。

小技巧：

- 文件顶部有标题、底部有汇总时，在导入面板设置「跳过顶部行 / 尾部行」。
- 多工作表名单可以一次全部导入，缺少班级列时用工作表名补充；导入后每行都记着来自哪个工作表。
- 复制与导出都按工作表（班级）逐个处理，不会把所有班合成一份；旧会话没有工作表信息时按班级拆分。
- 复制时建议从原文件该工作表第一名学生的单元格开始粘贴，行顺序与导入时一致。
- 合并列与已有列重名时，会自动添加 `_1`、`_2` 后缀，不会覆盖原列。

## 示例文件

- [示例名单](frontend/public/samples/sample_roster.xlsx)
- [示例成绩表](frontend/public/samples/sample_scores.xlsx)

也可以直接在应用首页下载这两个文件试用。

## 部署

构建静态文件：

```bash
npm run build
```

产物在 `frontend/dist/`，可部署到任意静态服务器。Apache 静态站点配置示例见 [apache_vue_config.conf.example](apache_vue_config.conf.example)。Vue 版没有后端进程，不需要再反代到 8501 端口。

## 技术栈

- Vue 3 + TypeScript + Vite
- Pinia（会话状态）
- SheetJS `xlsx`（浏览器内 Excel 解析与导出，按需加载）
- Lucide 图标

## 旧版 Streamlit

原始 Streamlit 版本仍完整保留在根目录（`app.py`、`requirements.txt`、`modules/`、`database/` 等），说明见 [README_STREAMLIT.md](README_STREAMLIT.md)。Vue 版不依赖 Python 后端，`app.py` 也没有引用 `modules/`、`database/` 那套多用户代码。

## 许可证

MIT License
