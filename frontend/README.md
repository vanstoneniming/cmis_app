# 前端结构

Vue 3 + TypeScript + Vite，纯静态应用。

## 目录

- `src/App.vue`：页面编排、会话持久化、导入/合并面板开关、导出与清空。
- `src/components/`
  - `WorkflowRail.vue`：左侧三步工作流。
  - `DataWorkspace.vue`：首屏引导或数据工作区。
  - `DataTable.vue`：可编辑表格、搜索、班级筛选、移动端横向滚动。
  - `RosterImportSheet.vue`：名单导入侧滑面板，含工作表、跳过行、列映射、预览。
  - `MergeSheet.vue`：成绩合并侧滑面板，含匹配列、数据列选择、重名核对。
  - `PreviewTable.vue`、`FileDropzone.vue`、`BaseSheet.vue`、`SummaryStrip.vue`、`ReportBanner.vue`、`ToastStack.vue` 等基础组件。
- `src/lib/cells.ts`：单元格空值、日期、数字、学号字符串的统一处理。
- `src/lib/transform.ts`：纯函数核心逻辑——表头识别、列类型判断、姓名/学号拆分、学生行生成、重名检测、列合并、完整度计算。
- `src/lib/excel.ts`：SheetJS 按需加载、工作簿读取、工作表转二维数组、Excel 导出。
- `src/stores/session.ts`：当前会话的列与行、导入报告、`sessionStorage` 持久化。
- `src/stores/toasts.ts`：全局通知。
- `src/lib/__tests__/transform.test.ts`：核心算法单元测试。

## 数据流

1. 文件通过 `FileDropzone` 选择，`RosterImportSheet` / `MergeSheet` 用 `readWorkbook` 解析。
2. 工作表转成二维数组后，`gridToTable` 处理跳过行、表头、重复列名和空列。
3. 名单导入：`prepareRosterTable` 拆分合并列并识别映射；`buildStudentsFromTable` 只保留「姓名(学号)」学生块，过滤标题行与统计行，生成 `学号/姓名/班级` 并给出识别结果预览。
4. 成绩合并：`analyzeTable` 判断数值列与文本列；`scoreMatchColumns` / `suggestMatchColumn` 按与基准名单的重合率推荐匹配列；`computeDuplicateConflicts` 找出重名并按班级预选；`mergeData` 完成匹配和列写入，基准名单中没有的记录会被忽略。
5. 数据写入 Pinia 后由 `DataTable` 渲染编辑；导出用 SheetJS 生成 `.xlsx`。

## 约束

- 数据处理都在浏览器内完成，没有后端接口。
- 会话数据写入 `sessionStorage`，关闭标签页即清空；大文件受浏览器内存限制。
- 数值列按「列名关键词或 70% 以上样本可转数字」判断；学号、班级、姓名等列强制保留为文本，避免前导零和 `.0` 问题。
- 匹配列只支持姓名类或学号类列，其他列会在合并面板中提示不可用。
- 合并时以基准名单为准：成绩表里多出来、基准名单中没有的学号/姓名会作为“已忽略”处理。
- 宽成绩表默认只预选「总分」等主要成绩列，避免一次导入几百个题目列。

## 验证

```bash
npm test
npm run typecheck
npm run build
```
