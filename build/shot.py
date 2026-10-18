import asyncio
from playwright.async_api import async_playwright
B='/workspace/anime-quest/';U='file://'+B+'index.html';O=B+'shots/'
CON=open('/workspace/opera-essay2/app/build/shot.py').read().split("CON=r'''")[1].split("'''")[0]
CON=CON.replace("if(!e.getClientRects().length)return;","if(!e.getClientRects().length||e.closest('dialog:not([open])')||e.closest('.toast:not(.on)'))return;if(document.querySelector('dialog[open]')&&!e.closest('dialog'))return;")
SMALL='''()=>[...document.querySelectorAll("a,button,input,summary,label.file")].filter(e=>{if(e.closest('dialog:not([open])')||e.closest('.toast:not(.on)'))return false;if(e.closest('.foot li'))return false;const r=e.getBoundingClientRect();return r.width&&r.height&&(r.height<43.5||r.width<43.5)}).map(e=>(e.id||e.className)+':'+Math.round(e.getBoundingClientRect().width)+'x'+Math.round(e.getBoundingClientRect().height))'''
RM='''()=>{var t=[];document.querySelectorAll('*').forEach(e=>{var cs=getComputedStyle(e);if(cs.transitionDuration.split(',').some(x=>parseFloat(x)>0))t.push('tr:'+(e.id||e.className));if(cs.animationName!=='none')t.push('an:'+(e.id||e.className))});return {running:document.getAnimations().length,styled:t}}'''
async def seed(pg):
  await pg.evaluate('localStorage.clear()');await pg.reload();await pg.wait_for_timeout(200)
  for d,s,e in [('2026-10-17','kusuriya3',1),('2026-10-17','kusuriya3',2),('2026-10-18','kusuriya3',3),('2026-10-18','fxkurumi',1),('2026-10-19','fxkurumi',2)]:
    await pg.evaluate(f'localStorage.setItem("aq-test-today","{d}")');await pg.click(f'#card-{s} .ep[data-ep="{e}"]');await pg.wait_for_timeout(20)
  await pg.evaluate('localStorage.setItem("aq-test-today","2026-10-19")');await pg.evaluate('__aq.render()')
async def run(b,w,res):
  c=await b.new_context(viewport={'width':w,'height':844 if w==390 else 860},device_scale_factor=2 if w==390 else 1,reduced_motion='reduce',color_scheme='light')
  await c.add_init_script("window.__aqToday=function(){return localStorage.getItem('aq-test-today')||'2026-10-19'}")
  pg=await c.new_page();errs=[];ext=[]
  pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('request',lambda r:not r.url.startswith(('file:','data:','blob:')) and ext.append(r.url))
  await pg.goto(U);await seed(pg);r={}
  await pg.click('#doNext');await pg.wait_for_timeout(60)   # toast visible in shot
  r['scrollWidth']=await pg.evaluate('document.documentElement.scrollWidth')
  r['small']=await pg.evaluate(SMALL)
  r['contrast light']=await pg.evaluate(CON)
  r['reduced motion']=await pg.evaluate(RM)
  await pg.evaluate('scrollTo(0,0)');await pg.screenshot(path=f'{O}main_{w}.png')
  await pg.evaluate('document.getElementById("card-kusuriya3").scrollIntoView({block:"start"});scrollBy(0,-8)');await pg.screenshot(path=f'{O}cards_{w}.png')
  await pg.click('#card-kusuriya3 .edit');await pg.wait_for_timeout(50)
  r['small(dialog)']=await pg.evaluate(SMALL);r['contrast dialog']=await pg.evaluate(CON)
  await pg.screenshot(path=f'{O}edit_{w}.png');await pg.keyboard.press('Escape')
  await pg.click('#th');await pg.wait_for_timeout(30);await pg.reload();await pg.wait_for_timeout(200)
  r['dark after reload']=await pg.evaluate('[document.documentElement.dataset.theme,getComputedStyle(document.body).backgroundColor]')
  await pg.click('#doNext');await pg.wait_for_timeout(40)
  r['contrast dark']=await pg.evaluate(CON)
  await pg.evaluate('scrollTo(0,0)');await pg.screenshot(path=f'{O}dark_{w}.png')
  await pg.evaluate('document.getElementById("badges").scrollIntoView({block:"center"})');await pg.screenshot(path=f'{O}badges_dark_{w}.png')
  await pg.click('#card-kusuriya3 .edit');r['contrast dialog dark']=await pg.evaluate(CON);await pg.keyboard.press('Escape')
  r['errors']=errs;r['external']=ext;res[w]=r;await c.close()
async def main():
  res={}
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
    for w in (390,1280):await run(b,w,res)
    c=await b.new_context(viewport={'width':390,'height':844},reduced_motion='no-preference');pg=await c.new_page();await pg.goto(U);await pg.evaluate('localStorage.clear()');await pg.reload();await pg.wait_for_timeout(200)
    await pg.click('#doNext')
    res['motion allowed']=await pg.evaluate('document.getAnimations().map(a=>[a.constructor.name,a.animationName||a.transitionProperty,a.effect.getTiming().duration])')
    await c.close();await b.close()
  for k,v in res.items():
    print('==',k)
    if isinstance(v,dict):[print('  ',a,':',x) for a,x in v.items()]
    else:print('  ',v)
asyncio.run(main())
