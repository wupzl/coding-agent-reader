"""Publish using existing Git Credential Manager access; credentials stay in memory."""
from pathlib import Path
import argparse,json,os,subprocess,urllib.request,urllib.error

ROOT=Path(__file__).resolve().parents[1]
OWNER='wupzl'
SLUG='coding-agent-reader'
READERS=['pytorch-apprentice','ai-era-reader','data-empire-reader','rag-empire-reader','system-design-reader','online-troubleshooting-reader','bookshelf']

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['publish-new','publish-navigation','status'])
    args=parser.parse_args()
    env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'}
    credential=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,env=env,check=True)
    fields=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    token=fields.get('password')
    if not token:raise SystemExit('No existing GitHub credential available')
    def api(path,data=None,method=None):
        req=urllib.request.Request('https://api.github.com/'+path,data=json.dumps(data).encode('utf-8') if data is not None else None,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'coding-agent-reader-publisher'})
        try:
            with urllib.request.urlopen(req,timeout=40) as response:
                raw=response.read();return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code==404:return None
            raise RuntimeError(f'GitHub API {method or "GET"} {path}: HTTP {e.code}') from None
    def git(repo,*commands,capture=False):
        return subprocess.run(['git',*commands],cwd=repo,env=env,text=True,encoding='utf-8',capture_output=capture,check=True)
    user=api('user')
    if user['login']!=OWNER:raise SystemExit('Authenticated account does not match intended repository owner')
    if args.action=='publish-new':
        repo=api(f'repos/{OWNER}/{SLUG}')
        if repo is None:
            repo=api('user/repos',{'name':SLUG,'private':False,'description':'Agent 帝国：代码审判者 · 九章小说式 Coding Agent 工程阅读、七个本地实验与二十七道练习','homepage':f'https://{OWNER}.github.io/{SLUG}/'})
            print('Created public repository: '+repo['html_url'],flush=True)
        if repo['private']:raise SystemExit('Existing repository is private; refusing to publish into an unexpected repository')
        if not (ROOT/'.git').exists():
            branches=api(f'repos/{OWNER}/{SLUG}/branches')
            if branches:raise SystemExit('Remote repository already has commits; inspect before attaching this checkout')
            git(ROOT,'init','-b','main');git(ROOT,'remote','add','origin',f'https://github.com/{OWNER}/{SLUG}.git')
        origin=git(ROOT,'remote','get-url','origin',capture=True).stdout.strip()
        if origin!=f'https://github.com/{OWNER}/{SLUG}.git':raise SystemExit('Unexpected origin')
        git(ROOT,'add','--all')
        changed=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode
        if changed:git(ROOT,'commit','-m','Build Agent Empire reader with local labs and reading tools')
        git(ROOT,'push','-u','origin','main')
        pages=api(f'repos/{OWNER}/{SLUG}/pages')
        if pages is None:pages=api(f'repos/{OWNER}/{SLUG}/pages',{'source':{'branch':'main','path':'/docs'}},'POST')
        print('Pages configured: '+pages['html_url'],flush=True)
    elif args.action=='publish-navigation':
        for name in READERS:
            path=ROOT.parent/name
            expected='wupzl.github.io' if name=='bookshelf' else name
            origin=git(path,'remote','get-url','origin',capture=True).stdout.strip()
            if origin!=f'https://github.com/{OWNER}/{expected}.git':raise SystemExit('Unexpected origin for '+name)
            git(path,'fetch','origin','--quiet')
            behind=git(path,'rev-list','--count','HEAD..@{u}',capture=True).stdout.strip()
            if behind!='0':raise SystemExit(name+' has upstream changes; inspect before publishing')
            git(path,'add','--all')
            changed=subprocess.run(['git','diff','--cached','--quiet'],cwd=path).returncode
            if changed:git(path,'commit','-m','Connect Agent Empire reader to the shared learning bookshelf')
            git(path,'push')
            print('Published navigation: '+expected,flush=True)
    else:
        for name in [SLUG,*[('wupzl.github.io' if r=='bookshelf' else r) for r in READERS]]:
            pages=api(f'repos/{OWNER}/{name}/pages') or {}
            builds=api(f'repos/{OWNER}/{name}/pages/builds/latest') or {}
            runs=api(f'repos/{OWNER}/{name}/actions/runs?per_page=3') or {}
            print(json.dumps({'repository':name,'pages_status':pages.get('status'),'url':pages.get('html_url'),'source':pages.get('source'),'latest_build':builds.get('status'),'build_commit':builds.get('commit'),'runs':[{'id':r['id'],'name':r['name'],'status':r['status'],'conclusion':r['conclusion'],'url':r['html_url']} for r in runs.get('workflow_runs',[])]},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
