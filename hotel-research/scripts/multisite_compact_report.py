#!/usr/bin/env python3
import asyncio, html, json, re, time
from pathlib import Path
from urllib.parse import urlencode
from cloakbrowser import launch_async

BASE=Path('/home/profe/hotel-research')
BOOKING_DATA=BASE/'data/booking_ab/cloak_all.json'
OUT=BASE/'data/multisite'
REPORT=BASE/'reports/hokkaido_hotels_3sites_compact.html'
OUT.mkdir(parents=True, exist_ok=True); REPORT.parent.mkdir(parents=True, exist_ok=True)

ITINERARY=[
 {'date':'2026-06-25','checkout':'2026-06-26','label':'6/25 抵達新千歲，惠庭緩衝','location_zh':'惠庭','search':'Eniwa, Hokkaido, Japan','note':'抵達新千歲後在惠庭緩衝'},
 {'date':'2026-06-26','checkout':'2026-06-27','label':'6/26 惠庭親子活動、支笏湖，進登別','location_zh':'登別','search':'Noboribetsu, Hokkaido, Japan','note':'經支笏湖後入住登別'},
 {'date':'2026-06-27','checkout':'2026-06-28','label':'6/27 登別、白老、室蘭，夜宿洞爺湖','location_zh':'洞爺湖','search':'Lake Toya, Hokkaido, Japan','note':'夜宿洞爺湖'},
 {'date':'2026-06-28','checkout':'2026-06-29','label':'6/28 洞爺湖轉場小樽','location_zh':'小樽','search':'Otaru, Hokkaido, Japan','note':'洞爺湖轉場小樽'},
 {'date':'2026-06-29','checkout':'2026-06-30','label':'6/29 鱗友朝市，小樽到札幌','location_zh':'札幌','search':'Sapporo, Hokkaido, Japan','note':'小樽到札幌'},
 {'date':'2026-06-30','checkout':'2026-07-01','label':'6/30 札幌購物與親子緩衝','location_zh':'札幌','search':'Sapporo, Hokkaido, Japan','note':'札幌購物與親子緩衝'},
 {'date':'2026-07-01','checkout':'2026-07-02','label':'7/1 札幌地下街、薄野與藻岩山','location_zh':'札幌','search':'Sapporo, Hokkaido, Japan','note':'札幌地下街、薄野與藻岩山'},
 {'date':'2026-07-02','checkout':'2026-07-03','label':'7/2 札幌自由日與機場巴士確認','location_zh':'札幌','search':'Sapporo, Hokkaido, Japan','note':'札幌自由日與機場巴士確認'},
]
OCCS=[
 {'key':'family_1room','label':'3大1小(10歲)｜1間房','rooms':'1'},
 {'key':'family_2rooms','label':'3大1小(10歲)｜2間房','rooms':'2'},
]

def price_num(s):
 m=re.search(r'([0-9][0-9,]*(?:\.\d+)?)', s or '')
 return float(m.group(1).replace(',','')) if m else None

def currency(s):
 s=s or ''
 if '¥' in s or 'JPY' in s: return 'JPY'
 if 'NT$' in s or 'TWD' in s: return 'TWD'
 if '$' in s or 'USD' in s: return 'USD'
 return ''

def score_num(s):
 nums=re.findall(r'\d+(?:\.\d+)?', s or '')
 return nums[0] if nums else ''

def expedia_url(site, dest, checkin, checkout, rooms):
 domain='www.expedia.com' if site=='Expedia' else 'www.hotels.com'
 return f'https://{domain}/Hotel-Search?'+urlencode({
  'destination':dest,'startDate':checkin,'endDate':checkout,'rooms':rooms,'adults':'3','children':'1_10','sort':'PRICE_LOW_TO_HIGH','useRewards':'false','currency':'JPY','locale':'en_US'
 })

def extract_expedia_like(text, site, url, limit=5):
 # Expedia/Hotels.com SSR text is structured around "Photo gallery for ...".
 pieces=re.split(r'Photo gallery for ', text)
 rows=[]
 for piece in pieces[1:]:
  lines=[x.strip() for x in piece.splitlines() if x.strip()]
  if not lines: continue
  name=lines[0]
  if len(name)>160 or any(bad in name.lower() for bad in ['static map','sort & filter']): continue
  chunk='\n'.join(lines[:35])
  # Prefer total price if visible; otherwise nightly.
  pm=re.search(r'((?:NT\$|\$|¥|JPY\s*)\s?[0-9][0-9,]*(?:\.\d+)?)\s+total', chunk, re.I)
  if not pm: pm=re.search(r'((?:NT\$|\$|¥|JPY\s*)\s?[0-9][0-9,]*(?:\.\d+)?)\s+nightly', chunk, re.I)
  if not pm: pm=re.search(r'((?:NT\$|\$|¥|JPY\s*)\s?[0-9][0-9,]*(?:\.\d+)?)', chunk, re.I)
  price=pm.group(1).replace('\xa0',' ') if pm else ''
  sm=re.search(r'(\d+(?:\.\d+)?)\s+out of 10|^(\d+(?:\.\d+)?)$', chunk, re.M)
  score=(sm.group(1) or sm.group(2)) if sm else ''
  area=''
  for line in lines[1:8]:
   if any(tok in line for tok in ['km from','Eniwa','Sapporo','Otaru','Chitose','Noboribetsu','Toya','Lake']):
    area=line; break
  if name and price:
   rows.append({'site':site,'name':name,'price':price,'price_num':price_num(price),'currency':currency(price),'score':score,'distance':area,'link':url})
  if len(rows)>=limit: break
 return rows

async def query_site(page, site, item, occ):
 url=expedia_url(site, item['search'], item['date'], item['checkout'], occ['rooms'])
 res={'site':site,'date':item['date'],'checkout':item['checkout'],'search':item['search'],'occupancy_key':occ['key'],'occupancy_label':occ['label'],'url':url,'hotels':[],'errors':[]}
 try:
  resp=await page.goto(url, wait_until='domcontentloaded', timeout=90000)
  res['status']=resp.status if resp else None
  await page.wait_for_timeout(9000)
  res['title']=await page.title(); res['final_url']=page.url
  text=await page.locator('body').inner_text(timeout=12000)
  res['body_len']=len(text)
  res['hotels']=extract_expedia_like(text, site, res['final_url'], 5)
  shot=OUT/f"{site.lower()}_{occ['key']}_{item['date']}.png"
  await page.screenshot(path=str(shot), full_page=False)
  res['screenshot']=str(shot)
 except Exception as e:
  res['errors'].append(repr(e))
 return res

def load_booking():
 arr=json.loads(BOOKING_DATA.read_text(encoding='utf-8'))
 out=[]
 for r in arr:
  rows=[]
  for h in (r.get('hotels') or [])[:5]:
   rows.append({'site':'Booking.com','name':h.get('name',''),'price':h.get('price',''),'price_num':price_num(h.get('price','')),'currency':currency(h.get('price','')),'score':score_num(h.get('score','')),'distance':h.get('distance',''),'link':h.get('link','')})
  out.append({'site':'Booking.com','date':r['date'],'checkout':r.get('checkout'),'search':r['search'],'occupancy_key':r.get('occupancy_key'),'occupancy_label':r.get('occupancy_label'),'url':r.get('url_requested'),'hotels':rows})
 return out

async def run_new_sites():
 results=[]
 browser=await launch_async(headless=True, locale='en-US', timezone='Asia/Tokyo')
 page=await browser.new_page(viewport={'width':1365,'height':900})
 for site in ['Expedia','Hotels.com']:
  for item in ITINERARY:
   for occ in OCCS:
    print('RUN',site,occ['key'],item['date'],item['search'],flush=True)
    res=await query_site(page,site,item,occ)
    results.append(res)
    (OUT/f"{site.lower().replace('.','')}_{occ['key']}_{item['date']}.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
    await asyncio.sleep(1.5)
 await browser.close()
 (OUT/'expedia_hotels_all.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 return results

def esc(x): return html.escape(str(x or ''))

def render(all_results):
 by={}
 for r in all_results:
  by.setdefault((r['date'],r['occupancy_key']),[]).append(r)
 generated=time.strftime('%Y-%m-%d %H:%M:%S %Z')
 css="""
 body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:14px;background:#f6f7fb;color:#172033;font-size:13px}h1{font-size:22px}h2{font-size:17px;margin:10px 0 4px}h3{font-size:14px;margin:8px 0}.meta{color:#667085;line-height:1.35}.day{background:#fff;border:1px solid #e4e7ec;border-radius:12px;padding:10px;margin:10px 0}.occ{background:#fff7ed;border-radius:10px;padding:8px;margin:8px 0}.site{margin:6px 0 10px}.pill{display:inline-block;border-radius:999px;padding:2px 7px;background:#eef4ff;color:#3538cd;font-size:11px}.sitepill{background:#ecfdf3;color:#067647}.warn{background:#fffaeb;color:#b54708}table{width:100%;border-collapse:collapse;background:#fff}th,td{border-bottom:1px solid #eaecf0;padding:4px 6px;text-align:left;vertical-align:top}th{font-size:12px;color:#475467;background:#f9fafb}.rank{width:32px;color:#667085}.price{white-space:nowrap;font-weight:700;color:#175cd3}.small{font-size:11px;color:#667085}.hotel{min-width:220px}a{color:#175cd3;text-decoration:none}a:hover{text-decoration:underline}.grid{display:grid;grid-template-columns:1fr;gap:8px}@media(min-width:1200px){.grid{grid-template-columns:1fr 1fr 1fr}}@media(max-width:900px){table{display:block;overflow-x:auto}body{margin:8px}}
 """
 parts=[f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>北海道飯店三網站比較</title><style>{css}</style></head><body>",
        "<h1>北海道飯店三網站比較（緊湊版）</h1>",
        f"<p class='meta'>網站：Booking.com、Expedia、Hotels.com｜工具：CloakBrowser｜條件：3大1小(10歲)，1間房與2間房｜產生：{esc(generated)}</p>",
        "<p class='meta'>已移除：3星級 / 高樓層 / 備註欄。價位排名為各網站在同一日期與房型策略下依擷取價格數字排序；各網站顯示幣別可能不同，請以連結頁最終價格為準。</p>"]
 for item in ITINERARY:
  parts.append(f"<section class='day'><h2>{esc(item['label'])} <span class='pill'>{esc(item['location_zh'])}</span></h2><div class='meta'>搜尋：{esc(item['search'])}｜入住 {item['date']} → 退房 {item['checkout']}｜{esc(item['note'])}</div>")
  for occ in OCCS:
   parts.append(f"<div class='occ'><h3>{esc(occ['label'])}</h3><div class='grid'>")
   for site in ['Booking.com','Expedia','Hotels.com']:
    r=next((x for x in by.get((item['date'],occ['key']),[]) if x['site']==site), None)
    hotels=(r or {}).get('hotels') or []
    hotels=sorted(hotels, key=lambda h: (h.get('price_num') is None, h.get('price_num') or 10**12))[:5]
    parts.append(f"<div class='site'><div><span class='pill sitepill'>{esc(site)}</span> <span class='small'>{len(hotels)}筆</span></div>")
    if not hotels:
     err=esc(json.dumps((r or {}).get('errors',[]),ensure_ascii=False)) if r else '未查詢'
     parts.append(f"<div class='small warn'>未取得結果 {err}</div></div>"); continue
    parts.append("<table><thead><tr><th class='rank'>#</th><th class='hotel'>飯店</th><th>價位排名/價格</th><th>評分/距離</th></tr></thead><tbody>")
    for i,h in enumerate(hotels,1):
     name=esc(h.get('name'))
     if h.get('link'): name=f"<a href='{esc(h.get('link'))}' target='_blank' rel='noreferrer'>{name}</a>"
     detail=' / '.join([x for x in [h.get('score'),h.get('distance')] if x])
     parts.append(f"<tr><td class='rank'>{i}</td><td class='hotel'>{name}</td><td class='price'>{esc(h.get('price') or '未顯示')}</td><td class='small'>{esc(detail)}</td></tr>")
    parts.append("</tbody></table></div>")
   parts.append("</div></div>")
  parts.append("</section>")
 parts.append("</body></html>")
 REPORT.write_text('\n'.join(parts),encoding='utf-8')

def main_sync(new_results):
 booking=load_booking()
 all_results=booking+new_results
 (OUT/'combined_3sites.json').write_text(json.dumps(all_results,ensure_ascii=False,indent=2),encoding='utf-8')
 render(all_results)
 print('REPORT',REPORT)
 print('site_runs',len(all_results),'hotel_rows',sum(len(r.get('hotels') or []) for r in all_results))

async def main():
 cache=OUT/'expedia_hotels_all.json'
 if cache.exists():
  new=json.loads(cache.read_text(encoding='utf-8'))
 else:
  new=await run_new_sites()
 main_sync(new)

if __name__=='__main__': asyncio.run(main())
