#!/usr/bin/env python3
import asyncio,json,re
from pathlib import Path
from cloakbrowser import launch_async
OUT=Path('/home/profe/hotel-research/data/trivago_ui'); OUT.mkdir(parents=True,exist_ok=True)
async def main():
 b=await launch_async(headless=True,locale='en-US',timezone='Asia/Tokyo')
 p=await b.new_page(viewport={'width':1365,'height':900})
 r={}
 try:
  await p.goto('https://www.trivago.com/en-US',wait_until='domcontentloaded',timeout=90000)
  await p.wait_for_timeout(3000)
  inp=p.locator('[data-testid="search-form-input"]').first
  await inp.fill('Eniwa, Hokkaido, Japan')
  await p.wait_for_timeout(2000)
  # dump suggestions text
  r['suggestions']=await p.locator('body').inner_text(timeout=10000)
  await p.keyboard.press('ArrowDown')
  await p.keyboard.press('Enter')
  await p.wait_for_timeout(2000)
  # maybe click search
  for sel in ['button[type="submit"]','button:has-text("Search")','button[data-testid*="search"]']:
   try:
    if await p.locator(sel).count():
     await p.locator(sel).first.click(timeout=2000); break
   except Exception: pass
  await p.wait_for_timeout(10000)
  r['title']=await p.title(); r['url']=p.url
  txt=await p.locator('body').inner_text(timeout=10000)
  r['text']=txt[:5000]; r['yen']=re.findall(r'(?:¥|JPY|\$|NT\$)\s?[0-9][0-9,]+',txt)[:30]
  r['cards']=await p.locator('[data-testid="accommodation-list-element"]').count()
  await p.screenshot(path=str(OUT/'trivago_ui.png'), full_page=False)
  (OUT/'trivago_ui.html').write_text(await p.content(),encoding='utf-8')
 except Exception as e: r['fatal']=repr(e)
 await b.close()
 print(json.dumps(r,ensure_ascii=False,indent=2)[:8000])
 (OUT/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
asyncio.run(main())
