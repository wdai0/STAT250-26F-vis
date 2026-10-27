const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
// Small DOM substitute for control logic; browser layout is checked separately.
const source=fs.readFileSync(0,'utf8');
let width=390;
class Element {
  constructor(tag='div'){this.tag=tag;this.attrs={};this.dataset=new Proxy({}, {set:(target,key,value)=>{target[key]=String(value);this.attrs['data-'+key]=String(value);return true;}});this.children=[];this.events={};this.hidden=false;this.disabled=false;this.textContent='';}
  setAttribute(key,value){this.attrs[key]=String(value);if(key.startsWith('data-'))this.dataset[key.slice(5)]=String(value);if(key==='hidden')this.hidden=true;if(key==='disabled')this.disabled=true;}
  getAttribute(key){return this.attrs[key];}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
  addEventListener(type,fn){this.events[type]=fn;}
  getBoundingClientRect(){return {width};}
  focus(){this.focused=true;}
  get innerHTML(){return this.markup||'';}
  set innerHTML(html){this.markup=html;this.children=parse(html).children;}
  querySelectorAll(selector){const match=node=>selector[0]==='#'?node.attrs.id===selector.slice(1):selector[0]==='['?(()=>{const m=selector.match(/^\[([^=\]]+)(?:="([^"]+)")?\]$/);return m&&m[1] in node.attrs&&(m[2]===undefined||node.attrs[m[1]]===m[2]);})():node.tag===selector;const all=[];const visit=node=>{for(const child of node.children){if(match(child))all.push(child);visit(child);}};visit(this);return all;}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
}
function parse(html){const root=new Element(),stack=[root];for(const match of html.matchAll(/<\/?([\w-]+)\b([^>]*)>/g)){const tag=match[1];if(match[0].startsWith('</')){if(stack.length>1)stack.pop();continue;}const el=new Element(tag);for(const a of match[2].matchAll(/([\w-]+)(?:="([^"]*)")?/g))el.setAttribute(a[1],a[2]||'');stack.at(-1).append(el);if(!['input','meta','br','hr','link'].includes(tag))stack.push(el);}return root;}
const page=parse(source.replace(/<style>[\s\S]*?<\/style>/g,'').replace(/<script>[\s\S]*?<\/script>/g,''));
const root=page.querySelector('#stat250-concepts');
const window={addEventListener(){}};
const context={document:{getElementById:id=>page.querySelector('#'+id),createElement:tag=>new Element(tag),createElementNS:(_,tag)=>new Element(tag),createTextNode:text=>{const e=new Element('#text');e.textContent=text;return e;}},window,ResizeObserver:class{constructor(fn){this.fn=fn;}observe(){}},console};
const script=source.match(/<script>([\s\S]*?)<\/script>/)[1].replace(/\}\)\(\);\s*$/, 'globalThis.audit={topics,visuals,select,sampleMeans,bootstrapMeans,normalCDF,quantile,boot,bootSE,bootLow,bootHigh,nullDifferences,normals};})();');
vm.runInNewContext(script,context);
const A=context.audit,get=id=>root.querySelector('#'+id);
const click=el=>{assert(el,'Missing control');assert(!el.disabled,'Disabled control');el.events.click();};
const walk=(node,fn)=>{fn(node);node.children.forEach(c=>walk(c,fn));};
assert.equal(A.topics.length,13);
assert.equal(A.topics.reduce((n,t)=>n+t.cards.length,0),52);
assert.equal(new Set(A.topics.flatMap(t=>t.cards.map(c=>c.visual))).size,52);
assert.equal(get('review-topic').querySelectorAll('option').length,13);
assert(!get('review-visual-content').hidden);
let buttonsExercised=0;
const auditMarkup=()=>{
  const panel=get('review-visual-content');
  assert(panel.children.length>0,'Empty visual');
  walk(panel,node=>{assert(!/NaN|undefined|Infinity/.test((node.markup||'')+node.textContent+JSON.stringify(node.attrs)),'Nonfinite output');});
  for(const svg of panel.querySelectorAll('svg')){
    const dims=svg.attrs.viewBox.split(' ').map(Number);
    for(const dot of svg.querySelectorAll('circle')){
      assert(Number(dot.attrs.cx)>=0&&Number(dot.attrs.cx)<=dims[2]);
      assert(Number(dot.attrs.cy)>=0&&Number(dot.attrs.cy)<=dims[3]);
    }
    for(const line of svg.querySelectorAll('line')){
      for(const name of ['x1','x2'])assert(Number(line.attrs[name])>=0&&Number(line.attrs[name])<=dims[2]);
      for(const name of ['y1','y2'])assert(Number(line.attrs[name])>=0&&Number(line.attrs[name])<=dims[3]);
    }
  }
};
for(const w of [220,390,640]){
  width=w;
  A.topics.forEach((topic,t)=>topic.cards.forEach((card,c)=>{
    A.select(t,c);
    assert(get('review-answer').hidden);
    assert(!get('review-visual-content').hidden);
    assert.equal(get('review-prompt').textContent,card.prompt);
    auditMarkup();
    click(get('review-reveal'));
    assert(!get('review-answer').hidden);
    assert(get('review-answer-text').querySelectorAll('strong').length>0,'Answer missing emphasis');
    const choices=get('review-visual-content').querySelectorAll('[data-choice]').map(b=>b.dataset.choice);
    for(const value of choices){click(get('review-visual-content').querySelector('[data-choice="'+value+'"]'));auditMarkup();buttonsExercised++;}
    for(const id of ['v-draw','v-resample','v-shuffle']){if(get(id)){click(get(id));auditMarkup();buttonsExercised++;}}
  }));
}
A.select(0,0);assert(get('review-prev').disabled);
for(let i=0;i<51;i++){click(get('review-next'));assert(get('review-answer').hidden);assert(!get('review-visual-content').hidden);}
assert(get('review-next').disabled);
for(let i=0;i<51;i++)click(get('review-prev'));
assert(get('review-prev').disabled);
get('review-topic').value='sampling';get('review-topic').events.change();
assert.equal(get('review-topic-title').textContent,'Sampling distributions');
assert.equal(get('review-count').textContent,'1 / 4');
assert.equal(A.nullDifferences.length,20);
assert(Math.abs(A.nullDifferences.reduce((a,b)=>a+b,0))<1e-10);
assert.equal(A.nullDifferences.filter(v=>Math.abs(v)>=14/3-1e-10).length,2);
const report={topics:A.topics.map(t=>({id:t.id,count:t.cards.length})),boot:{mean:A.boot.reduce((a,b)=>a+b,0)/A.boot.length,se:A.bootSE,low:A.bootLow,high:A.bootHigh},cdf:[-3,-1.6,0,1.6,3].map(x=>({x,p:A.normalCDF(x)})),replicates:[200,600,2000].map(n=>({n,values:Array.from(A.bootstrapMeans(n))})),coverage:[101,202,303,404].map(seed=>A.normals(100,seed).filter(x=>Math.abs(x)<=1.959964).length)};
console.log(JSON.stringify({...report,buttonsExercised}));
