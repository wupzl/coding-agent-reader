"""Verify real browser behavior through an offline HTTPS route, without a server."""
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
from html.parser import HTMLParser
import json,mimetypes
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parent
DOCS=ROOT/'docs'
OUT=ROOT/'test-results'
BASE='https://reader.test/coding-agent-reader/'

class Links(HTMLParser):
    def __init__(self,path):
        super().__init__();self.links=[];self.ids=[];self.feed(path.read_text(encoding='utf-8'))
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag in ('a','script','link','img'):
            value=attrs.get('href') or attrs.get('src')
            if value:self.links.append(value)

def main():
    OUT.mkdir(exist_ok=True)
    files=sorted(DOCS.glob('*.html'));parsed={path:Links(path) for path in files}
    assert len(files)==13
    for path,data in parsed.items():
        assert len(data.ids)==len(set(data.ids)),('duplicate IDs',path)
        assert 'katex-error' not in path.read_text(encoding='utf-8')
        for value in data.links:
            url=urlsplit(urljoin(BASE+path.name,value))
            if url.netloc!='reader.test' or not url.path.startswith('/coding-agent-reader/'):continue
            target=DOCS/unquote(url.path.removeprefix('/coding-agent-reader/'))
            if target.is_dir():target=target/'index.html'
            assert target.is_file(),(path.name,value)
            if url.fragment and target.suffix=='.html':assert unquote(url.fragment) in parsed[target].ids,(path.name,value)
    bank=json.loads((DOCS/'questions.json').read_text(encoding='utf-8'))
    assert len(bank)==9 and sum(map(len,bank.values()))==27
    errors=[];missing=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        context=browser.new_context(viewport={'width':1440,'height':1000},permissions=['clipboard-read','clipboard-write'])
        def serve(route):
            url=urlsplit(route.request.url)
            if url.netloc!='reader.test':route.abort();return
            if not url.path.startswith('/coding-agent-reader/'):route.fulfill(status=200,body='<!doctype html><title>Sibling reader</title>');return
            relative=unquote(url.path.removeprefix('/coding-agent-reader/')) or 'index.html'
            path=DOCS/relative
            if path.is_file():route.fulfill(path=str(path),content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream')
            else:missing.append(url.path);route.fulfill(status=404,body='Missing file')
        context.route('**/*',serve)
        page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
        for width in (390,768,1440):
            page.set_viewport_size({'width':width,'height':1000})
            for path in files:
                page.goto(BASE+path.name)
                if path.name.startswith('chapter-'):expect(page.locator('.quiz fieldset')).to_have_count(3)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('overflow',width,path.name)
                expect(page.locator('.shelf-menu a')).to_have_count(7)
                page.locator('.shelf-switch summary').click();box=page.locator('.shelf-menu').bounding_box()
                assert box and box['x']>=0 and box['x']+box['width']<=width,(width,path.name,box)
                page.locator('.shelf-switch summary').click()
                if path.name in ('index.html','chapter-01.html','practice.html'):
                    page.screenshot(path=str(OUT/f'{path.stem}-{width}.png'),full_page=path.name=='index.html')
            print(f'PASS: 13 pages at {width}px',flush=True)
        page.goto(BASE+'index.html');seen=set()
        for _ in range(3):
            page.locator('#theme').click();theme=page.locator('html').get_attribute('data-theme');seen.add(theme);page.reload();assert page.locator('html').get_attribute('data-theme')==theme
        assert seen=={'white','light','dark'}
        page.goto(BASE+'chapter-01.html');expect(page.locator('.quiz fieldset')).to_have_count(3)
        page.locator('#larger').click();size=page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--reading-size")');page.reload();assert page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--reading-size")')==size
        page.locator('#search-open').click();page.locator('#query').fill('SSRF');result=page.locator('.search-result[href^="chapter-07.html#"]').first;expect(result).to_be_visible();result.click();assert 'chapter-07.html#' in page.url
        page.locator('#search-open').click();page.locator('#query').fill('this-keyword-does-not-exist-4920');expect(page.locator('#search-status')).to_contain_text('未找到');page.keyboard.press('Escape');expect(page.locator('#search-dialog')).not_to_be_visible()
        page.goto(BASE+'chapter-01.html');expect(page.locator('.quiz fieldset')).to_have_count(3)
        page.evaluate('scrollTo(0,(document.documentElement.scrollHeight-innerHeight)*.34)')
        page.wait_for_function('JSON.parse(localStorage.getItem("coding-agent-reading"))?.progress?.[1]?.percent>=33')
        page.locator('#bookmark').click();expect(page.locator('#bookmark')).to_have_attribute('aria-pressed','true')
        page.goto(BASE+'reading.html');expect(page.locator('#bookmarks .reading-item')).to_have_count(1)
        page.locator('#bookmarks a').click();page.wait_for_function('scrollY/(document.documentElement.scrollHeight-innerHeight)>.30')
        fraction=page.evaluate('scrollY/(document.documentElement.scrollHeight-innerHeight)');assert abs(fraction-.34)<.03,fraction
        page.goto(BASE+'index.html');page.locator('#resume').click();page.wait_for_function('scrollY/(document.documentElement.scrollHeight-innerHeight)>.30')
        page.goto(BASE+'chapter-01.html');expect(page.locator('.quiz fieldset')).to_have_count(3)
        page.locator('.copy-code').first.click();copied=page.evaluate('navigator.clipboard.readText()');assert 'repositoryUrl' in copied
        for n,items in bank.items():
            page.goto(BASE+f'chapter-{int(n):02}.html');expect(page.locator('.quiz fieldset')).to_have_count(3)
            page.locator('.quiz-submit').click();expect(page.locator('.quiz-status')).to_contain_text('完成全部')
            for i,item in enumerate(items):page.locator(f'input[name="q{i}"][value="{item["answer"]}"]').check()
            page.locator('.quiz-submit').click();expect(page.locator('.quiz-status')).to_contain_text('3 / 3')
            page.reload();expect(page.locator('.quiz-status')).to_contain_text('3 / 3')
        page.goto(BASE+'practice.html')
        lab=page.locator('[data-lab="loop"]')
        for _ in range(6):lab.locator('.next').click()
        expect(lab.locator('.state')).to_have_text('READY_FOR_REVIEW');expect(lab.locator('.next')).to_be_disabled()
        lab.locator('.scenario').select_option('blocked')
        for _ in range(3):lab.locator('.next').click()
        expect(lab.locator('.state')).to_have_text('BLOCKED')
        lab.locator('.scenario').select_option('fixed');lab.locator('.budget').select_option('3')
        for _ in range(4):lab.locator('.next').click()
        expect(lab.locator('.state')).to_have_text('BUDGET_EXCEEDED')
        lab.locator('.scenario').select_option('budget');lab.locator('.budget').select_option('8')
        for _ in range(5):lab.locator('.next').click()
        expect(lab.locator('.state')).to_have_text('REVIEW_REQUIRED')
        lab=page.locator('[data-lab="retrieval"]');expect(lab.locator('.lab-output')).to_contain_text('0 个候选');lab.locator('.mode').select_option('expanded');expect(lab.locator('.lab-output')).to_contain_text('PaymentRetry.java')
        lab=page.locator('[data-lab="verify"]');expect(lab.locator('.lab-output')).to_contain_text('REPRODUCED')
        for evidence,status in [('none','INSUFFICIENT_EVIDENCE'),('blocked','BLOCKED'),('clean','NOT_REPRODUCED')]:lab.locator('.evidence').select_option(evidence);expect(lab.locator('.lab-output')).to_contain_text(status)
        lab.locator('.rule').select_option('unknown');expect(lab.locator('.lab-output')).to_contain_text('NEEDS_CLARIFICATION')
        lab=page.locator('[data-lab="patch"]')
        for strategy,count in [('none',2),('jvm',2),('database',1)]:lab.locator('.strategy').select_option(strategy);lab.locator('.run').click();expect(lab.locator('.lab-output')).to_contain_text(f'订单数：{count}')
        lab=page.locator('[data-lab="queue"]');expect(lab.locator('.backlog')).to_have_text('48');lab.locator('.workers').fill('30');expect(lab.locator('.capacity')).to_have_text('30');expect(lab.locator('.queue-reason')).to_contain_text('模型配额');lab.locator('.quota').fill('120');expect(lab.locator('.backlog')).to_have_text('0')
        lab=page.locator('[data-lab="guard"]')
        for request,status in [('read','ALLOW'),('escape','DENY'),('link','DENY'),('network','DENY'),('credential','DENY'),('build','SANDBOX_REQUIRED'),('inject','UNTRUSTED_CONTENT')]:lab.locator('select').select_option(request);expect(lab.locator('.lab-output strong')).to_have_text(status)
        lab=page.locator('[data-lab="eval"]');expect(lab.locator('.at-least')).to_have_text('78.4%');lab.locator('.probability').fill('0');expect(lab.locator('.at-least')).to_have_text('0.0%');lab.locator('.probability').fill('100');expect(lab.locator('.at-least')).to_have_text('100.0%');lab.locator('.attempts').fill('1');expect(lab.locator('.cost')).to_have_text('1×')
        page.goto(BASE+'reading.html');expect(page.locator('#quiz-records .reading-item')).to_have_count(9)
        page.locator('#bookmarks button').click();expect(page.locator('#bookmarks .reading-item')).to_have_count(0)
        page.locator('.clear-records summary').click();page.locator('#clear-records').click();page.locator('#clear-no').click();expect(page.locator('#clear-confirm')).not_to_be_visible();expect(page.locator('#quiz-records .reading-item')).to_have_count(9)
        page.locator('#clear-records').click();page.locator('#clear-yes').click();page.reload();expect(page.locator('#quiz-records .reading-item')).to_have_count(0)
        assert not errors,errors
        assert not missing,missing
        browser.close()
    print('PASS: links and anchors, local resources, themes, size, search, progress/resume, bookmarks, clipboard, all 27 questions and seven interactive labs; no JS errors.')

if __name__=='__main__':main()
