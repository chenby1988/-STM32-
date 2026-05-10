# 论文目录

本目录包含项目的研究论文，提供中文版与英文版两个版本。

## 文件说明

| 文件 | 说明 | 页数 | 大小 |
|------|------|------|------|
| `main.tex` | LaTeX 源文件（中文版） | - | ~60 KB |
| `main_en.tex` | LaTeX 源文件（英文版） | - | ~55 KB |
| `paper_chinese.pdf` | 中文版论文 PDF | 53 页 | ~788 KB |
| `paper_english.pdf` | 英文版论文 PDF | 58 页 | ~256 KB |
| `paper_french.pdf` | 法文版论文 PDF | - | ~293 KB |
| `paper_spanish.pdf` | 西班牙文版论文 PDF | - | ~285 KB |
| `paper_russian.pdf` | 俄文版论文 PDF | - | ~301 KB |
| `paper_arabic.pdf` | 阿拉伯文版论文 PDF | - | ~328 KB |

## 在线查看

- [中文版 PDF](https://github.com/chenby1988/-STM32-/blob/main/paper/paper_chinese.pdf)
- [英文版 PDF](https://github.com/chenby1988/-STM32-/blob/main/paper/paper_english.pdf)
- [法文版 PDF](https://github.com/chenby1988/-STM32-/blob/main/paper/paper_french.pdf)
- [西班牙文版 PDF](https://github.com/chenby1988/-STM32-/blob/main/paper/paper_spanish.pdf)
- [俄文版 PDF](https://github.com/chenby1988/-STM32-/blob/main/paper/paper_russian.pdf)
- [阿拉伯文版 PDF](https://github.com/chenby1988/-STM32-/blob/main/paper/paper_arabic.pdf)

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