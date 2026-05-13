#!/usr/bin/env python3
import asyncio,json,re
from pathlib import Path
from urllib.parse import urlencode, quote
from cloakbrowser import launch_async
OUT=Path('/home/profe/hotel-research/data/site_probe2'); OUT.mkdir(parents=True,exist_ok=True)
DESTS={'Eniwa':'Eniwa, Hokkaido, Japan','Noboribetsu':'Noboribetsu, Hokkaido, Japan','Otaru':'Otaru, Hokkaido, Japan','Sapporo':'Sapporo, Hokkaido, Japan'}
urls={
 'trip_search':'https://www.trip.com/hotels/list?'+urlencode({'city':'35766','checkin':'2026-06-25','checkout':'2026-06-26','adults':'3','children':'1','ages':'10','rooms':'1','searchword':'Eniwa'}),
 'expedia':'https://www.expedia.com/Hotel-Search?'+urlencode({'destination':'Eniwa, Hokkaido, Japan','startDate':'2026-06-25','endDate':'2026-06-26','rooms':'1','adults':'3','children':'1_10','sort':'RECOMMENDED'}),
 'hotels':'https://www.hotels.com/Hotel-Search?'+urlencode({'destination':'Eniwa, Hokkaido, Japan','startDate':'2026-06-25','endDate':'2026-06-26','rooms':'1','adults':'3','children':'1_10','sort':'RECOMMENDED'}),
 'travelko':'https://www.tour.ne.jp/j_hotel/list/?'+urlencode({'keyword':'Eniwa','checkin':'2026-06-25','checkout':'2026-06-26','adult':'3','child':'1'}),
}
async def main():
 b=await launch_async(headless=True,locale='en-US',timezone='Asia/Tokyo')
 p=await b.new_page(viewport={'width':1365,'height':900})
 res={}
 for site,url in urls.items():
  print('OPEN',site,url,flush=True)
  r={'url':url}
  try:
   resp=await p.goto(url,wait_until='domcontentloaded',timeout=90000); r['status']=resp.status if resp else None
   await p.wait_for_timeout(12000)
   r['title']=await p.title(); r['final_url']=p.url
   txt=await p.locator('body').inner_text(timeout=10000)
   r['len']=len(txt); r['sample']=txt[:3000]
   r['yen']=re.findall(r'(?:¥|JPY|￥|NT\$|TWD|US\$|\$)\s?[0-9][0-9,]+(?:\.\d+)?',txt)[:30]
   # all possible card-ish counts
   sels=['[data-stid="property-listing"]','[data-testid="property-card"]','[class*=hotel]','[class*=Hotel]','[class*=property]','[class*=Property]','li','article']
   r['counts']={}
   for s in sels:
    try:r['counts'][s]=await p.locator(s).count()
    except Exception as e:r['counts'][s]=repr(e)
   await p.screenshot(path=str(OUT/f'{site}.png'),full_page=False)
   (OUT/f'{site}.html').write_text(await p.content(),encoding='utf-8')
  except Exception as e:r['fatal']=repr(e)
  res[site]=r
 await b.close()
 (OUT/'probe.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(res,ensure_ascii=False,indent=2)[:10000])
asyncio.run(main())
