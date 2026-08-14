# pptx2pdfcrop

把 PowerPoint 中指定的幻灯片导出为**无白边、适合论文插图的 PDF**。

- 项目网站：[lijinzh.github.io/pptx2pdfcrop](https://lijinzh.github.io/pptx2pdfcrop/)
- English summary: [README.en.md](README.en.md)

项目只支持 Windows，并直接调用桌面版 Microsoft PowerPoint。默认使用 `vector`
模式：PowerPoint 原生导出矢量 PDF，再通过修改页面边界最大限度裁掉白边。文字、
路径和矢量图形不会被整页栅格化，适合论文插图和后续放大排版。

对于无法从源 PPT 中消除的复杂透明渐变或软遮罩问题，仍可显式使用
`--mode compatible`，让 PowerPoint 先渲染高分辨率 TIFF，再生成兼容性更强的图片 PDF。

## 功能

- 按页码导出：`8`、`1,3-5` 或 `all`
- 默认 PowerPoint 原生矢量 PDF，保留文字和绘图对象
- 高分辨率检测内容边界，最大限度去除白边
- 可选 TIFF 扁平化兼容模式，支持 JPEG 4:4:4 或无损压缩
- 多页输入合并成一个 PDF，每一页独立裁切
- 临时 TIFF/JPEG 自动清理，默认只留下最终 PDF
- `doctor` 命令检查 PowerPoint 自动化环境

## 系统要求

- Windows 10/11
- 桌面版 Microsoft PowerPoint
- Python 3.10 或更高版本
- 推荐使用 [uv](https://docs.astral.sh/uv/)

不支持 PowerPoint 网页版、WPS、Linux 或 macOS。源文件可以处于打开状态，工具会用
独立的只读 PowerPoint 实例读取磁盘中已经保存的版本。

## 安装

从 GitHub 安装：

```powershell
uv tool install git+https://github.com/Lijinzh/pptx2pdfcrop.git
```

本地开发安装：

```powershell
git clone https://github.com/Lijinzh/pptx2pdfcrop.git
cd pptx2pdfcrop
uv sync --extra dev
uv run pptx2pdfcrop doctor
```

## 使用

默认矢量模式：导出第 8 页，自动生成文件名：

```powershell
pptx2pdfcrop export .\绘图.pptx --slides 8
```

指定输出文件：

```powershell
pptx2pdfcrop export .\绘图.pptx --slides 8 -o .\figure-8.pdf
```

导出多页并逐页裁切：

```powershell
pptx2pdfcrop export .\绘图.pptx --slides 1,3-5 -o .\figures.pdf
```

包含复杂透明效果时，可显式启用 TIFF 兼容模式：

```powershell
pptx2pdfcrop export .\绘图.pptx --slides 8 --mode compatible
```

兼容模式下如果文件偏大，可降低 DPI 或 JPEG 质量：

```powershell
pptx2pdfcrop export .\绘图.pptx --slides 8 --mode compatible --dpi 450 --jpeg-quality 92
```

完全无损的兼容模式（文件通常明显更大）：

```powershell
pptx2pdfcrop export .\绘图.pptx --slides 8 --mode compatible --compression lossless
```

覆盖已有输出文件：

```powershell
pptx2pdfcrop export .\绘图.pptx --slides 8 -o .\figure-8.pdf --force
```

## 去白边参数

默认参数会保留每一个非纯白像素，并在四周留下 `0.5 pt` 的防截断边距：

```powershell
pptx2pdfcrop export .\绘图.pptx --slides 8 --white-threshold 255 --padding 0.5
```

- `--white-threshold 255`：只有纯白色被视为白边，最适合保留渐隐边缘。
- 将阈值降低到 `250` 或 `245`：会把接近白色的像素也裁掉，更激进。
- `--padding 0`：完全贴边；不推荐，部分阅读器可能截掉最外层抗锯齿像素。

矢量模式使用高分辨率 PDF 渲染结果检测边界，但只修改 PDF 页面框，不会栅格化内容。
兼容模式则在 TIFF 阶段、早于 JPEG 压缩时完成白边检测。

## 清晰度与体积建议

| 使用场景 | DPI | JPEG 质量 | 说明 |
|---|---:|---:|---|
| 兼容模式论文综合图 | 600 | 92 | 照片和文字兼顾 |
| 更小文件 | 450 | 92 | 通常仍足够清晰 |
| 极细线条/后续大幅缩放 | 600-900 | 95-97 | 文件会增大 |
| 必须逐像素无损 | 600 | `--compression lossless` | 文件最大 |

JPEG 模式使用 4:4:4 色度采样，避免文字和彩色细线因常见的 4:2:0 采样而发糊。PDF 中
直接嵌入已经压缩好的图片，不进行第二次有损重编码。

在项目自带的论文综合图测试中，600 DPI、质量 92 的单页结果约为 1.75 MiB；同分辨率
无损结果约为 4.07 MiB。实际大小取决于照片和图形复杂度。

## 默认矢量工作流程

```text
PPT/PPTX
  -> PowerPoint 原生导出矢量 PDF
  -> 高分辨率检测非白色内容边界
  -> 平移原始 PDF 内容并重设页面框
  -> 只保留裁切后的矢量 PDF
```

## TIFF 兼容工作流程

```text
PPT/PPTX
  -> PowerPoint 按指定页导出高分辨率 TIFF
  -> 在无损 TIFF 上检测非白色内容边界
  -> 裁切并保留极小安全边距
  -> JPEG 4:4:4 或无损编码
  -> 直接嵌入多页 PDF
  -> 删除全部临时文件，只保留最终 PDF
```

复杂透明叠层在不同 PDF 阅读器中仍可能显示不一致，此时应先从 PPT 源文件修正透明素材，
或者显式选择 `--mode compatible`。

## 开发与测试

```powershell
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run pptx2pdfcrop doctor
```

PowerPoint 端到端测试必须在安装了桌面版 PowerPoint 的 Windows 机器上运行。普通单元
测试不启动 PowerPoint。

## 项目结构

```text
src/pptx2pdfcrop/
  cli.py          命令行参数与终端输出
  models.py       导出选项和结果数据模型
  pages.py        幻灯片页码解析
  powerpoint.py   PowerPoint COM 后端
  geometry.py     像素内容边界检测
  vector_pdf.py   保留矢量内容的 PDF 裁切
  raster_pdf.py   compatible 模式图片编码与 PDF 生成
  pipeline.py     两种模式的统一编排
docs/             中英文静态网站
tests/            不依赖 PowerPoint 的单元测试
```

## 实现依据

- [Microsoft PowerPoint `Slide.Export`](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slide.export)
- [Microsoft PowerPoint `Presentation.ExportAsFixedFormat`](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentation.exportasfixedformat)
- [Pillow 图像格式与 TIFF/JPEG 参数](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)

## 许可证

[MIT](LICENSE)
