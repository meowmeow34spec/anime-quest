# build.py: data/anime.json(단일 원본) -> index.html 안의 const ANIME 상수로 인라인
import json,re,html,subprocess,base64,os
B='/workspace/anime-quest/';T=B+'build/'
A=json.load(open(B+'data/anime.json'))
for a in A:
  assert set(a)>={'id','title','totalEpisodes','image','source'},a['id']
  assert a['totalEpisodes'] is None or isinstance(a['totalEpisodes'],int)
  assert os.path.exists(B+a['image']),a['image']
E=lambda s:html.escape(str(s),quote=True)
css=open(T+'style.css').read();js=open(T+'app.js').read()
data='/* ===== 작품 데이터 =====\n   원본: data/anime.json  (build.py가 이 상수를 생성해요. 직접 고쳐도 되지만, build.py를 다시 돌리면 json 내용으로 덮어써져요.)\n   주의: file://로 열면 fetch("data/anime.json")가 막혀서, 데이터를 이렇게 스크립트 안에 넣어 둬요.\n   필드: id, title, original, totalEpisodes(모르면 null), image(images/ 안의 파일), status, note, source[{label,url}], imageSource\n*/\nconst ANIME = '+json.dumps(A,ensure_ascii=False,indent=1).replace('</','<\\/')+';\n/* ===== 작품 데이터 끝 ===== */\n'
srcs=''.join(f'<li><b>{E(a["title"])}</b>: '+', '.join(f'<a href="{E(s["url"])}" rel="noreferrer">{E(s["label"])}</a>' for s in a['source'])+f'<br>이미지: <a href="{E(a["imageSource"])}" rel="noreferrer">공식 사이트 키 비주얼</a></li>' for a in A)
star='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8L3.5 9.2l5.9-.9z" fill="currentColor"/></svg>'
body=f'''<header class="bar0"><h1>ADHD를 위한 애니 보기 퀘스트</h1><button type="button" id="th" class="th" aria-label="다크 모드로" aria-pressed="false"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" fill="currentColor"/></svg></button></header>
<main>
<div class="top">
<section class="today" aria-labelledby="tqh"><h2 class="tq-h" id="tqh"><span id="todayDone" hidden>{star}</span>오늘의 퀘스트: 1화</h2><div id="todayBody"></div></section>
<div class="stats">
<div class="stat"><p class="sl">레벨</p><p class="sv">Lv <span id="lv">1</span></p><div class="xpbar" aria-hidden="true"><i id="xpBar" style="width:0%"></i></div><p class="sm"><span id="xpNow">0</span> / 100 XP</p><p class="sm">전체 <span id="xpTotal">0</span> XP</p><p class="sm">1화 10 XP, 완주 50 XP</p></div>
<div class="stat"><p class="sl">연속 시청</p><p class="sv"><span id="streak">0</span><small>일</small></p><p class="sm ink" id="streakMsg"></p><p class="sm">최고 기록 <span id="best">0</span>일 · 오늘 <span id="todayN">0</span>화</p></div>
</div></div>
<section class="sec" aria-labelledby="h-cards"><div class="sech"><h2 id="h-cards">퀘스트 카드 <span class="sl" style="font-weight:400"><span id="count">3</span>개</span></h2><button type="button" class="btn" id="addBtn" data-k="addBtn">작품 추가</button></div><div id="cards"></div>
<div id="hiddenWrap" class="sec" hidden><h3 class="fl">숨긴 작품</h3><ul id="hiddenList"></ul></div></section>
<section class="sec" aria-labelledby="h-bd"><div class="sech"><h2 id="h-bd">배지 <span class="sl" style="font-weight:400"><span id="bdCount">0</span> / 7</span></h2></div><ul id="badges"></ul></section>
<footer class="foot">
<p>진행 기록은 이 브라우저(localStorage)에만 저장돼요. 다른 기기나 브라우저와는 동기화되지 않아요.</p>
<p>총 화수는 공식 사이트 정보로 확인했어요 (2026년 10월 19일 기준). 바뀌면 카드의 “편집”에서 고칠 수 있어요.</p>
<details><summary>정보·이미지 출처</summary><ul>{srcs}</ul><p>이미지는 각 작품 공식 사이트의 키 비주얼이며, 개인 감상용으로만 써요.</p></details>
<button type="button" class="ghost" id="wipeBtn" data-ask="wipeAsk">데이터 초기화</button>
<div class="confirm" id="wipeAsk" hidden><p>진행 기록, 배지, 추가한 작품, 편집 내용이 모두 지워져요. 되돌릴 수 없어요.</p><div class="crow"><button type="button" class="danger" id="doWipe">모두 지우기</button><button type="button" class="ghost" data-nevermind>그만두기</button></div></div>
</footer>
</main>
<div class="toast" id="toast" role="status" aria-live="polite"><span id="toastMsg"></span><button type="button" id="toastUndo" hidden>되돌리기</button></div>
<dialog id="ed" aria-labelledby="edTitle"><form id="edForm" class="dl" novalidate>
<div class="dh"><h2 id="edTitle">작품 추가</h2><button type="button" class="th" id="edCancel" aria-label="닫기"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button></div>
<div class="fr" id="fTitleRow"><label for="fTitle">제목</label><input type="text" id="fTitle" maxlength="80" autocomplete="off"></div>
<div class="fr"><label for="fTotal">총 화수 (선택)</label><input type="number" id="fTotal" inputmode="numeric" min="1" max="2000" step="1"><p class="hint" id="fTotalHint"></p></div>
<div class="fr"><span class="fl">이미지 (선택)</span><div class="irow"><label class="file">파일 올리기<input type="file" id="fFile" accept="image/*"></label><button type="button" class="ghost" id="imgReset" hidden>원래 이미지로</button></div>
<p class="hint" id="imgInfo">올린 이미지는 600px 너비로 줄여서 이 브라우저에 저장해요.</p>
<div id="fUrlRow"><label for="fUrl" class="fl" style="margin-top:12px">또는 이미지 주소 (내가 고른 인터넷 주소)</label><input type="url" id="fUrl" placeholder="https://" autocomplete="off"><p class="hint">주소를 넣으면 페이지를 열 때 그 사이트에서 이미지를 불러와요.</p></div>
<div id="imgPrev"></div></div>
<p class="err" id="edErr" role="alert"></p>
<div class="dact"><button type="submit" class="primary">저장</button></div>
<div class="dz">
<div id="dangerProg"><div class="irow"><button type="button" class="ghost" data-ask="progAsk">이 작품 진행 초기화</button></div><div class="confirm" id="progAsk" hidden><p>이 작품에서 체크한 화가 모두 풀려요. 배지는 그대로 남아요.</p><div class="crow"><button type="button" class="danger" id="doProg">초기화</button><button type="button" class="ghost" data-nevermind>그만두기</button></div></div></div>
<div id="dangerBuilt" class="fr"><div class="irow"><button type="button" class="ghost" data-ask="hideAsk">이 작품 숨기기</button></div><div class="confirm" id="hideAsk" hidden><p>목록에서 숨겨요. 진행 기록은 남아 있고, 아래 “숨긴 작품”에서 다시 보이게 할 수 있어요.</p><div class="crow"><button type="button" class="danger" id="doHide">숨기기</button><button type="button" class="ghost" data-nevermind>그만두기</button></div></div></div>
<div id="dangerCustom" class="fr"><div class="irow"><button type="button" class="ghost" data-ask="delAsk">이 작품 삭제</button></div><div class="confirm" id="delAsk" hidden><p>이 작품과 진행 기록이 지워져요. 되돌릴 수 없어요.</p><div class="crow"><button type="button" class="danger" id="doDelete">삭제</button><button type="button" class="ghost" data-nevermind>그만두기</button></div></div></div>
</div></form></dialog>'''
chars=set(html.unescape(re.sub(r'<[^>]+>',' ',body))+json.dumps(A,ensure_ascii=False)+js+'0123456789')
chars=''.join(sorted(c for c in chars if ord(c)>=32))
open(T+'chars.txt','w').write(chars)
def sub(src,name):
  out=T+name+'.woff2';subprocess.run(['pyftsubset',src,'--text-file='+T+'chars.txt','--flavor=woff2','--output-file='+out,'--layout-features=*'],check=True)
  return base64.b64encode(open(out,'rb').read()).decode()
P='/usr/share/fonts/truetype/sand-box/custom/Pretendard/'
f4=sub(P+'Pretendard-Regular.otf','p400');f7=sub(P+'Pretendard-Bold.otf','p700')
fonts=f'@font-face{{font-family:"AQ Sans";font-weight:400;font-display:swap;src:url(data:font/woff2;base64,{f4}) format("woff2")}}@font-face{{font-family:"AQ Sans";font-weight:700;font-display:swap;src:url(data:font/woff2;base64,{f7}) format("woff2")}}'
page=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ADHD를 위한 애니 보기 퀘스트</title><meta name="color-scheme" content="light dark">
<script>try{{var t=localStorage.getItem('aq-theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<style>{fonts}
{css}</style></head><body>
{body}
<script>
{data}
{js}</script></body></html>'''
open(B+'index.html','w').write(page)
print(len(page.encode()),'bytes',len(f4),len(f7))
