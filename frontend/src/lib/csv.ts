/**
 * 下载 CSV 文件：带 BOM，Excel 直接打开不乱码
 * @param fileName 文件名
 * @param header 表头
 * @param rows 数据行
 */
export function downloadCsv(
  fileName: string,
  header: string[],
  rows: string[][],
): void {
  const escape = (value: string): string => {
    const text = value ?? ''
    return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
  }
  const content = [header, ...rows]
    .map((row) => row.map(escape).join(','))
    .join('\r\n')
  const blob = new Blob(['\uFEFF' + content], {
    type: 'text/csv;charset=utf-8;',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
