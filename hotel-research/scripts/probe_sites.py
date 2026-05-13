#!/usr/bin/env python3
import asyncio, json, re, time
from pathlib import Path
from urllib.parse import quote, urlencode
from cloakbrowser import launch_async

OUT=Path('/home/profe/hotel-research/data/site_probe'); OUT.mkdir(parents=True, exist_ok=True)
CHECKIN='2026-06-25'; CHECKOUT='2026-06-26'; DEST='Eniwa, Hokkaido, Japan'
URLS={
 'agoda': 'https://www.agoda.com/search?'+urlencode({'city':'','textToSearch':DEST,'checkIn':CHECKIN,'checkOut':CHECKOUT,'rooms':'1','adults':'3','children':'1','childAges':'10','currencyCode':'JPY'}),
 'trivago': 'https://www.trivago.com/en-US/srl/hotels-'+quote(DEST.lower().replace(',','').replace(' ','-'))+'?'+urlencode({'search':'200-212','arrivalDate':CHECKIN,'departureDate':CHECKOUT,'rooms':'1','adults':'3','children':'1','childrenAge':'10','currency':'JPY'}),
}
SELECTORS={
 'agoda': ['[data-selenium="hotel-item"]','[data-element-name="property-card"]','li.PropertyCard','div.PropertyCard','[class*=PropertyCard]'],
 'trivago': ['[data-testid="accommodation-list-element"]','li[data-testid*=item]','[data-testid*=hotel-card]','article','[class*=AccommodationList] li'],
}
async def main():
    browser=await launch_async(headless=True, locale='en-US', timezone='Asia/Tokyo')
    page=await browser.new_page(viewport={'width':1365,'height':900})
    results={}
    for site,url in URLS.items():
        print('OPEN', site, url, flush=True)
        r={'site':site,'url':url,'errors':[]}
        try:
            resp=await page.goto(url, wait_until='domcontentloaded', timeout=90000)
            r['status']=resp.status if resp else None
            await page.wait_for_timeout(12000)
            r['title']=await page.title(); r['final_url']=page.url
            body=await page.locator('body').inner_text(timeout=10000)
            r['body_len']=len(body); r['body_sample']=body[:2000]
            r['yen_snips']=re.findall(r'(?:¥|JPY)\s?[0-9][0-9,]+', body)[:30]
            counts={}
            for sel in SELECTORS[site]:
                try: counts[sel]=await page.locator(sel).count()
                except Exception as e: counts[sel]=repr(e)
            r['selector_counts']=counts
            await page.screenshot(path=str(OUT/f'{site}.png'), full_page=False)
            (OUT/f'{site}.html').write_text(await page.content(), encoding='utf-8')
        except Exception as e:
            r['fatal']=repr(e)
        results[site]=r
    await browser.close()
    (OUT/'probe.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False, indent=2)[:6000])
asyncio.run(main())
