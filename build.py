"""Build a portable GitHub Pages reader from maintained Markdown and local assets."""
from pathlib import Path
import html, json, re, shutil, subprocess
import markdown
from pygments.formatters import HtmlFormatter

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'docs'
BOOK=json.loads((ROOT/'book.json').read_text(encoding='utf-8'))
CHAPTERS=BOOK['chapters']
PROJECTS=[('pytorch-apprentice','PyTorch：炼金术士的学徒'),('ai-era-reader','AI 纪元'),('data-empire-reader','数据帝国'),('rag-empire-reader','RAG 帝国'),('system-design-reader','系统设计'),('online-troubleshooting-reader','生产环境'),('coding-agent-reader','Agent 帝国'), ('interview-proof-reader', '面试官的审判')]
LABS=[('loop','Agent 的下一步','逐步执行任务，观察证据、预算与停止条件。'),('retrieval','从描述找到代码','比较关键词和加入同义词的检索，观察候选文件。'),('verify','Bug 审判庭','依据需求、代码和运行证据，选择可支持的结论。'),('patch','两台服务器的订单','切换 JVM 锁与数据库约束，观察跨实例并发。'),('queue','云端任务调度','调整到达速率、Worker 与模型配额，观察积压。'),('guard','工具权限闸门','模拟路径、网络与凭证访问的运行时决策。'),('eval','一次成功与多次尝试','改变单次成功概率和尝试预算，理解计算假设。')]
CHAPTER_LAB=['loop','loop','retrieval','verify','patch','queue','guard','eval','loop']

def page(title,body,chapter=0):
    menu=''.join(f'<a href="/{slug}/"'+(' aria-current="page"' if slug=='coding-agent-reader' else '')+f'>{name}</a>' for slug,name in PROJECTS)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="Agent 帝国：代码审判者。九章小说式 Coding Agent 工程阅读，含本地交互实验与章末练习。"><title>{html.escape(title)} · Agent 帝国</title><script>try{{document.documentElement.dataset.theme=localStorage.getItem('coding-agent-theme')||'white';document.documentElement.style.setProperty('--reading-size',Math.max(16,Math.min(26,Number(localStorage.getItem('coding-agent-size'))||18))+'px')}}catch(e){{}}</script><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="shelf-nav.css"><link rel="stylesheet" href="reader.css"><link rel="stylesheet" href="syntax.css"><script src="app.js" defer></script><script src="labs.js" defer></script></head>
<body data-chapter="{chapter}"><a class="skip" href="#main">跳到正文</a><div id="progress" aria-hidden="true"></div><header><a class="brand" href="index.html">Agent 帝国<span>THE CODE TRIBUNAL</span></a><nav class="shelf-nav" aria-label="学习项目导航"><a class="shelf-home" href="/">← 学习书架</a><details class="shelf-switch"><summary>切换项目 ▾</summary><div class="shelf-menu">{menu}</div></details></nav><div class="controls"><button id="search-open" aria-label="搜索全书" title="搜索全书（/）">搜索</button><button id="smaller" aria-label="缩小字号">A−</button><button id="larger" aria-label="增大字号">A＋</button><button id="theme" aria-label="切换阅读背景">纯白</button></div></header>
{body}<footer><a href="index.html">Agent 帝国：代码审判者</a> · 第一卷完 · 九章<br><a href="practice.html">交互实验</a> · <a href="reading.html">我的阅读</a> · <a href="editorial.html">内容说明与来源</a> · <a href="https://github.com/wupzl/coding-agent-reader">项目源码 ↗</a><br><small>小说式工程学习 · 无需登录 · 记录保存在当前浏览器</small></footer>
<dialog id="search-dialog" aria-labelledby="search-title"><div class="dialog-heading"><h2 id="search-title">搜索全书</h2><button id="search-close" aria-label="关闭搜索">×</button></div><label for="query">关键词或代码，例如 幂等、Tool Registry、SSRF</label><input id="query" type="search" placeholder="搜索九章正文…" autocomplete="off"><p id="search-status" role="status">输入关键词开始搜索</p><div id="search-results"></div></dialog><div id="toast" role="status" aria-live="polite"></div></body></html>'''

def render(source):
    formulas=[]
    def stash(m):
        tex=m[1] if m[1] is not None else m[2]
        formulas.append({'tex':tex,'display':m[1] is not None})
        return f'MATHTOKEN{len(formulas)-1}END'
    chunks=re.split(r'(```.*?```|`[^`\n]+`)',source,flags=re.S)
    for i in range(0,len(chunks),2):
        # Manuscript HTML is text, never executable markup.
        chunks[i]=chunks[i].replace('<','&lt;').replace('>','&gt;') if re.search(r'<(?:script|iframe|style|img|svg|video)\b',chunks[i],re.I) else chunks[i]
        chunks[i]=re.sub(r'\\\[(.*?)\\\]|\\\((.*?)\\\)',stash,chunks[i],flags=re.S)
    md=markdown.Markdown(extensions=['fenced_code','tables','toc','sane_lists','codehilite'],extension_configs={'toc':{'toc_depth':'2-2','permalink':False},'codehilite':{'guess_lang':False}})
    rendered=md.convert(''.join(chunks))
    if formulas:
        run=subprocess.run(['node',str(ROOT/'render-math.cjs')],input=json.dumps(formulas),text=True,encoding='utf-8',capture_output=True,check=True)
        for i,value in enumerate(json.loads(run.stdout)): rendered=rendered.replace(f'MATHTOKEN{i}END',value)
    def code_controls(m):
        return '<div class="code-block"><button class="copy-code" type="button">复制代码</button>'+m[0]+'</div>'
    rendered=re.sub(r'<div class="codehilite">.*?</div>',code_controls,rendered,flags=re.S)
    return rendered,md.toc

def lab_html(name):
    title=next(x[1] for x in LABS if x[0]==name)
    return f'<section class="lab" data-lab="{name}" aria-label="{title}"><div class="lab-heading"><p class="eyebrow">LOCAL EXPERIMENT</p><h2>{title}</h2><p>浏览器内的教学模拟，数据与结果均非真实平台测量。</p></div><div class="lab-body"></div></section>'

def main():
    OUT.mkdir(exist_ok=True)
    sources=sorted((ROOT/'chapters').glob('[0-9][0-9].md'))
    assert len(sources)==len(CHAPTERS)==9
    metadata=[]; search=[]
    for i,(item,path) in enumerate(zip(CHAPTERS,sources)):
        n=i+1; source=path.read_text(encoding='utf-8')
        # Page heading is rendered once, outside article.
        source=source.split('\n',1)[1]
        source=re.sub(r'^\s*> 阅读提示：[^\n]+\n','',source,count=1)
        rendered,toc=render(source)
        minutes=max(5,round(len(re.sub(r'```.*?```','',source,flags=re.S))/450))
        metadata.append({**item,'minutes':minutes,'url':f'chapter-{n:02}.html'})
        booknav=''.join(f'<a href="chapter-{c["number"]:02}.html"'+(' aria-current="page"' if c['number']==n else '')+f'><span>{c["number"]:02}</span> {html.escape(c["title"])}</a>' for c in CHAPTERS)
        prev=f'<a href="chapter-{n-1:02}.html">← 上一章</a>' if n>1 else '<a href="index.html">← 全书目录</a>'
        nxt=f'<a href="chapter-{n+1:02}.html">下一章 →</a>' if n<9 else '<a href="index.html">第一卷完 · 返回目录 →</a>'
        body=f'''<div class="reader-layout"><aside><a href="index.html">← 全书导航</a><details class="book-toc"><summary>九章工程旅程</summary><nav aria-label="全书章节">{booknav}</nav></details><p class="eyebrow">本章目录</p>{toc}<a href="reading.html">我的进度与书签 →</a></aside><main id="main" class="chapter-main"><div class="chapter-heading"><p class="eyebrow">CHAPTER {n:02} / 09 · 约 {minutes} 分钟</p><h1>{html.escape(item['title'])}</h1><p>{item['topics']}</p><div class="chapter-tools"><button id="bookmark" type="button" aria-pressed="false">收藏当前位置</button><a href="reading.html">我的阅读 →</a><span id="read-status" role="status"></span></div></div><details class="mobile-toc"><summary>章节与本章目录</summary><nav class="book-links">{booknav}</nav>{toc}</details><details class="editor-note"><summary>阅读提示 · {item['note_title']}</summary><p>{html.escape(item['note'])}</p></details><article>{rendered}</article><section class="chapter-extras"><h2>把这一章放进实验</h2>{lab_html(CHAPTER_LAB[i])}<a class="text-link" href="practice.html">全部七个交互实验 →</a></section><section class="quiz" data-quiz="{n}" aria-label="第{n}章练习"><h2>章末练习</h2><p>三道题，检查你是否理解了工程取舍。</p><div class="quiz-body"></div></section><nav class="chapter-nav" aria-label="上下章">{prev}{nxt}</nav></main></div>'''
        (OUT/f'chapter-{n:02}.html').write_text(page(item['title'],body,n),encoding='utf-8')
        sections=re.split(r'(<h[23] id="[^"]+">.*?</h[23]>)',rendered,flags=re.S)
        anchor=''; heading='故事开始'
        for section in sections:
            match=re.fullmatch(r'<h[23] id="([^"]+)">(.*?)</h[23]>',section,flags=re.S)
            if match: anchor=match[1]; heading=html.unescape(re.sub('<[^>]+>','',match[2])); continue
            text=html.unescape(re.sub('<[^>]+>',' ',section))
            if text.strip(): search.append({'chapter':n,'title':item['title'],'section':heading,'url':f'chapter-{n:02}.html'+('#'+anchor if anchor else ''),'text':re.sub(r'\s+',' ',text)})
    cards=''.join(f'<a class="card" href="chapter-{c["number"]:02}.html"><span class="number">{c["number"]:02}</span><div><h3>{html.escape(c["title"])}</h3><p>{c["topics"]}</p><small>约 {c["minutes"]} 分钟 <span data-chapter-progress="{c["number"]}"></span></small></div><span class="arrow">↗</span></a>' for c in metadata)
    home=f'''<main class="home" id="main"><section class="hero"><p class="eyebrow">一本写给工程实践者的 AGENT 技术小说</p><h1>让每一次修复，<br>都经得起<span>审判。</span></h1><p class="intro">一条仓库 URL，一份 Bug 描述。<br>跟随林川与陈工，走过检索、复现、补丁、验证与云端调度，理解 Coding Agent 背后的工程。</p><a class="start" href="chapter-01.html">从第一章开始阅读 <span>→</span></a><a class="resume" id="resume" hidden href="chapter-01.html">继续阅读 →</a><div class="book-mark" aria-hidden="true">Agent<span>帝 国</span><small>证据 · 补丁 · 验证</small></div><p class="hero-note">第一卷完 · 九章正文 · 七个本地实验 · 二十七道练习</p></section><nav class="home-links" aria-label="阅读工具"><a href="practice.html">交互实验室 ↗</a><a href="reading.html">我的阅读与书签 ↗</a><a href="editorial.html">内容说明与技术来源 ↗</a></nav><section class="catalog"><div class="section-title"><h2>全书导航</h2><span>9 章 · 按顺序阅读，也可自由探索</span></div><div class="cards">{cards}</div></section></main>'''
    (OUT/'index.html').write_text(page('全书导航',home),encoding='utf-8')
    practice='<main id="main" class="standalone"><p class="eyebrow">ENGINEERING LABS</p><h1>交互实验室</h1><p class="intro">把抽象的工程取舍，变成可以观察的结果。实验不连接模型、不执行仓库代码。</p><nav class="lab-index">'+''.join(f'<a href="#{name}">{title}</a>' for name,title,_ in LABS)+'</nav>'+''.join(f'<div id="{name}">{lab_html(name)}</div>' for name,_,_ in LABS)+'</main>'
    (OUT/'practice.html').write_text(page('交互实验室',practice),encoding='utf-8')
    reading='''<main id="main" class="standalone"><p class="eyebrow">YOUR READING DESK</p><h1>我的阅读</h1><p>进度、书签和练习结果保存在当前浏览器，不会跨设备同步。</p><section class="reading-section"><h2>阅读进度</h2><div id="reading-progress"></div></section><section class="reading-section"><h2>我的书签</h2><div id="bookmarks"></div></section><section class="reading-section"><h2>练习记录</h2><div id="quiz-records"></div></section><details class="clear-records"><summary>管理本地记录</summary><p>清除后无法恢复。字号与主题设置会保留。</p><button id="clear-records" type="button">清除全部阅读记录</button><div id="clear-confirm" hidden><p>确认清除当前浏览器内本书的进度、书签与练习记录？</p><button id="clear-yes" type="button">确认清除</button><button id="clear-no" type="button">取消</button></div></details></main>'''
    (OUT/'reading.html').write_text(page('我的阅读',reading),encoding='utf-8')
    editorial,_=render((ROOT/'EDITORIAL.md').read_text(encoding='utf-8'))
    (OUT/'editorial.html').write_text(page('内容说明与来源','<main id="main" class="standalone"><article>'+editorial+'</article></main>'),encoding='utf-8')
    (OUT/'search.json').write_text(json.dumps(search,ensure_ascii=False),encoding='utf-8')
    (OUT/'chapters.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'syntax.css').write_text(HtmlFormatter(style='monokai').get_style_defs('.codehilite'),encoding='utf-8')
    for path in (ROOT/'assets').iterdir():
        if path.is_file(): shutil.copyfile(path,OUT/path.name)
    (OUT/'.nojekyll').touch()
    print(f'Built {len(metadata)} chapters, {len(search)} search sections, seven labs and 27 exercises.')

if __name__=='__main__': main()
