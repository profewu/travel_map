#!/usr/bin/env python3
"""A/B query Booking.com with stock Playwright vs CloakBrowser for Hokkaido itinerary.

Outputs JSON per run and a combined HTML report.
"""
import argparse
import asyncio
import html
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlencode

BASE = Path('/home/profe/hotel-research')
OUT = BASE / 'data' / 'booking_ab'
REPORTS = BASE / 'reports'
OUT.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

# Interpreting the supplied itinerary as overnight lodging locations.
ITINERARY = [
    {'date': '2026-06-25', 'weekday': 'Thu', 'label': '6/25 抵達新千歲，惠庭緩衝', 'location_zh': '惠庭', 'search': 'Eniwa, Hokkaido, Japan', 'note': '抵達新千歲後在惠庭緩衝'},
    {'date': '2026-06-26', 'weekday': 'Fri', 'label': '6/26 惠庭親子活動、支笏湖，進登別', 'location_zh': '登別', 'search': 'Noboribetsu, Hokkaido, Japan', 'note': '經支笏湖後入住登別'},
    {'date': '2026-06-27', 'weekday': 'Sat', 'label': '6/27 登別、白老、室蘭，夜宿洞爺湖', 'location_zh': '洞爺湖', 'search': 'Lake Toya, Hokkaido, Japan', 'note': '夜宿洞爺湖'},
    {'date': '2026-06-28', 'weekday': 'Sun', 'label': '6/28 洞爺湖轉場小樽', 'location_zh': '小樽', 'search': 'Otaru, Hokkaido, Japan', 'note': '洞爺湖轉場小樽'},
    {'date': '2026-06-29', 'weekday': 'Mon', 'label': '6/29 鱗友朝市，小樽到札幌', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '小樽到札幌'},
    {'date': '2026-06-30', 'weekday': 'Tue', 'label': '6/30 札幌購物與親子緩衝', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '札幌購物與親子緩衝'},
    {'date': '2026-07-01', 'weekday': 'Wed', 'label': '7/1 札幌地下街、薄野與藻岩山', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '札幌地下街、薄野與藻岩山'},
    {'date': '2026-07-02', 'weekday': 'Thu', 'label': '7/2 札幌自由日與機場巴士確認', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '札幌自由日與機場巴士確認'},
]

NEXT_DAY = {
    '2026-06-25': '2026-06-26',
    '2026-06-26': '2026-06-27',
    '2026-06-27': '2026-06-28',
    '2026-06-28': '2026-06-29',
    '2026-06-29': '2026-06-30',
    '2026-06-30': '2026-07-01',
    '2026-07-01': '2026-07-02',
    '2026-07-02': '2026-07-03',
}


OCCUPANCIES = [
    {
        'key': 'family_1room',
        'label': '3大1小（10歲）｜1間房（尋找4人房/家庭房）',
        'group_adults': '3',
        'group_children': '1',
        'children_age': '10',
        'no_rooms': '1',
    },
    {
        'key': 'family_2rooms',
        'label': '3大1小（10歲）｜2間房（尋找2間房組合）',
        'group_adults': '3',
        'group_children': '1',
        'children_age': '10',
        'no_rooms': '2',
    },
]


def booking_url(search: str, checkin: str, checkout: str, occupancy: dict) -> str:
    query = {
        'ss': search,
        'checkin': checkin,
        'checkout': checkout,
        'group_adults': occupancy['group_adults'],
        'no_rooms': occupancy['no_rooms'],
        'group_children': occupancy['group_children'],
        'age': occupancy['children_age'],
        'selected_currency': 'JPY',
        'lang': 'en-us',
        'order': 'popularity',
    }
    return 'https://www.booking.com/searchresults.html?' + urlencode(query)


async def run_stock(headless=True):
    from playwright.async_api import async_playwright
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless)
    context = await browser.new_context(locale='en-US', timezone_id='Asia/Tokyo', viewport={'width': 1365, 'height': 900})
    page = await context.new_page()
    return pw, browser, page


async def run_cloak(headless=True):
    from cloakbrowser import launch_async
    browser = await launch_async(headless=headless, locale='en-US', timezone='Asia/Tokyo')
    page = await browser.new_page(viewport={'width': 1365, 'height': 900})
    return None, browser, page


async def accept_cookies(page):
    for sel in ['button:has-text("Accept")', 'button:has-text("Accept all")', 'button:has-text("I agree")', 'button:has-text("OK")']:
        try:
            loc = page.locator(sel).first
            if await loc.count() and await loc.is_visible(timeout=1000):
                await loc.click(timeout=2500)
                await page.wait_for_timeout(700)
                return sel
        except Exception:
            pass
    return None


async def extract_hotels(page, limit=5):
    cards = page.locator('[data-testid="property-card"]')
    n = await cards.count()
    rows = []
    for i in range(min(n, 20)):
        card = cards.nth(i)
        async def text(sel):
            try:
                loc = card.locator(sel).first
                if await loc.count():
                    return re.sub(r'\s+', ' ', (await loc.inner_text(timeout=1200))).strip()
            except Exception:
                pass
            return ''
        name = await text('[data-testid="title"]')
        price = await text('[data-testid="price-and-discounted-price"]')
        score = await text('[data-testid="review-score"]')
        address = await text('[data-testid="address"]')
        distance = await text('[data-testid="distance"]')
        link = ''
        try:
            a = card.locator('a[href*="/hotel/"]').first
            if await a.count():
                link = await a.get_attribute('href') or ''
        except Exception:
            pass
        if name:
            rows.append({'name': name, 'price': price, 'score': score, 'address': address, 'distance': distance, 'link': link})
        if len(rows) >= limit:
            break
    return rows, n


async def query_one(mode, item, occupancy, headed=False):
    pw = browser = page = None
    started = time.time()
    url = booking_url(item['search'], item['date'], NEXT_DAY[item['date']], occupancy)
    result = {
        **item,
        'mode': mode,
        'occupancy_key': occupancy['key'],
        'occupancy_label': occupancy['label'],
        'occupancy': occupancy,
        'checkout': NEXT_DAY[item['date']],
        'url_requested': url,
        'hotels': [],
        'errors': [],
    }
    try:
        if mode == 'playwright':
            pw, browser, page = await run_stock(headless=not headed)
        else:
            pw, browser, page = await run_cloak(headless=not headed)
        resp = await page.goto(url, wait_until='domcontentloaded', timeout=90000)
        result['response_status'] = resp.status if resp else None
        result['cookie_clicked'] = await accept_cookies(page)
        try:
            await page.wait_for_load_state('networkidle', timeout=7000)
        except Exception:
            result['errors'].append('networkidle_timeout')
        try:
            await page.locator('[data-testid="property-card"]').first.wait_for(timeout=9000)
        except Exception:
            result['errors'].append('property_card_timeout')
        await page.wait_for_timeout(1000)
        result['title'] = await page.title()
        result['final_url'] = page.url
        nav = await page.evaluate('''() => ({userAgent:navigator.userAgent, webdriver:navigator.webdriver, platform:navigator.platform, language:navigator.language, timezone:Intl.DateTimeFormat().resolvedOptions().timeZone})''')
        result['navigator'] = nav
        body = await page.locator('body').inner_text(timeout=10000)
        low = body.lower()
        result['body_text_len'] = len(body)
        result['block_signals'] = [s for s in ['captcha','verify you are human','access denied','blocked','unusual traffic','robot','sorry'] if s in low]
        hotels, count = await extract_hotels(page, 5)
        result['property_card_count'] = count
        result['hotels'] = hotels
        shot = OUT / f"{mode}_{occupancy['key']}_{item['date']}_{re.sub('[^A-Za-z0-9]+','_',item['search'])}.png"
        await page.screenshot(path=str(shot), full_page=False)
        result['screenshot'] = str(shot)
    except Exception as e:
        result['fatal_error'] = repr(e)
    finally:
        result['elapsed_sec'] = round(time.time() - started, 2)
        try:
            if browser:
                await browser.close()
        except Exception:
            pass
        try:
            if pw:
                await pw.stop()
        except Exception:
            pass
    return result


def render_html(results_by_mode):
    generated = time.strftime('%Y-%m-%d %H:%M:%S %Z')
    css = """
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:24px;color:#172033;background:#f6f7fb}
    h1,h2,h3,h4{color:#101828}.meta{color:#667085}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:white;border:1px solid #e4e7ec;border-radius:14px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.05);margin:14px 0}.mode{font-weight:700}.ok{color:#067647}.bad{color:#b42318}.warn{color:#b54708}.hotel{border-top:1px solid #eaecf0;padding:10px 0}.hotel:first-child{border-top:0}.price{font-weight:700;color:#175cd3}.small{font-size:12px;color:#667085}.pill{display:inline-block;border-radius:999px;padding:2px 8px;background:#eef4ff;color:#3538cd;font-size:12px;margin-left:6px}.occ{background:#fff7ed;color:#b54708}a{color:#175cd3}pre{white-space:pre-wrap;background:#101828;color:#f2f4f7;padding:10px;border-radius:8px;overflow:auto}@media(max-width:900px){.grid{grid-template-columns:1fr}}
    """
    parts = [f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>北海道行程飯店 A/B 查詢：Playwright vs CloakBrowser</title><style>{css}</style></head><body>",
             "<h1>北海道行程飯店 A/B 查詢：Playwright vs CloakBrowser</h1>",
             f"<p class='meta'>來源網站：Booking.com｜每晚條件：3 adults + 1 child age 10；比較 1間房 vs 2間房；JPY、en-US、Asia/Tokyo｜產生時間：{html.escape(generated)}</p>",
             "<p class='meta'>說明：以下把行程解讀為每晚住宿地點；7/3 為返程日，未列住宿。Playwright 與 CloakBrowser 使用相同 URL/日期/人數/房數條件查詢。</p>"]
    for item in ITINERARY:
        parts.append(f"<section class='card'><h2>{html.escape(item['label'])} <span class='pill'>{html.escape(item['location_zh'])}</span></h2>")
        parts.append(f"<p class='meta'>住宿搜尋：{html.escape(item['search'])}｜入住：{item['date']}｜退房：{NEXT_DAY[item['date']]}｜備註：{html.escape(item['note'])}</p>")
        for occupancy in OCCUPANCIES:
            parts.append(f"<h3><span class='pill occ'>{html.escape(occupancy['label'])}</span></h3><div class='grid'>")
            for mode in ['playwright','cloak']:
                r = next((x for x in results_by_mode.get(mode, []) if x['date'] == item['date'] and x.get('occupancy_key') == occupancy['key']), None)
                parts.append("<div class='card'>")
                parts.append(f"<h4>{'Stock Playwright' if mode=='playwright' else 'CloakBrowser'}</h4>")
                if not r:
                    parts.append("<p class='bad'>未執行</p></div>")
                    continue
                hotels = r.get('hotels') or []
                status_class = 'ok' if hotels else 'bad'
                parts.append(f"<p class='{status_class}'>抓到飯店：{len(hotels)} / property cards：{r.get('property_card_count',0)}</p>")
                parts.append(f"<p class='small'>HTTP: {r.get('response_status')}｜elapsed: {r.get('elapsed_sec')}s｜title: {html.escape(str(r.get('title','')))}</p>")
                nav = r.get('navigator') or {}
                parts.append(f"<p class='small'>webdriver={html.escape(str(nav.get('webdriver')))}｜platform={html.escape(str(nav.get('platform')))}｜UA={html.escape(str(nav.get('userAgent','')))}</p>")
                if r.get('errors') or r.get('block_signals') or r.get('fatal_error'):
                    parts.append(f"<p class='warn small'>errors={html.escape(json.dumps(r.get('errors',[]), ensure_ascii=False))} block={html.escape(json.dumps(r.get('block_signals',[]), ensure_ascii=False))} fatal={html.escape(str(r.get('fatal_error','')))}</p>")
                if not hotels:
                    parts.append("<p class='bad'>此模式未取得有效飯店清單。</p>")
                else:
                    for idx,h in enumerate(hotels,1):
                        link = h.get('link') or ''
                        name = html.escape(h.get('name',''))
                        if link:
                            name = f"<a href='{html.escape(link)}' target='_blank' rel='noreferrer'>{name}</a>"
                        parts.append("<div class='hotel'>")
                        parts.append(f"<div><strong>{idx}. {name}</strong></div>")
                        parts.append(f"<div class='price'>{html.escape(h.get('price') or '價格未顯示')}</div>")
                        extra = '｜'.join([x for x in [h.get('score',''), h.get('address',''), h.get('distance','')] if x])
                        if extra:
                            parts.append(f"<div class='small'>{html.escape(extra)}</div>")
                        parts.append("</div>")
                if r.get('screenshot'):
                    parts.append(f"<p class='small'>screenshot: {html.escape(r['screenshot'])}</p>")
                parts.append("</div>")
            parts.append("</div>")
        parts.append("</section>")
    parts.append("</body></html>")
    return '\n'.join(parts)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['playwright','cloak','both'], default='both')
    ap.add_argument('--headed', action='store_true')
    args = ap.parse_args()
    modes = ['playwright','cloak'] if args.mode == 'both' else [args.mode]
    all_results = {}
    for mode in modes:
        mode_results = []
        for item in ITINERARY:
            for occupancy in OCCUPANCIES:
                print(f"RUN {mode} {occupancy['key']} {item['date']} {item['search']}", flush=True)
                res = await query_one(mode, item, occupancy, headed=args.headed)
                mode_results.append(res)
                (OUT / f"{mode}_{occupancy['key']}_{item['date']}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
                # Gentle pacing.
                await asyncio.sleep(2.0 if mode == 'cloak' else 0.5)
        all_results[mode] = mode_results
        (OUT / f"{mode}_all.json").write_text(json.dumps(mode_results, ensure_ascii=False, indent=2), encoding='utf-8')
    # If only one mode, load existing other mode if present for combined report.
    for mode in ['playwright','cloak']:
        if mode not in all_results and (OUT / f"{mode}_all.json").exists():
            all_results[mode] = json.loads((OUT / f"{mode}_all.json").read_text(encoding='utf-8'))
    html_text = render_html(all_results)
    report = REPORTS / 'hokkaido_hotels_booking_playwright_vs_cloak.html'
    report.write_text(html_text, encoding='utf-8')
    print(f"REPORT {report}")

if __name__ == '__main__':
    asyncio.run(main())
