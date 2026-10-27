"""Import the supplied manuscript once, keeping the source and editing log."""
from pathlib import Path
import json, re, shutil

ROOT = Path(__file__).resolve().parents[1]
TITLES = ['一条 URL 引发的代码战争', '智能体的大脑——Agent Loop 与工具调用', '百万行代码迷宫——Agent 如何找到真正的 Bug？', 'Bug 审判庭——如何证明一个 Bug 真的存在？', '代码外科医生——AI 如何安全地修改百万行代码？', '云端战争——一千个 Coding Agent 同时觉醒', '安全与失控——当 Agent 获得执行权限', '评测法庭——如何证明 Coding Agent 真的变聪明了？', '终极面试——从实习项目到真正的工程体系']
TOPICS = ['整体架构 · 异步任务 · 从证据到补丁', 'ReAct · 工具调用 · 状态机与上下文', '关键词 · AST / LSP · Code RAG', '最小复现 · JUnit · 独立验证', 'Git Diff · 幂等性 · 最小变更', '消息队列 · Worker · 限流与可观测性', '提示注入 · 沙箱 · 权限与审计', 'SWE-bench · Pass@K · 配对评测', '工程取舍 · 实习复盘 · 面试表达']
NOTES = {
1: ('证据优先的修复链路', '本章的接口、订单代码和运行报告是教学示例，不能直接作为生产实现或真实项目成绩。数据库唯一约束应匹配业务幂等域；重复键异常的恢复读取需要在失败事务结束后执行。'),
2: ('把模型输出视为行动提议', '模型提出工具调用，由 Runtime 校验名称、参数和授权后执行。示例中的循环应配合时间、Token 和工具次数预算；文本中的推理步骤是教学化决策摘要，并不意味着需要展示模型内部推理。'),
3: ('检索结果还不是根因', '关键词、AST、LSP、调用图与向量检索提供不同线索。调用关系可能受反射、动态分派和跨服务通信影响；必须结合运行证据验证候选根因。'),
4: ('测试证据有适用范围', '一次复现失败不能证明缺陷不存在；Mock 测试不能替代真实数据库和事务验证。修复前失败、修复后通过的同一用例应由独立验证流程保存和重跑。'),
5: ('最小补丁与明确事务边界', '本章 Java、SQL 和 Patch Guard 代码展示设计思路。真实实现还要检查路径穿越和符号链接、旧数据迁移、同请求 ID 的参数冲突、事务提交后的可见性及补偿策略。'),
6: ('并发受最紧张的资源约束', 'Java 21 虚拟线程适合大量等待 I/O 的任务，并不会增加数据库连接、模型配额或 CPU。Sandbox 资源应独立计费与限额；本章监控数字均为故事中的假设数据。'),
7: ('容器配置只是多层防线之一', '仓库文档、构建脚本和工具返回都可能包含不可信输入。Pod Security 的 Restricted 配置可收紧权限，但不能单独证明可安全执行任意恶意代码；还要考虑网络、凭证、内核隔离与审计。'),
8: ('评测结论必须附带实验条件', 'SWE-bench 通过代码库、问题和补丁评估软件问题解决能力。Pass@K 应说明采样和预算；同一任务集比较应保留逐题配对结果，并同时报告样本量、成本和不确定性。'),
9: ('分清故事示例与个人经历', '林川的叙事与本书的代码属于教学案例。面试表达应以自己的真实职责、代码、证据和可核实指标为准；第二卷在本项目中仅保留原文预告。'),
}

def language(code):
    s=code.strip()
    if re.search(r'^(@\w+|public |private |import java|class |interface |record |while \(|for \(|try \{)',s,re.M): return 'java'
    if s.startswith(('{','[')):
        try: json.loads(s); return 'json'
        except ValueError: pass
    if re.search(r'^(ALTER TABLE|CREATE (TABLE|UNIQUE|INDEX)|SELECT |INSERT |UPDATE )',s,re.M|re.I): return 'sql'
    if re.search(r'^(apiVersion:|kind:|spec:)',s,re.M): return 'yaml'
    if re.search(r'^(git |mvn |rg |curl |docker |kubectl |java |npm )',s,re.M): return 'bash'
    if s.startswith(('<project','<dependency','<?xml')): return 'xml'
    if s.startswith(('diff --git','--- a/','@@ ')): return 'diff'
    return 'text'

def main():
    source=ROOT.parent/'codingagent.md'
    (ROOT/'source').mkdir(exist_ok=True)
    shutil.copyfile(source,ROOT/'source'/'codingagent.original.md')
    raw=source.read_text(encoding='utf-8-sig')
    starts=[raw.index('## 第一章：')]
    for numeral in ['二','三','四','五','六']:
        starts.append(raw.index(f'## 第{numeral}章：'))
    starts.append(raw.index('# 第一幕：藏在 README 里的命令'))
    for numeral in ['八','九']: starts.append(raw.index(f'## 第{numeral}章：'))
    (ROOT/'chapters').mkdir(exist_ok=True)
    report=[]; metadata=[]
    for i,start in enumerate(starts):
        n=i+1
        chunk=raw[start:starts[i+1] if i+1<len(starts) else len(raw)]
        chunk=re.sub(r'\n# 《Agent 帝国：代码审判者》\s*$', '',chunk)
        chunk=re.sub(r'\n下一章。\s*$', '',chunk)
        if n==1:
            chunk=chunk[:chunk.index('## 《Agent 帝国》后续章节路线')]
        # The seventh chapter lacks its own title in the manuscript.
        if n==7: chunk='## 第七章：'+TITLES[i]+'\n\n'+chunk
        lines=chunk.splitlines(); out=[]; fenced=False; code=[]; code_lang=''; removed=[]
        for index,line in enumerate(lines):
            if line.strip().startswith('```'):
                if not fenced:
                    fenced=True; code=[]; code_lang=line.strip()[3:]
                else:
                    out+=['```'+(code_lang or language('\n'.join(code))),*code,'```']; fenced=False
                continue
            if fenced: code.append(line); continue
            if re.fullmatch(r'[0-9:./%]{22,}',line.strip()):
                removed.append(line.strip()); out.append('（原文图表刻度已省略；请结合相邻文字理解示意数据。）'); continue
            line=re.sub(r'\?utm_source=chatgpt\.com','',line)
            line=line.replace('Pass\\@','Pass@').replace('pass\\@','pass@')
            if re.match(r'^#{1,2} ',line):
                text=line.lstrip('# ').strip()
                if index==0: line='# '+text
                elif re.match(r'(第[一二三四五六七八九十百]+幕[：:]|终章[：:]|尾声[：:]|《Agent 帝国》第一卷完结|第二卷预告|本章知识|第[一二三四五六七八九]章知识)',text): line='## '+text
                elif text.startswith('下一章'): line='### '+text
                else: line='### '+text
            out.append(line)
        assert not fenced, f'Unclosed code fence chapter {n}'
        text='\n'.join(out).strip()+'\n'
        # Repair over-escaped display delimiters; preserve commands inside the formula.
        text=re.sub(r'\\{2,}([\[\]()])',lambda m:'\\'+m[1],text)
        text=re.sub(r'\\([_{}])',r'\1',text)
        note_title,note=NOTES[n]
        first,rest=text.split('\n',1)
        text=first+'\n\n> 阅读提示：'+note+'\n'+rest
        (ROOT/'chapters'/f'{n:02}.md').write_text(text,encoding='utf-8')
        metadata.append({'number':n,'title':TITLES[i],'topics':TOPICS[i],'note_title':note_title,'note':note})
        report.append({'chapter':n,'characters':len(text),'code_blocks':text.count('```')//2,'removed_chart_artifacts':removed})
    (ROOT/'book.json').write_text(json.dumps({'title':'Agent 帝国：代码审判者','status':'第一卷完','chapters':metadata},ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'CONTENT_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
