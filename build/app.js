/* ================= 로직 (작품 데이터는 위의 ANIME 상수) ================= */
(function(){
'use strict';
var KEY='aq-v1',TKEY='aq-theme',XP_EP=10,XP_DONE=50,XP_LV=100;
var BADGES=[
 {id:'first',name:'첫 화',desc:'처음으로 1화를 체크했어요',test:function(m){return m.eps>=1}},
 {id:'five',name:'다섯 걸음',desc:'모두 합쳐 5화를 봤어요',test:function(m){return m.eps>=5}},
 {id:'ten',name:'열 화 돌파',desc:'모두 합쳐 10화를 봤어요',test:function(m){return m.eps>=10}},
 {id:'s3',name:'사흘 연속',desc:'3일 연속으로 1화 이상 봤어요',test:function(m){return m.streak>=3}},
 {id:'s7',name:'일주일 연속',desc:'7일 연속으로 1화 이상 봤어요',test:function(m){return m.streak>=7}},
 {id:'done1',name:'첫 완주',desc:'작품 하나를 끝까지 봤어요',test:function(m){return m.done>=1}},
 {id:'back',name:'다시 시작',desc:'쉬었다가 다시 1화를 봤어요',test:function(m){return m.back}}
];
var $=function(s,r){return (r||document).querySelector(s)};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function pad(n){return (n<10?'0':'')+n}
function today(){if(typeof window.__aqToday==='function')return window.__aqToday();var d=new Date();return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())}
function addDays(s,n){var p=s.split('-'),d=new Date(+p[0],+p[1]-1,+p[2]+n);return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())}
function blank(){return {v:1,watch:{},custom:[],over:{},badges:{},focus:null,hist:[]}}
var S;try{S=JSON.parse(localStorage.getItem(KEY))||blank()}catch(e){S=blank()}
['watch','over','badges'].forEach(function(k){if(!S[k]||typeof S[k]!=='object')S[k]={}});if(!Array.isArray(S.custom))S.custom=[];if(!Array.isArray(S.hist))S.hist=[];
function isQuota(e){return e&&(e.name==='QuotaExceededError'||e.name==='NS_ERROR_DOM_QUOTA_REACHED'||e.code===22||e.code===1014)}
var QUOTA_MSG='저장 공간이 꽉 찼어요. 이미지를 더 작은 걸로 바꾸거나, 다른 작품의 올린 이미지를 빼면 저장할 수 있어요.';
function save(){try{localStorage.setItem(KEY,JSON.stringify(S));return true}catch(e){if(isQuota(e)){toast(QUOTA_MSG);return false}toast('저장하지 못했어요. 이 브라우저에서 저장소를 쓸 수 없는 상태예요.');return false}}
function snapshot(){return JSON.stringify(S)}
function restore(s){S=JSON.parse(s)}
/* ---------- 작품 ---------- */
function all(){return ANIME.map(function(a){var o=S.over[a.id]||{};return {id:a.id,title:a.title,original:a.original,builtIn:true,total:('total' in o)?o.total:a.totalEpisodes,officialTotal:a.totalEpisodes,image:o.image||a.image,imageCustom:!!o.image,status:a.status,note:a.note,source:a.source,hidden:!!o.hidden}}).concat(S.custom.map(function(c){return {id:c.id,title:c.title,builtIn:false,total:c.totalEpisodes,officialTotal:null,image:c.image||'',imageCustom:!!c.image,status:'',note:'',source:null,hidden:false}}))}
function visible(){return all().filter(function(a){return !a.hidden})}
function byId(id){return all().filter(function(a){return a.id===id})[0]}
function W(id){return S.watch[id]||(S.watch[id]={})}
function watchedList(a){var w=S.watch[a.id]||{};return Object.keys(w).map(Number).filter(function(n){return a.total==null||n<=a.total})}
function nextEp(a){var w=S.watch[a.id]||{};if(a.total==null){var m=0;for(var k in w)m=Math.max(m,+k);for(var i=1;i<=m+1;i++)if(!w[i])return i}for(var j=1;j<=a.total;j++)if(!w[j])return j;return null}
function isDone(a){return a.total!=null&&a.total>0&&watchedList(a).length>=a.total}
function metrics(){var shows=all(),eps=0,done=0;shows.forEach(function(a){eps+=watchedList(a).length;if(isDone(a))done++});
 var dates={};shows.forEach(function(a){var w=S.watch[a.id]||{};for(var k in w)if(a.total==null||+k<=a.total)dates[w[k]]=(dates[w[k]]||0)+1});
 var t=today(),y=addDays(t,-1),start=dates[t]?t:(dates[y]?y:null),streak=0,d=start;while(d&&dates[d]){streak++;d=addDays(d,-1)}
 var runStart=start?addDays(start,-(streak-1)):null,back=false;if(runStart)for(var k2 in dates)if(k2<addDays(runStart,-1))back=true;
 var ks=Object.keys(dates).sort(),best=0,run=0,prev=null;ks.forEach(function(k){run=(prev&&addDays(prev,1)===k)?run+1:1;best=Math.max(best,run);prev=k});
 var xp=eps*XP_EP+done*XP_DONE;
 return {eps:eps,done:done,streak:streak,best:best,todayCount:dates[t]||0,pending:!dates[t]&&!!dates[y],rest:!start&&ks.length>0,back:back&&!!dates[t],xp:xp,lv:Math.floor(xp/XP_LV)+1,inLv:xp%XP_LV}}
function newBadges(){var m=metrics(),got=[];BADGES.forEach(function(b){if(!S.badges[b.id]&&b.test(m)){S.badges[b.id]=today();got.push(b)}});return got}
/* ---------- 행동 ---------- */
function toggle(id,ep){var a=byId(id);if(!a)return;var w=W(id),before=metrics(),snap=snapshot();
 if(w[ep]){S.hist.push({id:id,ep:ep,prev:w[ep]});delete w[ep];S.focus=id;trim();if(!save()){restore(snap);return}render();toast(ep+'화 체크를 풀었어요.',true);return}
 w[ep]=today();S.hist.push({id:id,ep:ep,prev:null});S.focus=id;trim();var got=newBadges(),after=metrics(),a2=byId(id);
 if(!save()){restore(snap);render();return}
 var msg=ep+'화 완료! +'+XP_EP+' XP';if(isDone(a2)&&!isDoneBefore(a,ep))msg+=' · 완주 보너스 +'+XP_DONE+' XP';if(after.lv>before.lv)msg+=' · 레벨 '+after.lv+'!';
 if(got.length)msg+=' · 배지: '+got.map(function(b){return b.name}).join(', ');
 render();pop(id,ep);toast(msg,true)}
function isDoneBefore(a,ep){var l=watchedList(a).filter(function(n){return n!==ep}).length;return a.total!=null&&l>=a.total}
function trim(){if(S.hist.length>30)S.hist=S.hist.slice(-30)}
function undo(id){var i=S.hist.length-1;if(id)while(i>=0&&S.hist[i].id!==id)i--;if(i<0)return;var h=S.hist.splice(i,1)[0],w=W(h.id);if(h.prev)w[h.ep]=h.prev;else delete w[h.ep];S.focus=h.id;save();render();toast(h.ep+'화를 '+(h.prev?'다시 체크했어요.':'체크 전으로 되돌렸어요.'))}
/* ---------- 토스트 ---------- */
var tEl,tTimer;
function toast(msg,withUndo){tEl=tEl||$('#toast');$('#toastMsg').textContent=msg;$('#toastUndo').hidden=!withUndo;tEl.classList.add('on');clearTimeout(tTimer);tTimer=setTimeout(function(){tEl.classList.remove('on')},4200)}
function pop(id,ep){var b=document.querySelector('.ep[data-id="'+id+'"][data-ep="'+ep+'"]');if(b){b.classList.add('pop')}}
/* ---------- 렌더 ---------- */
function imgHtml(a,cls){if(a.image)return '<img class="'+cls+'" src="'+esc(a.image)+'" alt="" loading="lazy" decoding="async">';return '<div class="'+cls+' noimg" aria-hidden="true"><span>'+esc(a.title.slice(0,1))+'</span></div>'}
function pickFocus(){var v=visible().filter(function(a){return nextEp(a)!=null});if(!v.length)return null;var f=v.filter(function(a){return a.id===S.focus})[0];return f||v[0]}
function render(){var ae=document.activeElement,key=ae&&ae.dataset?ae.dataset.k:null;renderToday();renderCards();renderBadges();renderHidden();if(key){var el=document.querySelector('[data-k="'+key+'"]');if(el)el.focus({preventScroll:true})}}
function renderToday(){var m=metrics(),f=pickFocus(),el=$('#todayBody'),others=visible().filter(function(a){return nextEp(a)!=null}).length;
 var h='';
 if(f){var n=nextEp(f);
  h+='<div class="tq-next">'+imgHtml(f,'tq-img')+'<div><p class="tq-show">'+esc(f.title)+'</p><p class="tq-ep"><span class="num">'+n+'</span>화</p></div></div>'+
   '<button type="button" class="big" id="doNext" data-k="doNext" data-id="'+esc(f.id)+'" data-ep="'+n+'">'+n+'화 봤어요</button>'+
   '<p class="tq-hint">'+(m.todayCount?'<span class="ok">오늘 퀘스트 완료! 오늘 '+m.todayCount+'화 봤어요.</span> 더 보고 싶을 때만 이어서 봐도 충분해요.':'딱 1화만 보면 오늘 퀘스트 완료예요.')+'</p>'+
   (others>1?'<button type="button" class="ghost" id="swap" data-k="swap">다른 작품으로 바꾸기</button>':'');
 }else{h+='<p class="tq-show">지금 체크할 다음 화가 없어요.</p><p class="tq-hint">작품을 추가하거나, 총 화수를 늘려 보세요.</p><button type="button" class="big" id="addFromToday" data-k="addFromToday">작품 추가</button>'}
 el.innerHTML=h;$('#todayDone').hidden=!m.todayCount;
 $('#lv').textContent=m.lv;$('#xpNow').textContent=m.inLv;$('#xpBar').style.width=m.inLv+'%';$('#xpTotal').textContent=m.xp;
 $('#streak').textContent=m.streak;
 $('#streakMsg').textContent=m.todayCount?(m.streak>1?m.streak+'일째 이어 가는 중이에요.':'오늘부터 연속 기록이 시작됐어요.'):m.pending?'오늘 1화를 보면 '+(m.streak+1)+'일이 돼요.':m.rest?'쉬어 가는 중이에요. 언제든 1화로 다시 시작하면 돼요.':'첫 화를 보면 연속 기록이 시작돼요.';
 $('#best').textContent=m.best;$('#todayN').textContent=m.todayCount}
function renderCards(){var h='';visible().forEach(function(a){var w=S.watch[a.id]||{},list=watchedList(a),n=nextEp(a),tot=a.total,pct=tot?Math.round(list.length/tot*100):0,canUndo=S.hist.some(function(x){return x.id===a.id});
 var eps='',max=tot!=null?tot:Math.max(n||1,list.length?Math.max.apply(null,list):0);
 for(var i=1;i<=max;i++){var on=!!w[i];eps+='<button type="button" class="ep'+(on?' on':'')+(i===n?' nx':'')+'" data-k="ep-'+esc(a.id)+'-'+i+'" data-id="'+esc(a.id)+'" data-ep="'+i+'" aria-pressed="'+on+'" aria-label="'+i+'화'+(on?', 봤어요':'')+'"><span>'+i+'</span>'+(on?'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>':'')+'</button>'}
 h+='<article class="card" id="card-'+esc(a.id)+'" data-show="'+esc(a.id)+'">'+imgHtml(a,'cover')+'<div class="cb">'+
 '<div class="ch"><h3>'+esc(a.title)+'</h3><button type="button" class="edit" data-k="edit-'+esc(a.id)+'" data-edit="'+esc(a.id)+'">편집</button></div>'+
 (a.original?'<p class="orig" lang="ja">'+esc(a.original)+'</p>':'')+
 (a.status?'<p class="st">'+esc(a.status)+'</p>':'')+(a.note?'<p class="st">'+esc(a.note)+'</p>':'')+
 '<div class="pg"><div class="pgt"><span><b class="pgn">'+list.length+'</b> / '+(tot!=null?tot+'화':'?화')+'</span><span>'+(isDone(a)?'완주했어요!':tot!=null?pct+'%':'총 화수를 정하면 진행률이 보여요')+'</span></div>'+
 '<div class="bar" aria-hidden="true"><i style="width:'+pct+'%"></i></div></div>'+
 (tot==null?'<p class="unk">총 화수를 아직 몰라요. <button type="button" class="link" data-k="settot-'+esc(a.id)+'" data-edit="'+esc(a.id)+'">총 화수 정하기</button></p>':'')+
 '<div class="eps" role="group" aria-label="'+esc(a.title)+' 회차">'+eps+'</div>'+
 '<div class="cf"><button type="button" class="ghost" data-k="undo-'+esc(a.id)+'" data-undo="'+esc(a.id)+'"'+(canUndo?'':' disabled')+'>마지막 체크 되돌리기</button></div>'+
 '</div></article>'});
 $('#cards').innerHTML=h||'<p class="empty">보이는 작품이 없어요. 작품을 추가하거나 숨긴 작품을 다시 보이게 해 보세요.</p>';
 var vc=visible().length;$('#count').textContent=vc}
function renderBadges(){$('#badges').innerHTML=BADGES.map(function(b){var on=!!S.badges[b.id];return '<li class="bd'+(on?' on':'')+'"><span class="bi" aria-hidden="true">'+(on?'<svg viewBox="0 0 24 24"><path d="M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8L3.5 9.2l5.9-.9z" fill="currentColor"/></svg>':'<svg viewBox="0 0 24 24"><path d="M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8L3.5 9.2l5.9-.9z" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>')+'</span><span><b>'+b.name+'</b><small>'+(on?b.desc:'아직이에요. '+b.desc.replace('했어요','하면 받아요').replace('봤어요','보면 받아요'))+'</small></span></li>'}).join('');
 $('#bdCount').textContent=Object.keys(S.badges).filter(function(k){return BADGES.some(function(b){return b.id===k})}).length}
function renderHidden(){var hid=all().filter(function(a){return a.hidden});$('#hiddenWrap').hidden=!hid.length;$('#hiddenList').innerHTML=hid.map(function(a){return '<li><span>'+esc(a.title)+'</span><button type="button" class="ghost" data-k="unhide-'+esc(a.id)+'" data-unhide="'+esc(a.id)+'">다시 보이기</button></li>'}).join('')}
/* ---------- 이미지 업로드 ---------- */
function fileToDataURL(file){return new Promise(function(res,rej){if(!file||!/^image\//.test(file.type)){rej(new Error('type'));return}var url=URL.createObjectURL(file),im=new Image();im.onload=function(){var w=Math.min(600,im.naturalWidth),h=Math.round(im.naturalHeight*w/im.naturalWidth),c=document.createElement('canvas');c.width=w;c.height=h;var x=c.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,w,h);x.drawImage(im,0,0,w,h);URL.revokeObjectURL(url);res(c.toDataURL('image/jpeg',0.8))};im.onerror=function(){URL.revokeObjectURL(url);rej(new Error('decode'))};im.src=url})}
/* ---------- 편집/추가 다이얼로그 ---------- */
var dlg=$('#ed'),mode=null,curId=null,pendingImg=undefined,opener=null;
function openEd(m,id){mode=m;curId=id||null;pendingImg=undefined;opener=document.activeElement;var a=id?byId(id):null,f=$('#edForm');f.reset();$('#edErr').textContent='';closeConfirms();
 $('#edTitle').textContent=m==='add'?'작품 추가':a.title+' 편집';
 $('#fTitleRow').hidden=!(m==='add'||(a&&!a.builtIn));$('#fTitle').value=a&&!a.builtIn?a.title:'';
 $('#fTotal').value=a&&a.total!=null?a.total:'';
 $('#fTotalHint').textContent=a&&a.builtIn?'공식 발표 기준 '+a.officialTotal+'화예요. 바꾸면 이 브라우저에만 저장돼요.':'모르면 비워 두세요. 나중에 정할 수 있어요.';
 $('#fUrlRow').hidden=!!(a&&a.builtIn);$('#fUrl').value=a&&!a.builtIn&&a.image&&!/^data:/.test(a.image)?a.image:'';
 $('#imgPrev').innerHTML=a&&a.image?'<img src="'+esc(a.image)+'" alt="">':'';
 $('#imgReset').hidden=!(a&&a.imageCustom);$('#imgReset').textContent=a&&a.builtIn?'원래 이미지로':'이미지 빼기';
 $('#dangerBuilt').hidden=!(a&&a.builtIn);$('#dangerCustom').hidden=!(a&&!a.builtIn);$('#dangerProg').hidden=!a;
 dlg.showModal();(m==='add'?$('#fTitle'):$('#fTotal')).focus()}
function closeConfirms(){[].forEach.call(document.querySelectorAll('.confirm'),function(c){c.hidden=true})}
dlg.addEventListener('close',function(){if(opener&&document.body.contains(opener))opener.focus()});
$('#fFile').addEventListener('change',function(){var f=this.files[0];if(!f)return;$('#edErr').textContent='';fileToDataURL(f).then(function(d){pendingImg=d;$('#imgPrev').innerHTML='<img src="'+d+'" alt="">';$('#imgInfo').textContent='600px 너비로 줄였어요 (약 '+Math.round(d.length*0.75/1024)+'KB).'}).catch(function(){$('#edErr').textContent='이 파일은 이미지로 읽지 못했어요. JPG나 PNG로 다시 골라 주세요.'})});
$('#imgReset').addEventListener('click',function(){pendingImg=null;$('#imgPrev').innerHTML='';$('#fUrl').value='';$('#imgInfo').textContent=mode==='edit'&&byId(curId).builtIn?'저장하면 원래 이미지로 돌아가요.':'저장하면 이미지가 빠져요.'});
function readTotal(){var v=$('#fTotal').value.trim();if(v==='')return {ok:true,val:null};var n=Number(v);if(!/^\d+$/.test(v)||n<1||n>2000)return {ok:false};return {ok:true,val:n}}
$('#edForm').addEventListener('submit',function(e){e.preventDefault();var t=readTotal();if(!t.ok){$('#edErr').textContent='총 화수는 1 이상의 숫자로 적어 주세요. 모르면 비워 둬도 돼요.';$('#fTotal').focus();return}
 var snap=snapshot(),url=$('#fUrl').value.trim();
 if(url&&!/^https?:\/\//i.test(url)&&!/^data:image\//.test(url)){$('#edErr').textContent='이미지 주소는 http:// 또는 https://로 시작해야 해요.';return}
 if(mode==='add'){var title=$('#fTitle').value.trim();if(!title){$('#edErr').textContent='제목을 적어 주세요.';$('#fTitle').focus();return}
  var id='u'+Date.now().toString(36)+Math.random().toString(36).slice(2,6);S.custom.push({id:id,title:title,totalEpisodes:t.val,image:pendingImg||url||'',source:null});S.focus=id;
  if(!save()){restore(snap);$('#edErr').textContent=QUOTA_MSG;return}dlg.close();render();toast('“'+title+'” 퀘스트를 추가했어요.');var c=document.getElementById('card-'+id);if(c)c.scrollIntoView({block:'nearest'});return}
 var a=byId(curId);
 if(a.builtIn){var o=S.over[a.id]||(S.over[a.id]={});if(t.val===a.officialTotal)delete o.total;else o.total=t.val;if(pendingImg===null)delete o.image;else if(pendingImg)o.image=pendingImg}
 else{var c2=S.custom.filter(function(x){return x.id===a.id})[0],nt=$('#fTitle').value.trim();if(!nt){$('#edErr').textContent='제목을 적어 주세요.';return}c2.title=nt;c2.totalEpisodes=t.val;if(pendingImg===null)c2.image='';else if(pendingImg)c2.image=pendingImg;else c2.image=url}
 if(!save()){restore(snap);$('#edErr').textContent=QUOTA_MSG;return}dlg.close();render();toast('저장했어요.')});
$('#edCancel').addEventListener('click',function(){dlg.close()});
document.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
 if(b.dataset.ask){closeConfirms();var c=document.getElementById(b.dataset.ask);c.hidden=false;var y=c.querySelector('.danger');if(y)y.focus();return}
 if(b.dataset.nevermind!==undefined){var c3=b.closest('.confirm');c3.hidden=true;var asker=document.querySelector('[data-ask="'+c3.id+'"]');if(asker)asker.focus();return}
 if(b.id==='doHide'){var o=S.over[curId]||(S.over[curId]={});o.hidden=true;if(S.focus===curId)S.focus=null;save();var nm=byId(curId).title;dlg.close();render();toast('“'+nm+'”을 숨겼어요. 아래 “숨긴 작품”에서 다시 보이게 할 수 있어요.');return}
 if(b.id==='doDelete'){var nm2=byId(curId).title;S.custom=S.custom.filter(function(x){return x.id!==curId});delete S.watch[curId];S.hist=S.hist.filter(function(h){return h.id!==curId});if(S.focus===curId)S.focus=null;save();dlg.close();render();toast('“'+nm2+'”을 지웠어요.');return}
 if(b.id==='doProg'){delete S.watch[curId];S.hist=S.hist.filter(function(h){return h.id!==curId});save();dlg.close();render();toast('이 작품의 진행을 처음으로 돌렸어요.');return}
 if(b.id==='doWipe'){S=blank();save();try{localStorage.removeItem(KEY)}catch(e2){}$('#wipeAsk').hidden=true;render();toast('모든 데이터를 지웠어요. 처음부터 가볍게 시작해요.');return}
 if(b.classList.contains('ep')){toggle(b.dataset.id,+b.dataset.ep);return}
 if(b.id==='doNext'){toggle(b.dataset.id,+b.dataset.ep);return}
 if(b.id==='swap'){var v=visible().filter(function(a){return nextEp(a)!=null}),f=pickFocus(),i=v.indexOf(v.filter(function(a){return a.id===f.id})[0]);S.focus=v[(i+1)%v.length].id;save();render();return}
 if(b.dataset.edit){openEd('edit',b.dataset.edit);return}
 if(b.dataset.undo){undo(b.dataset.undo);return}
 if(b.dataset.unhide){var o2=S.over[b.dataset.unhide];if(o2)delete o2.hidden;save();render();toast('다시 보이게 했어요.');return}
 if(b.id==='toastUndo'){undo(null);return}
 if(b.id==='addBtn'||b.id==='addFromToday'){openEd('add');return}
});
/* ---------- 테마 ---------- */
var root=document.documentElement,th=$('#th');function isDark(){return root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches}
function syncTh(){var d=isDark();th.setAttribute('aria-pressed',String(d));th.setAttribute('aria-label',d?'라이트 모드로':'다크 모드로')}
th.addEventListener('click',function(){var n=isDark()?'light':'dark';root.dataset.theme=n;try{localStorage.setItem(TKEY,n)}catch(e){}syncTh()});syncTh();
window.__aq={state:function(){return JSON.parse(JSON.stringify(S))},metrics:metrics,render:render,QUOTA_MSG:QUOTA_MSG};
render();
})();
