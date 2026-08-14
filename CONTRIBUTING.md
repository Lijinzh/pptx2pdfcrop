# Contributing

感谢参与 `pptx2pdfcrop`。

## 开发环境

项目仅支持 Windows。普通单元测试不需要 PowerPoint，但端到端导出测试要求安装桌面版
Microsoft PowerPoint。

```powershell
uv sync --extra dev
uv run pytest
uv run ruff check .
uv build
uv run pptx2pdfcrop doctor
```

## 提交要求

- 不要把测试用 PPT、论文原图或临时 TIFF 提交到仓库。
- 新增裁切逻辑时，需要覆盖纯白背景、近白色渐变和零安全边距场景。
- 修改默认 DPI、JPEG 质量或色度采样时，需要给出文件体积和放大画质对比。
- PowerPoint COM 调用必须使用独立实例、只读打开源文件，并确保异常时关闭实例。
- 用户可见文档优先使用简体中文，并同步更新必要的英文摘要。
- 修改官网时，需要检查 1440px 桌面视口和 390px 移动视口，并确认中英文页面一致。

## Pull Request

请在 PR 中说明：

1. 修改解决了什么问题；
2. 使用了什么 PPT/页码进行验证；
3. 输出 PDF 的 DPI、压缩参数和大小变化；
4. 是否影响默认 `vector` 模式或可选 `compatible` 模式。
