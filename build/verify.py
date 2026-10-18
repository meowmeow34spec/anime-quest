import asyncio,json,re,os
from playwright.async_api import async_playwright
B='/workspace/anime-quest/';U='file://'+B+'index.html'
A=json.load(open(B+'data/anime.json'));H=open(B+'index.html').read()
rows=[]
def R(name,ok,detail=''):rows.append(('PASS' if ok else 'FAIL',name,detail))
# ---- static
m=re.search(r'const ANIME = (\[.*?\]);\n/\* ===== 작품 데이터 끝',H,re.S)
R('inline const ANIME == data/anime.json (one source of truth)',m and json.loads(m.group(1))==A,'marker block found' if m else 'missing')
R('ANIME block sits at top of the main script',H.find('const ANIME')<H.find('/* ================= 로직'),'')
RES={'kusuriya3':24,'seitokai':12,'fxkurumi':12}
R('episode counts == researched values',{a['id']:a['totalEpisodes'] for a in A}==RES,str(RES))
R('every show has source URLs',all(a['source'] and all(s['url'].startswith('https://') for s in a['source']) for a in A),'')
R('images local files in images/',all(a['image'].startswith('images/') and os.path.getsize(B+a['image'])<200_000 for a in A),', '.join(f"{a['image']} {os.path.getsize(B+a['image'])//1024}KB" for a in A))
ext=[x for x in re.findall(r'(?:src)=["\']([^"\']+)',H) if not x.startswith(('images/','data:'))]+re.findall(r'url\((?!data:)[^)]*\)',H)+re.findall(r'<link[^>]+href',H)
R('no external src/link/url() in HTML',not ext,str(ext) or 'none (source <a> links only fire on tap)')
for w in ['뒤처','실패','놓쳤','끊겼','망했']:
  if w in H:R(f'no pressure wording "{w}"',False)
R('no pressure wording (뒤처/실패/놓쳤/끊겼/망했)',not any(w in H for w in ['뒤처','실패','놓쳤','끊겼','망했']),'')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
    c=await b.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');pg=await c.new_page();errs=[];extq=[]
    pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('request',lambda r:not r.url.startswith(('file:','data:','blob:')) and extq.append(r.url))
    await c.add_init_script("window.__aqToday=function(){return localStorage.getItem('aq-test-today')||'2026-10-19'}")
    await pg.goto(U);await pg.evaluate('localStorage.clear()');await pg.reload();await pg.wait_for_timeout(300)
    ev=pg.evaluate
    R('3 quest cards',await ev('document.querySelectorAll(".card").length')==3)
    tot=await ev('[...document.querySelectorAll(".card")].map(c=>c.querySelector(".pgt span").textContent)')
    R('page episode counts match research',tot==['0 / 24화','0 / 12화','0 / 12화'],str(tot))
    R('episode tiles = counts',await ev('[...document.querySelectorAll(".card")].map(c=>c.querySelectorAll(".ep").length)')==[24,12,12])
    imgs=await ev('[...document.images].map(i=>[i.getAttribute("src"),i.complete&&i.naturalWidth>0])')
    R('images load locally',all(s.startswith('images/') and ok for s,ok in imgs),str(imgs))
    R('today quest heading + single big button',await ev('[document.getElementById("tqh").textContent,document.querySelectorAll(".today .big").length,document.getElementById("doNext").textContent]')==['오늘의 퀘스트: 1화',1,'1화 봤어요'])
    # check ep via big button
    await pg.click('#doNext');await pg.wait_for_timeout(50)
    st=await ev('[document.querySelector("#card-kusuriya3 .pgt span").textContent,document.getElementById("xpTotal").textContent,document.getElementById("doNext").textContent,document.getElementById("toastMsg").textContent,document.querySelector("#card-kusuriya3 .ep[data-ep=\\"1\\"]").getAttribute("aria-pressed"),document.getElementById("streak").textContent]')
    R('check updates progress, XP, next action, toast',st[:3]==['1 / 24화','10','2화 봤어요'] and '1화 완료! +10 XP' in st[3] and st[4]=='true' and st[5]=='1',str(st))
    await pg.click('#card-fxkurumi .ep[data-ep="3"]');await pg.wait_for_timeout(30)
    await pg.reload();await pg.wait_for_timeout(200)
    st2=await ev('[document.querySelector("#card-kusuriya3 .pgt span").textContent,document.querySelector("#card-fxkurumi .pgt span").textContent,document.getElementById("xpTotal").textContent,document.getElementById("doNext").dataset.id+" "+document.getElementById("doNext").textContent]')
    R('persists after reload (progress, XP, next action follows last show)',st2==['1 / 24화','1 / 12화','20','fxkurumi 1화 봤어요'],str(st2))
    # undo via toast + uncheck per episode
    await pg.click('#card-fxkurumi .ep[data-ep="4"]');await pg.click('#toastUndo');await pg.wait_for_timeout(30)
    a=await ev('document.querySelector("#card-fxkurumi .ep[data-ep=\\"4\\"]").getAttribute("aria-pressed")')
    await pg.click('#card-fxkurumi .ep[data-ep="3"]');await pg.wait_for_timeout(30)
    b2=await ev('[document.querySelector("#card-fxkurumi .pgt span").textContent,document.getElementById("toastMsg").textContent]')
    await pg.click('#card-fxkurumi [data-undo]');await pg.wait_for_timeout(30)
    c2=await ev('document.querySelector("#card-fxkurumi .pgt span").textContent')
    R('undo (toast), uncheck per episode, per-card undo',a=='false' and b2[0]=='0 / 12화' and c2=='1 / 12화',f'{a} {b2} {c2}')
    # streak simulation
    await ev('localStorage.clear()');await pg.reload();await pg.wait_for_timeout(150)
    async def day(d,ep=None,show='seitokai'):
      await ev(f'localStorage.setItem("aq-test-today","{d}")');await ev('__aq.render()')
      if ep:await pg.click(f'#card-{show} .ep[data-ep="{ep}"]');await pg.wait_for_timeout(20)
      return await ev('[__aq.metrics().streak,__aq.metrics().best,document.getElementById("streakMsg").textContent,Object.keys(__aq.state().badges).join(",")]')
    s=[await day('2026-10-10',1),await day('2026-10-11',2),await day('2026-10-12',3),await day('2026-10-13'),await day('2026-10-15'),await day('2026-10-15',4),await day('2026-10-16',5)]
    exp=[1,2,3,3,0,1,2]
    R('streak logic over simulated dates',[x[0] for x in s]==exp and s[4][1]==3,' | '.join(f'{x[0]}일 best{x[1]} "{x[2]}"' for x in s))
    R('gentle wording when streak pauses',s[3][2]=='오늘 1화를 보면 4일이 돼요.' and s[4][2]=='쉬어 가는 중이에요. 언제든 1화로 다시 시작하면 돼요.',f'{s[3][2]} / {s[4][2]}')
    R('badges earned (first, s3, five, back) and kept',all(k in s[-1][3] for k in ['first','s3','five','back']),s[-1][3])
    R('uncheck removes that day from streak',True if True else False,'')
    await day('2026-10-16');await pg.click('#card-seitokai .ep[data-ep="5"]');await pg.wait_for_timeout(20)
    un=await ev('[__aq.metrics().streak,Object.keys(__aq.state().badges).length]')
    rows[-1]=('PASS' if un[0]==1 and un[1]>=4 else 'FAIL','uncheck today removes the day from the streak; badges stay',str(un))
    # edit built-in count -> blank -> back
    await ev('localStorage.removeItem("aq-test-today")')
    await pg.click('#card-kusuriya3 .edit');await pg.fill('#fTotal','13');await pg.click('#ed .primary');await pg.wait_for_timeout(30)
    e1=await ev('[document.querySelector("#card-kusuriya3 .pgt span").textContent,document.querySelectorAll("#card-kusuriya3 .ep").length]')
    url_hidden=None
    await pg.click('#card-kusuriya3 .edit');url_hidden=await ev('document.getElementById("fUrlRow").hidden');await pg.fill('#fTotal','');await pg.click('#ed .primary');await pg.wait_for_timeout(30)
    e2=await ev('[document.querySelector("#card-kusuriya3 .pgt span").textContent,!!document.querySelector("#card-kusuriya3 .unk")]')
    await pg.reload();await pg.wait_for_timeout(150)
    e3=await ev('document.querySelector("#card-kusuriya3 .pgt span").textContent')
    await pg.click('#card-kusuriya3 .edit');await pg.fill('#fTotal','24');await pg.click('#ed .primary');await pg.wait_for_timeout(30)
    e4=await ev('[document.querySelector("#card-kusuriya3 .pgt span").textContent,JSON.stringify(__aq.state().over.kusuriya3||{})]')
    R('built-in episode count editable (13 -> blank -> 24), persists',e1==['0 / 13화',13] and e2[0]=='0 / ?화' and e2[1] and e3=='0 / ?화' and e4[0]=='0 / 24화',f'{e1} {e2} {e3} {e4}')
    R('built-in shows: no remote-URL field (upload only)',url_hidden is True)
    # hide / unhide
    await pg.click('#card-seitokai .edit');await pg.click('[data-ask="hideAsk"]');await pg.click('#doHide');await pg.wait_for_timeout(30)
    h1=await ev('[document.querySelectorAll(".card").length,document.querySelectorAll("#hiddenList li").length]')
    await pg.reload();await pg.wait_for_timeout(100);h2=await ev('document.querySelectorAll(".card").length')
    await pg.click('[data-unhide="seitokai"]');h3=await ev('document.querySelectorAll(".card").length')
    R('hide built-in (confirm step), persists, unhide',h1==[2,1] and h2==2 and h3==3,f'{h1} {h2} {h3}')
    # add with upload
    await pg.click('#addBtn');await pg.fill('#fTitle','테스트 애니');await pg.set_input_files('#fFile',B+'build/test_upload.png');await pg.wait_for_timeout(400)
    await pg.click('#ed .primary');await pg.wait_for_timeout(100)
    ad=await ev('(()=>{const c=[...document.querySelectorAll(".card")].pop();const im=c.querySelector("img.cover");return [document.querySelectorAll(".card").length,c.querySelector("h3").textContent,c.querySelector(".pgt span").textContent,!!c.querySelector(".unk"),im&&im.src.slice(0,22),im&&im.naturalWidth,im&&im.src.length]})()')
    await pg.reload();await pg.wait_for_timeout(200)
    ad2=await ev('(()=>{const c=[...document.querySelectorAll(".card")].pop();const im=c.querySelector("img.cover");return [document.querySelectorAll(".card").length,c.querySelector("h3").textContent,im&&im.naturalWidth]})()')
    R('add show (title, blank count, upload) + persists',ad[0]==4 and ad[1]=='테스트 애니' and ad[2]=='0 / ?화' and ad[3] and ad[4]=='data:image/jpeg;base64' and ad2==[4,'테스트 애니',600],f'{ad[:6]} dataURL {ad[6]//1024}KB; after reload {ad2}')
    R('upload resized to 600px wide JPEG data URL',ad[5]==600,f'{ad[5]}px, {ad[6]//1024}KB from a 1600x900 PNG')
    cid=await ev('__aq.state().custom[0].id')
    # open-ended episodes when total unknown
    await pg.click(f'#card-{cid} .ep[data-ep="1"]');tiles=await ev(f'document.querySelectorAll("#card-{cid} .ep").length')
    R('unknown total: tiles grow (1 checked -> next tile appears)',tiles==2,str(tiles))
    # edit custom
    await pg.click(f'#card-{cid} .edit');await pg.fill('#fTitle','테스트 애니 2');await pg.fill('#fTotal','5');await pg.click('#ed .primary');await pg.wait_for_timeout(30)
    await pg.reload();await pg.wait_for_timeout(150)
    ed=await ev(f'[document.querySelector("#card-{cid} h3").textContent,document.querySelector("#card-{cid} .pgt span").textContent]')
    R('edit user show (title, count), persists',ed==['테스트 애니 2','1 / 5화'],str(ed))
    # quota
    await ev('(()=>{const o=Storage.prototype.setItem;window.__orig=o;Storage.prototype.setItem=function(k,v){if(k==="aq-v1")throw new DOMException("full","QuotaExceededError");return o.call(this,k,v)};return 1})()')
    before=await ev('JSON.stringify(__aq.state().custom)')
    await pg.click('#addBtn');await pg.fill('#fTitle','꽉 찬 테스트');await pg.set_input_files('#fFile',B+'build/test_upload.png');await pg.wait_for_timeout(400);await pg.click('#ed .primary');await pg.wait_for_timeout(50)
    q=await ev('[document.getElementById("ed").open,document.getElementById("edErr").textContent,JSON.stringify(__aq.state().custom)]')
    await pg.click('#edCancel')
    await pg.click('#card-fxkurumi .ep[data-ep="1"]');await pg.wait_for_timeout(30)
    q2=await ev('[document.getElementById("toastMsg").textContent,document.querySelector("#card-fxkurumi .ep[data-ep=\\"1\\"]").getAttribute("aria-pressed")]')
    await ev('(()=>{Storage.prototype.setItem=window.__orig;return 1})()')
    qm=await ev('__aq.QUOTA_MSG')
    R('quota error: friendly Korean message, nothing half-saved',q[0] and q[1]==qm and q[2]==before and q2[0]==qm and q2[1]=='false',f'dialog stays open, msg="{q[1][:24]}…", toggle reverted={q2[1]=="false"}')
    # delete with confirm
    await pg.click(f'#card-{cid} .edit');await pg.click('[data-ask="delAsk"]');vis=await ev('!document.getElementById("delAsk").hidden')
    await pg.click('#delAsk [data-nevermind]');still=await ev('document.getElementById("ed").open')
    await pg.click('[data-ask="delAsk"]');await pg.click('#doDelete');await pg.wait_for_timeout(30)
    await pg.reload();await pg.wait_for_timeout(150)
    dl=await ev(f'[document.querySelectorAll(".card").length,!document.getElementById("card-{cid}"),!("{cid}" in __aq.state().watch)]')
    R('delete user show needs confirm, persists',vis and still and dl==[3,True,True],f'confirm shown={vis}, 그만두기 keeps dialog={still}, after={dl}')
    # wipe
    await pg.click('#wipeBtn');await pg.click('#doWipe');await pg.wait_for_timeout(30)
    w=await ev('[document.getElementById("xpTotal").textContent,__aq.state().custom.length,Object.keys(__aq.state().badges).length]')
    R('data reset behind confirm',w==['0',0,0],str(w))
    R('0 console errors',not errs,str(errs[:3]))
    R('0 external requests',not extq,str(extq[:3]))
    await b.close()
asyncio.run(main())
wd=max(len(r[1]) for r in rows)
for s,n,d in rows:print(f'{s} | {n:<{wd}} | {d}')
print('fails:',sum(1 for r in rows if r[0]!='PASS'))
