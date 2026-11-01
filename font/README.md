# font/

| 文件 | 说明 |
|---|---|
| `ZCOOLKuaiLe-Regular.ttf` | 站酷快乐体（ZCOOL KuaiLe），SIL Open Font License 1.1，可自由使用、修改、再分发（需保留 `OFL.txt`） |
| `OFL.txt` | 上面这个字体的授权全文 |
| `STKAITI.TTF` | 华文楷体，商业字体，**不在仓库里**（.gitignore 已排除），仅原作者本机保留 |

- 字体来源：<https://github.com/googlefonts/zcool-kuaile>（Google Fonts 收录的 ZCOOL KuaiLe）
- Copyright 2018 The ZCOOL KuaiLe Project Authors
- 游戏只拿它显示左上角的“当前得分”，字号 20

`game.py` 的加载顺序：`ZCOOLKuaiLe-Regular.ttf` → `STKAITI.TTF` → 系统字体（微软雅黑 / 黑体 / 苹方）。
