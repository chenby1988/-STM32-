# 论文目录

本目录包含项目的研究论文，提供中文版与英文版两个版本。

## 文件说明

| 文件 | 说明 | 页数 | 大小 |
|------|------|------|------|
| `main.tex` | LaTeX 源文件（中文版） | - | ~60 KB |
| `main_en.tex` | LaTeX 源文件（英文版） | - | ~55 KB |
| `paper_chinese.pdf` | 中文版论文 PDF | 53 页 | ~788 KB |
| `paper_english.pdf` | 英文版论文 PDF | 58 页 | ~256 KB |

## 在线查看

- [中文版 PDF](https://github.com/chenby1988/-STM32-/blob/main/paper/paper_chinese.pdf)
- [英文版 PDF](https://github.com/chenby1988/-STM32-/blob/main/paper/paper_english.pdf)

## 本地编译

如需自行编译，请确保已安装 XeLaTeX（TeX Live 2023 或更高版本）：

```bash
# 中文版
xelatex main.tex
xelatex main.tex

# 英文版
xelatex main_en.tex
xelatex main_en.tex
```

> **注意**：中文版依赖 `ctex` 宏包与 Fandol 中文字体；英文版使用标准 `article` 文档类。
