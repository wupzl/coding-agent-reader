"""Add this book to all six sibling readers and the shared bookshelf."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
SLUG='coding-agent-reader'
LINK=f'<a href="/{SLUG}/">Agent 帝国</a>'
READERS=['pytorch-apprentice','ai-era-reader','data-empire-reader','rag-empire-reader','system-design-reader','online-troubleshooting-reader']

def edit(path,transform):
    original=path.read_text(encoding='utf-8')
    updated=transform(original)
    if updated!=original:path.write_text(updated,encoding='utf-8')

def menu(text):
    def add(m):return m[0] if f'/{SLUG}/' in m[1] else f'<div class="shelf-menu">{m[1]}{LINK}</div>'
    return re.sub(r'<div class="shelf-menu">(.*?)</div>',add,text,flags=re.S)

def generator(text):
    if f"('{SLUG}'" in text:return text
    for item in ["('online-troubleshooting-reader', '生产环境')","('online-troubleshooting-reader','生产环境')", "(SLUG, '生产环境')"]:
        if item in text:return text.replace(item,item+f", ('{SLUG}', 'Agent 帝国')",1)
    raise AssertionError('Generator project list not found')

def main():
    for slug in READERS:
        repo=ROOT/slug
        for page in (repo/'docs').glob('*.html'):edit(page,menu)
        if (repo/'build.py').exists():edit(repo/'build.py',menu if slug=='pytorch-apprentice' else generator)
        readme=repo/'README.md'
        edit(readme,lambda s:s if 'coding-agent-reader' in s else s+'\n\n项目切换菜单已接入 [Agent 帝国：代码审判者](https://wupzl.github.io/coding-agent-reader/)，九章小说式 Coding Agent 工程阅读。\n')
        verify=repo/'verify.py'
        if verify.exists():edit(verify,lambda s:s.replace("page.locator('.shelf-menu a').count() == 6","page.locator('.shelf-menu a').count() == 7"))
    shelf=ROOT/'bookshelf'
    card='''<a class="project green" href="/coding-agent-reader/"><div class="cover" aria-hidden="true"><span class="volume">07 / THE CODE TRIBUNAL</span><strong>Agent 帝国<span class="cover-subtitle">代码审判者</span></strong><span class="symbol">A</span><span class="cover-foot">证据 · 补丁 · 验证</span></div><div class="project-copy"><p class="category">CODING AGENT · 工程小说</p><h3>Agent 帝国：代码审判者</h3><p>跟随林川与陈工，从一条仓库 URL 走进检索、复现、补丁、沙箱与评测，在故事和本地实验中理解可信的自动修复。</p><div class="tags"><span>9 章</span><span class="project-status">第一卷完</span><span>7 个交互实验 · 27 道练习</span></div><span class="enter">进入阅读 <span aria-hidden="true">↗</span></span></div></a>'''
    def home(s):
        if f'/{SLUG}/' not in s:
            marker='</div><div class="shelf-note">';assert marker in s
            s=s.replace(marker,card+marker,1)
        return s.replace('06 / 持续更新','07 / 持续更新')
    edit(shelf/'index.html',home)
    def verify(s):
        if f"'{SLUG}':" not in s:s=s.replace("    'online-troubleshooting-reader': '连载',","    'online-troubleshooting-reader': '连载',\n    'coding-agent-reader': '第一卷完',")
        return s.replace('six','seven')
    edit(shelf/'verify.py',verify)
    def workflow(s):
        if f'repository: wupzl/{SLUG}' not in s:
            marker='      - uses: actions/setup-python@v5'
            s=s.replace(marker,f'      - uses: actions/checkout@v4\n        with:\n          repository: wupzl/{SLUG}\n          ref: main\n          path: {SLUG}\n'+marker,1)
            marker='      - name: Verify system design reader'
            s=s.replace(marker,'      - name: Verify Coding Agent reading features\n        run: python coding-agent-reader/verify.py\n'+marker,1)
            s=s.replace('            online-troubleshooting-reader/test-results/','            online-troubleshooting-reader/test-results/\n            coding-agent-reader/test-results/')
        return s.replace('all six readers','all seven readers')
    edit(shelf/'.github/workflows/verify-readers.yml',workflow)
    edit(shelf/'README.md',lambda s:s.replace('系统设计和生产环境六个阅读项目','系统设计、生产环境和 Agent 帝国七个阅读项目').replace('其余六个仓库','其余七个仓库').replace('六项目切换菜单','七项目切换菜单').replace('六个阅读仓库','七个阅读仓库').replace('`online-troubleshooting-reader/` 目录中','`online-troubleshooting-reader/`、`coding-agent-reader/` 目录中').replace('生产环境 4 章（连载，第五章待续）。','生产环境 4 章（连载，第五章待续）、Agent 帝国 9 章（第一卷完）。')+'\n\nAgent 帝国的完整交互验收：`python coding-agent-reader/verify.py`。\n' if 'Agent 帝国的完整交互验收' not in s else s)
    print('Integrated seven readers, all source generators, bookshelf and shared CI checks.')

if __name__=='__main__':main()
