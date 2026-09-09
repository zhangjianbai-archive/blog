(() => {
  const version=document.querySelector('meta[name="site-version"]')?.content;
  const base='/blog/articles/', results=document.querySelector('#results'), field=document.querySelector('#search');
  const keys=['q','category','topic','tag','author','readable'];
  const normalize=t=>t.normalize('NFKC').toLocaleLowerCase().trim();
  let saved; try { saved=JSON.parse(sessionStorage.getItem('article-return')); } catch {}
  if (!results) {
    if(saved && saved.article===location.pathname) {
      const u=new URL(saved.url,location.origin);
      if(u.origin===location.origin && u.pathname===base) document.querySelectorAll('.back-results').forEach(a=>{
        a.href=u.href;a.textContent='返回筛选结果';a.addEventListener('click',()=>{try{sessionStorage.setItem('restore-results','1');}catch{}});
      });
    }
    return;
  }
  const rows=[...results.querySelectorAll('.catalog-entry')], readable=document.querySelector('#readable-only'), clear=document.querySelector('#clear-search'), chips=document.querySelector('#active-filters');
  const prev=document.querySelector('#prev-page'),next=document.querySelector('#next-page'),size=20;
  let state=new URLSearchParams(location.search);
  if(location.hash&&!state.has('category'))state.set('category',location.hash.slice(1));
  if(state.get('topic')){const r=rows.find(r=>r.dataset.topic===state.get('topic'));if(r)state.set('category',r.dataset.category);}
  const labels={q:'搜索',category:'议题',topic:'专题',tag:'合集',author:'作者',readable:'只看已上架'};
  function label(k,v){return [...document.querySelectorAll(`[data-select="${k}"] option`)].find(o=>o.value===v)?.textContent||[...document.querySelectorAll(`[data-filter="${k}"]`)].find(a=>a.dataset.value===v)?.textContent||v;}
  function render(mode){
    if(version)state.set("v",version);
    const terms=normalize(state.get('q')||'').split(/\s+/).filter(Boolean);
    const matched=rows.filter(r=>terms.every(t=>normalize(r.dataset.search).includes(t))&&(!state.get('readable')||r.dataset.readable==='true')&&['category','topic','author'].every(k=>!state.get(k)||r.dataset[k]===state.get(k))&&(!state.get('tag')||r.dataset.tag.split(' ').includes(state.get('tag'))));
    const pages=Math.max(1,Math.ceil(matched.length/size)),page=Math.max(1,Math.min(pages,parseInt(state.get('page'),10)||1));
    if(page>1)state.set('page',String(page));else state.delete('page');
    const shown=new Set(matched.slice((page-1)*size,page*size));rows.forEach(r=>r.hidden=!shown.has(r));
    field.value=state.get('q')||'';readable.checked=state.get('readable')==='1';
    document.querySelectorAll('[data-select]').forEach(s=>s.value=state.get(s.dataset.select)||'');
    document.querySelectorAll('[data-filter]').forEach(a=>{if((state.get(a.dataset.filter)||'')===a.dataset.value)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');});
    chips.replaceChildren();keys.filter(k=>state.get(k)).forEach(k=>{const b=document.createElement('button'),t=k==='readable'?labels[k]:`${labels[k]}：${label(k,state.get(k))}`;b.textContent=t+' ×';b.setAttribute('aria-label','取消'+t);b.addEventListener('click',()=>change(k,''));chips.append(b);});
    clear.hidden=!keys.some(k=>state.get(k));document.querySelector('#result-count').textContent=`${matched.length} 个标题 · ${matched.filter(r=>r.dataset.readable==='true').length} 篇可阅读全文`;
    document.querySelector('#empty').hidden=matched.length!==0;document.querySelector('#page-count').textContent=`${page} / ${pages}`;
    for(const [el,n,disabled] of [[prev,page-1,page===1],[next,page+1,page===pages]]){
      el.setAttribute('aria-disabled',String(disabled));
      if(disabled){el.removeAttribute('href');}else{const params=new URLSearchParams(state);params.set('page',String(n));el.href=keys.some(k=>state.get(k))?base+'?'+params:(n===1?base:base+'page/'+n+'/');}
    }
    document.querySelector('.pagination').hidden=pages===1;
    if(mode){const u=new URL(base,location.origin);u.search=state.toString();history[mode](null,'',u);}
  }
  function change(k,v,mode='pushState'){
    if(v)state.set(k,v);else state.delete(k);
    if(k==='category')state.delete('topic');
    if(k==='topic'&&v){const r=rows.find(r=>r.dataset.topic===v);if(r)state.set('category',r.dataset.category);}
    if(k!=='page')state.delete('page');render(mode);
  }
  document.addEventListener('click',event=>{
    const a=event.target.closest('a');if(!a||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
    if(a.dataset.filter){event.preventDefault();change(a.dataset.filter,a.dataset.value);document.querySelector('.page-title').scrollIntoView({block:'start'});return;}
    const u=new URL(a.href);if(u.origin===location.origin&&u.pathname.startsWith(base)&&u.pathname!==base){try{sessionStorage.setItem('article-return',JSON.stringify({url:location.href,scroll:scrollY,article:u.pathname}));}catch{}}
  });
  document.querySelectorAll('[data-select]').forEach(s=>s.addEventListener('change',()=>change(s.dataset.select,s.value)));
  field.addEventListener('input',()=>change('q',field.value,'replaceState'));
  document.querySelector('#search-form').addEventListener('submit',e=>{e.preventDefault();change('q',field.value,'replaceState');});
  readable.addEventListener('change',()=>change('readable',readable.checked?'1':''));
  clear.addEventListener('click',()=>{state=new URLSearchParams();render('pushState');});
  for(const [el,delta] of [[prev,-1],[next,1]])el.addEventListener('click',e=>{if(e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();if(el.getAttribute('aria-disabled')==='true')return;change('page',String((Number(state.get('page'))||1)+delta));document.querySelector('.page-title').scrollIntoView();});
  addEventListener('popstate',()=>{state=new URLSearchParams(location.search);render();});render('replaceState');
  try{if(sessionStorage.getItem('restore-results')==='1'){sessionStorage.removeItem('restore-results');if(saved&&new URL(saved.url).href===location.href)requestAnimationFrame(()=>scrollTo({top:saved.scroll,behavior:'instant'}));}}catch{}
})();
