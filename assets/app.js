(() => {
  'use strict';
  const root=document.documentElement, prefix='coding-agent-', chapter=Number(document.body.dataset.chapter)||0;
  const read=(key,fallback)=>{try {const value=localStorage.getItem(prefix+key);return value===null?fallback:JSON.parse(value)} catch {return fallback}};
  let storageFailed=false;
  const write=(key,value)=>{try{localStorage.setItem(prefix+key,JSON.stringify(value));return true}catch{if(!storageFailed){storageFailed=true;toast('浏览器未允许本地存储，本次记录无法保存。')}return false}};
  let state=read('reading',null);
  if(!state||typeof state!=='object'||state.version!==1) state={version:1,progress:{},bookmarks:[],quiz:{},last:0};
  state.progress=state.progress&&typeof state.progress==='object'?state.progress:{};
  state.bookmarks=Array.isArray(state.bookmarks)?state.bookmarks:[];
  state.quiz=state.quiz&&typeof state.quiz==='object'?state.quiz:{};
  const persist=()=>write('reading',state);
  function element(tag,text,className){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(className)e.className=className;return e}
  let toastTimer;
  function toast(message){const e=document.querySelector('#toast');e.textContent=message;e.classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>e.classList.remove('visible'),3000)}
  const themes=['white','light','dark'],themeNames={white:'纯白',light:'米白',dark:'深色'};
  function setTheme(value){const theme=themes.includes(value)?value:'white';root.dataset.theme=theme;const button=document.querySelector('#theme');button.textContent=themeNames[theme];button.setAttribute('aria-label','切换背景，当前'+themeNames[theme]);try{localStorage.setItem(prefix+'theme',theme)}catch{}}
  setTheme(root.dataset.theme);
  document.querySelector('#theme').addEventListener('click',()=>setTheme(themes[(themes.indexOf(root.dataset.theme)+1)%3]));
  let size=18;try{size=Math.min(26,Math.max(16,Number(localStorage.getItem(prefix+'size'))||18))}catch{}
  function resize(delta){size=Math.min(26,Math.max(16,size+delta));root.style.setProperty('--reading-size',size+'px');try{localStorage.setItem(prefix+'size',String(size))}catch{}document.querySelector('#smaller').disabled=size<=16;document.querySelector('#larger').disabled=size>=26}
  document.querySelector('#smaller').addEventListener('click',()=>resize(-1));
  document.querySelector('#larger').addEventListener('click',()=>resize(1));resize(0);

  const dialog=document.querySelector('#search-dialog'),query=document.querySelector('#query'),results=document.querySelector('#search-results'),status=document.querySelector('#search-status');
  let indexPromise=null,searchTimer,searchVersion=0;
  const loadIndex=()=>indexPromise||(indexPromise=fetch('search.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).catch(e=>{indexPromise=null;throw e}));
  function highlight(parent,text,word){const at=text.toLocaleLowerCase().indexOf(word.toLocaleLowerCase());if(at<0){parent.textContent=text;return}parent.append(document.createTextNode(text.slice(0,at)),element('mark',text.slice(at,at+word.length)),document.createTextNode(text.slice(at+word.length)))}
  async function search(){const version=++searchVersion;results.replaceChildren();const words=query.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);if(!words.length){status.textContent='输入关键词开始搜索';return}status.textContent='正在搜索…';try{const data=await loadIndex();if(version!==searchVersion)return;const found=data.map(item=>({...item,haystack:(item.title+' '+item.section+' '+item.text).toLocaleLowerCase()})).filter(item=>words.every(word=>item.haystack.includes(word))).sort((a,b)=>Number(words.some(word=>b.section.toLocaleLowerCase().includes(word)))-Number(words.some(word=>a.section.toLocaleLowerCase().includes(word))));status.textContent=found.length?`找到 ${found.length} 个段落${found.length>40?'，显示前 40 个':''}`:'未找到匹配内容，试试更短的关键词。';for(const item of found.slice(0,40)){const link=element('a',undefined,'search-result');link.href=item.url;const title=element('strong');highlight(title,`第${item.chapter}章 · ${item.section}`,words[0]);const at=Math.max(0,item.text.toLocaleLowerCase().indexOf(words[0])-55),snippet=element('p');highlight(snippet,(at?'…':'')+item.text.slice(at,at+180)+'…',words[0]);link.append(title,snippet);results.append(link)}}catch{if(version===searchVersion)status.textContent='搜索索引加载失败，请检查连接后重新输入。'}}
  document.querySelector('#search-open').addEventListener('click',()=>{dialog.showModal();query.focus()});
  document.querySelector('#search-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close()}});
  query.addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(search,120)});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&dialog.open){event.preventDefault();dialog.close();return}if(event.key==='/'&&!/INPUT|TEXTAREA|SELECT/.test(event.target.tagName)&&!event.ctrlKey&&!event.metaKey){event.preventDefault();if(!dialog.open)dialog.showModal();query.focus()}});

  document.querySelectorAll('.copy-code').forEach(button=>button.addEventListener('click',async()=>{const text=button.closest('.code-block').querySelector('pre').textContent;try{if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(text);else{const area=element('textarea',text);area.style.position='fixed';area.style.opacity='0';document.body.append(area);area.select();const copied=document.execCommand('copy');area.remove();if(!copied)throw Error('copy unavailable')}toast('代码已复制')}catch{toast('复制未获浏览器允许，请选择代码后复制。')}}));
  const resume=document.querySelector('#resume');if(resume&&state.last>=1&&state.last<=9){resume.href=`chapter-${String(state.last).padStart(2,'0')}.html?resume=1`;resume.textContent=`继续阅读第 ${state.last} 章 →`;resume.hidden=false}
  document.querySelectorAll('[data-chapter-progress]').forEach(e=>{const p=state.progress[e.dataset.chapterProgress];if(p)e.textContent=p.maxPercent>=98?'· 已读完':`· 已读 ${p.maxPercent}%`});

  if(chapter){
    const bookmarkButton=document.querySelector('#bookmark'),readStatus=document.querySelector('#read-status');let saveTimer,ready=false;
    const headings=[...document.querySelectorAll('article h2[id],article h3[id]')];
    const fraction=()=>Math.max(0,Math.min(1,scrollY/Math.max(1,document.documentElement.scrollHeight-innerHeight)));
    function section(){let current=null;for(const h of headings){if(h.getBoundingClientRect().top<=innerHeight*.35)current=h;else break}return current}
    function bookmarkKey(){return `${chapter}:${section()?.id||'start'}`}
    function refreshBookmark(){const exists=state.bookmarks.some(b=>b.key===bookmarkKey());bookmarkButton.setAttribute('aria-pressed',String(exists));bookmarkButton.textContent=exists?'取消此处书签':'收藏当前位置'}
    function saveProgress(){if(!ready)return;const percent=Math.round(fraction()*100),old=state.progress[chapter];state.progress[chapter]={percent,maxPercent:Math.max(old?.maxPercent||0,percent),fraction:fraction(),updatedAt:Date.now()};state.last=chapter;persist()}
    function update(){const p=Math.round(fraction()*100);document.querySelector('#progress').style.width=p+'%';readStatus.textContent=`本章 ${p}%`;refreshBookmark();clearTimeout(saveTimer);saveTimer=setTimeout(saveProgress,250)}
    bookmarkButton.addEventListener('click',()=>{const key=bookmarkKey(),index=state.bookmarks.findIndex(b=>b.key===key);if(index>=0){state.bookmarks.splice(index,1);toast('已移除此处书签')}else{const h=section();state.bookmarks.push({key,id:Date.now().toString(36)+Math.random().toString(36).slice(2,7),chapter,label:h?.textContent||document.querySelector('h1').textContent,fraction:fraction(),createdAt:Date.now()});toast('已收藏当前位置')}persist();refreshBookmark()});
    const params=new URLSearchParams(location.search);requestAnimationFrame(()=>requestAnimationFrame(()=>{if(!location.hash){const id=params.get('bookmark'),saved=id?state.bookmarks.find(b=>b.id===id&&b.chapter===chapter):params.has('resume')?state.progress[chapter]:null;if(saved&&Number.isFinite(saved.fraction))scrollTo(0,saved.fraction*Math.max(0,document.documentElement.scrollHeight-innerHeight))}ready=true;state.last=chapter;update()}));
    window.addEventListener('scroll',update,{passive:true});window.addEventListener('resize',update);window.addEventListener('pagehide',saveProgress);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')saveProgress()});
  }

  if(document.querySelector('#reading-progress')){
    const bookmarks=document.querySelector('#bookmarks');
    const url=n=>`chapter-${String(n).padStart(2,'0')}.html`;
    function showReading(){const progress=document.querySelector('#reading-progress');progress.replaceChildren();let count=0;for(let n=1;n<=9;n++){const p=state.progress[n];if(!p)continue;count++;const row=element('div',undefined,'reading-item'),a=element('a',`第 ${n} 章 · ${p.maxPercent>=98?'已读完':'已读 '+p.maxPercent+'%'}`);a.href=url(n)+'?resume=1';row.append(a,element('span','继续上次位置 →'));progress.append(row)}if(!count)progress.append(element('p','还没有阅读记录，从第一章开始吧。'));bookmarks.replaceChildren();for(const b of [...state.bookmarks].reverse()){const row=element('div',undefined,'reading-item'),a=element('a',`第 ${b.chapter} 章 · ${b.label}`),remove=element('button','移除');a.href=url(b.chapter)+'?bookmark='+encodeURIComponent(b.id);remove.setAttribute('aria-label','移除书签：'+b.label);remove.addEventListener('click',()=>{state.bookmarks=state.bookmarks.filter(x=>x.id!==b.id);persist();showReading()});row.append(a,remove);bookmarks.append(row)}if(!state.bookmarks.length)bookmarks.append(element('p','还没有书签。阅读时点击“收藏当前位置”。'));const records=document.querySelector('#quiz-records');records.replaceChildren();for(const [n,record] of Object.entries(state.quiz)){const row=element('div',undefined,'reading-item'),a=element('a',`第 ${n} 章 · ${record.score} / 3 题`);a.href=url(Number(n))+'#quiz-'+n;row.append(a,element('span','查看作答与解析 →'));records.append(row)}if(!Object.keys(state.quiz).length)records.append(element('p','完成章末练习后，成绩会显示在这里。'))}
    document.querySelector('#clear-records').addEventListener('click',()=>document.querySelector('#clear-confirm').hidden=false);
    document.querySelector('#clear-no').addEventListener('click',()=>document.querySelector('#clear-confirm').hidden=true);
    document.querySelector('#clear-yes').addEventListener('click',()=>{state={version:1,progress:{},bookmarks:[],quiz:{},last:0};persist();showReading();document.querySelector('#clear-confirm').hidden=true;toast('阅读记录已清除')});showReading();
  }

  const quiz=document.querySelector('[data-quiz]');
  if(quiz){quiz.id='quiz-'+chapter;const body=quiz.querySelector('.quiz-body');fetch('questions.json').then(r=>{if(!r.ok)throw Error('load failed');return r.json()}).then(bank=>{const items=bank[String(chapter)];const form=element('form');const fields=[];items.forEach((item,i)=>{const field=element('fieldset'),legend=element('legend',`${i+1}. ${item.q}`);field.append(legend);item.options.forEach((text,j)=>{const label=element('label'),input=element('input');input.type='radio';input.name='q'+i;input.value=String(j);label.append(input,document.createTextNode(text));field.append(label)});const feedback=element('div',undefined,'quiz-feedback');feedback.hidden=true;field.append(feedback);fields.push(field);form.append(field)});const actions=element('div',undefined,'quiz-actions'),submit=element('button','提交答案','quiz-submit'),reset=element('button','重新作答'),message=element('p','','quiz-status');submit.type='submit';reset.type='button';message.setAttribute('role','status');actions.append(submit,reset,message);form.append(actions);body.append(form);
    function grade(answers,save){let score=0;items.forEach((item,i)=>{const correct=answers[i]===item.answer;if(correct)score++;const feedback=fields[i].querySelector('.quiz-feedback');feedback.hidden=false;feedback.textContent=(correct?'回答正确。':'回答有误。')+' 正确答案：'+item.options[item.answer]+'。'+item.explanation});message.textContent=`答对 ${score} / ${items.length} 题。${score===items.length?'你已经抓住本章要点。':'可以查看解析后重新作答。'}`;if(save){state.quiz[chapter]={answers,score,updatedAt:Date.now()};persist()}}
    form.addEventListener('submit',event=>{event.preventDefault();const answers=items.map((_,i)=>{const value=new FormData(form).get('q'+i);return value===null?null:Number(value)});if(answers.some(x=>x===null)){message.textContent='请完成全部三道题后再提交。';return}grade(answers,true)});
    reset.addEventListener('click',()=>{form.reset();fields.forEach(f=>f.querySelector('.quiz-feedback').hidden=true);message.textContent='';delete state.quiz[chapter];persist()});
    const saved=state.quiz[chapter];if(saved&&Array.isArray(saved.answers)&&saved.answers.length===items.length&&saved.answers.every(a=>Number.isInteger(a)&&a>=0&&a<3)){saved.answers.forEach((answer,i)=>{fields[i].querySelector(`input[value="${answer}"]`).checked=true});grade(saved.answers,false)}
    }).catch(()=>{body.textContent='练习加载失败，请刷新页面重试。'})}
})();
