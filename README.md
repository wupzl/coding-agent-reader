# Agent 帝国：代码审判者

九章小说式 Coding Agent 工程阅读，沿用 AI 纪元的阅读样式，适配手机与桌面。第一卷完结，第二卷仅保留原文预告。

- [在线阅读](https://wupzl.github.io/coding-agent-reader/)
- [学习书架](https://wupzl.github.io/)
- [内容整理与技术依据](EDITORIAL.md)

## 阅读功能

全书搜索、章内目录、上下章切换、纯白/米白/深色背景、字号调整、阅读进度记忆、多位置书签、代码高亮与复制、七个本地交互实验和二十七道带解析的章末练习。

实验覆盖 Agent 状态循环、代码检索、Bug 证据判断、跨实例幂等、Worker 与配额、权限闸门、尝试预算。均为浏览器内的教学模拟，不调用模型、不读取仓库、不执行后端任务。阅读记录保存在当前浏览器，“我的阅读”中可查看和清除。

## 构建与预览

需要 Python 3.10+ 与 Node.js。KaTeX 的 MathML 渲染器随仓库提供，无需 npm 安装或外部 CDN。

```bash
python -m pip install -r requirements.txt
python build.py
python -m http.server 4175 --directory docs --bind 127.0.0.1
```

访问 `http://127.0.0.1:4175/`。项目切换与书架链接使用 GitHub Pages 的根路径，本地跨项目验收由学习书架的检查脚本提供。

## 内容维护

修改 `chapters/01.md` 至 `09.md`，章节信息同步更新 `book.json`，练习位于 `assets/questions.json`。运行 `python build.py` 重新生成 `docs/`，提交源文件与生成结果。

`source/codingagent.original.md` 保留原始文档。`scripts/prepare_content.py` 是一次性导入脚本，再次运行会用原始文档覆盖维护后的章节；常规编辑不需要运行它。`CONTENT_REVIEW.json` 记录导入时的代码块和图表残留处理。

## 验证

```bash
python -m playwright install chromium
python verify.py
```

检查全部页面的本地链接、锚点、静态资源、手机/平板/桌面布局、搜索、持久化、书签、代码复制、三个主题、全部练习与七类交互。截图写入未跟踪的 `test-results/`。

## 发布与导航

GitHub Pages 从 `main` 分支的 `/docs` 发布，仓库为公开项目，无需后端。所有页面保留学习书架与七项目切换入口。

跨项目维护脚本 `scripts/integrate_bookshelf.py` 会更新同级六个阅读仓库的已生成页面、源生成器和学习书架验收配置。运行前应确认这些仓库的工作区状态。该脚本本身不提交或推送。

第三方 KaTeX 许可证见 `vendor/KaTeX-LICENSE.txt`。


项目切换菜单已接入 [面试官的审判](https://wupzl.github.io/interview-proof-reader/)，七章技术面试小说与七组本地训练，第八章待续。


项目切换菜单已接入 [LangChain 帝国](https://wupzl.github.io/langchain-empire-reader/)，五章正文，第六章待续。
