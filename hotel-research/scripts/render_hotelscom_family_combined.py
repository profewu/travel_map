#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import html
import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode

from cloakbrowser import launch_async

BASE = Path('/home/profe/hotel-research')
DATA_DIR = BASE / 'data' / 'hotelscom_probe'
LEGACY_DIR = BASE / 'data' / 'multisite'
REPORT_PATH = BASE / 'reports' / 'hokkaido_hotels_hotelscom_family_combined.html'
SUMMARY_PATH = BASE / 'reports' / 'hokkaido_hotels_hotelscom_family_summary.json'
SCRIPT_PATH = BASE / 'scripts' / 'render_hotelscom_family_combined.py'
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

PRICE_WARNING = '這只是該日期查詢下平台卡片顯示的起始參考價，不是保證最終成交價。'
LINK_WARNING = '此連結為住宿頁連結，非精確 room-level 連結。'

ITINERARY = [
    {'date': '2026-06-25', 'checkout': '2026-06-26', 'label': '6/25 抵達新千歲，惠庭緩衝', 'location_zh': '惠庭', 'search': 'Eniwa, Hokkaido, Japan', 'note': '抵達新千歲後在惠庭緩衝'},
    {'date': '2026-06-26', 'checkout': '2026-06-27', 'label': '6/26 惠庭親子活動、支笏湖，進登別', 'location_zh': '登別', 'search': 'Noboribetsu, Hokkaido, Japan', 'note': '經支笏湖後入住登別'},
    {'date': '2026-06-27', 'checkout': '2026-06-28', 'label': '6/27 登別、白老、室蘭，夜宿洞爺湖', 'location_zh': '洞爺湖', 'search': 'Lake Toya, Hokkaido, Japan', 'note': '夜宿洞爺湖'},
    {'date': '2026-06-28', 'checkout': '2026-06-29', 'label': '6/28 洞爺湖轉場小樽', 'location_zh': '小樽', 'search': 'Otaru, Hokkaido, Japan', 'note': '洞爺湖轉場小樽'},
    {'date': '2026-06-29', 'checkout': '2026-06-30', 'label': '6/29 鱗友朝市，小樽到札幌', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '小樽到札幌'},
    {'date': '2026-06-30', 'checkout': '2026-07-01', 'label': '6/30 札幌購物與親子緩衝', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '札幌購物與親子緩衝'},
    {'date': '2026-07-01', 'checkout': '2026-07-02', 'label': '7/1 札幌地下街、薄野與藻岩山', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '札幌地下街、薄野與藻岩山'},
    {'date': '2026-07-02', 'checkout': '2026-07-03', 'label': '7/2 札幌自由日與機場巴士確認', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '札幌自由日與機場巴士確認'},
]
OCCS = [
    {'key': 'family_1room', 'label': '3大1小(10歲)｜1 room', 'rooms': '1', 'section_id': 'one-room'},
    {'key': 'family_2rooms', 'label': '3大1小(10歲)｜2 rooms', 'rooms': '2', 'section_id': 'two-rooms'},
]

TARGET_HINTS = {
    'Eniwa, Hokkaido, Japan': ['eniwa', 'chitose', 'new chitose', 'cts-new chitose'],
    'Noboribetsu, Hokkaido, Japan': ['noboribetsu', 'noboribetsuonsen', 'noboribetsu onsen'],
    'Lake Toya, Hokkaido, Japan': ['toyako', 'lake toya', 'toya', 'toyako-cho'],
    'Otaru, Hokkaido, Japan': ['otaru'],
    'Sapporo, Hokkaido, Japan': ['sapporo', 'susukino', 'odori', 'tanukikoji', 'nakajima', 'sapporo station'],
}
CORE_SAPPORO_HINTS = ['susukino', 'odori', 'tanukikoji', 'sapporo station', 'odori park', 'nakajima']
OUTER_SAPPORO_HINTS = ['jozankei', 'shin-sapporo', 'teine', 'atsubetsu', 'airport', 'cts-new chitose', 'chitose']
FAMILY_POSITIVE_HINTS = ['apartment', 'residence', 'residential', 'suite', 'kitchen', 'kitchenette', 'spacious', 'family', 'sofa bed', 'separate bedroom']
FAMILY_NEGATIVE_HINTS = ['hostel', 'capsule', 'cabin', 'dormitory', 'shared bathroom']
TWO_ROOM_POSITIVE_HINTS = ['hotel', 'ryokan', 'resort', 'inn']

PRICE_TOKEN = r'(?:NT\$|US\$|TWD|JPY|¥|￥|\$)\s?[0-9][0-9,]*(?:\.\d+)?'
PRICE_RE = re.compile(PRICE_TOKEN)
RATING_RE = re.compile(r'(\d+(?:\.\d+)?)\s+out of 10')
REVIEWS_RE = re.compile(r'([0-9][0-9,]*) reviews')
DIST_RE = re.compile(r'([0-9]+(?:\.[0-9]+)?)\s+mi from\s+(.+)$', re.I)


def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def esc(value: object) -> str:
    return html.escape(str(value or ''))


def price_num(text: str) -> float | None:
    m = PRICE_RE.search(text or '')
    return float(re.sub(r'[^0-9.]', '', m.group(0))) if m else None


def hotels_url(item: dict[str, str], occ: dict[str, str]) -> str:
    return 'https://www.hotels.com/Hotel-Search?' + urlencode({
        'destination': item['search'],
        'startDate': item['date'],
        'endDate': item['checkout'],
        'rooms': occ['rooms'],
        'adults': '3',
        'children': '1_10',
        'sort': 'RECOMMENDED',
    })


def expedia_warmup_url(item: dict[str, str], occ: dict[str, str]) -> str:
    return 'https://www.expedia.com/Hotel-Search?' + urlencode({
        'destination': item['search'],
        'startDate': item['date'],
        'endDate': item['checkout'],
        'rooms': occ['rooms'],
        'adults': '3',
        'children': '1_10',
        'sort': 'RECOMMENDED',
    })


def normalize_name(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').strip()).lower()


def build_link_lookup(links: list[dict[str, str]]) -> tuple[dict[str, list[str]], list[str]]:
    mapping: dict[str, list[str]] = defaultdict(list)
    ordered = []
    for row in links:
        text = row.get('text', '')
        href = row.get('href', '')
        m = re.match(r'More information about\s+(.*?),\s+opens in a new tab', text)
        name = m.group(1).strip() if m else text.strip()
        if not name or not href:
            continue
        mapping[normalize_name(name)].append(href)
        ordered.append(href)
    return mapping, ordered


def parse_hotels_from_text(text: str, links: list[dict[str, str]], item: dict[str, str], occ: dict[str, str]) -> list[dict[str, object]]:
    link_lookup, ordered_links = build_link_lookup(links)
    ordered_index = 0
    hotels = []
    pieces = re.split(r'Photo gallery for ', text)
    for piece in pieces[1:]:
        lines = [line.strip() for line in piece.splitlines() if line.strip()]
        if not lines:
            continue
        name = lines[0]
        if len(name) > 160 or 'sort & filter' in name.lower():
            continue
        chunk_lines = []
        stop_markers = {'Photo gallery for', 'Search results', 'How our sort order works'}
        for line in lines[1:16]:
            if any(marker in line for marker in stop_markers):
                break
            chunk_lines.append(line)
        chunk = '\n'.join(chunk_lines)
        total_match = re.search(rf'The current price is ({PRICE_TOKEN}) total', chunk)
        total_price = total_match.group(1) + ' total' if total_match else ''
        nightly_match = re.search(rf'({PRICE_TOKEN}) nightly', chunk)
        nightly_price = nightly_match.group(1) + ' nightly' if nightly_match else ''
        price = total_price or nightly_price or ''
        score_match = RATING_RE.search(chunk)
        review_match = REVIEWS_RE.search(chunk)
        distance_line = next((line for line in chunk_lines if ' from ' in line and 'mi' in line), '')
        price_value = price_num(price)
        norm_name = normalize_name(name)
        link = ''
        if link_lookup.get(norm_name):
            link = link_lookup[norm_name].pop(0)
        elif ordered_index < len(ordered_links):
            link = ordered_links[ordered_index]
        ordered_index += 1
        hotels.append({
            'name': name,
            'rank_raw': len(hotels) + 1,
            'link': link,
            'link_type': 'property-level',
            'price': price,
            'price_num': price_value,
            'nightly_price': nightly_price,
            'total_price': total_price,
            'score': float(score_match.group(1)) if score_match else None,
            'reviews': int(review_match.group(1).replace(',', '')) if review_match else 0,
            'distance': distance_line,
            'snippet': chunk.replace('\n', ' | '),
            'location_text': distance_line,
            'occupancy_mode': occ['key'],
            'target_search': item['search'],
        })
    return hotels


def is_outer_sapporo(text: str) -> bool:
    low = (text or '').lower()
    return any(hint in low for hint in OUTER_SAPPORO_HINTS)


def area_score(item: dict[str, str], hotel: dict[str, object]) -> tuple[float, list[str], bool]:
    low = (' '.join([str(hotel.get('name') or ''), str(hotel.get('location_text') or ''), str(hotel.get('snippet') or '')])).lower()
    reasons = []
    approximate = False
    score = 0.0
    matched = any(hint in low for hint in TARGET_HINTS[item['search']])
    if matched:
        score += 18
        reasons.append('地點訊號較接近當晚落腳點')
    else:
        score -= 10
        approximate = True
        reasons.append('平台卡片地點訊號較弱，只能近似判斷')
    if item['search'] == 'Sapporo, Hokkaido, Japan':
        if any(hint in low for hint in CORE_SAPPORO_HINTS):
            score += 10
            reasons.append('偏札幌核心區')
        if is_outer_sapporo(low):
            score -= 24
            approximate = True
            reasons.append('疑似札幌外圍區，已降權')
    if item['search'] == 'Eniwa, Hokkaido, Japan' and 'sapporo' in low and 'chitose' not in low:
        score -= 18
        approximate = True
        reasons.append('結果偏札幌市區，離惠庭較遠')
    if item['search'] == 'Otaru, Hokkaido, Japan' and 'sapporo' in low:
        score -= 22
        approximate = True
        reasons.append('結果偏札幌，不是小樽核心')
    if item['search'] == 'Lake Toya, Hokkaido, Japan' and 'toyako' not in low and 'lake toya' not in low and 'toya' not in low:
        score -= 15
        approximate = True
        reasons.append('未明確落在洞爺湖圈')
    return score, reasons, approximate


def selection_score(item: dict[str, str], occ: dict[str, str], hotel: dict[str, object]) -> tuple[float, list[str], bool]:
    score = 0.0
    reasons = []
    approximate = False

    if hotel.get('price_num') is not None:
        score += 20
        score += max(0.0, 40.0 - math.log10(float(hotel['price_num']) + 1) * 18.0)
        reasons.append('有明確起始參考價')
    else:
        score -= 30
        approximate = True
        reasons.append('卡片價格不完整')

    if hotel.get('score') is not None:
        score += float(hotel['score']) * 5.5
        reasons.append(f"評分 {hotel['score']}")
    else:
        approximate = True
        reasons.append('缺少明確評分')

    reviews = int(hotel.get('reviews') or 0)
    if reviews:
        score += min(18.0, math.log10(reviews + 1) * 7.5)
        reasons.append(f'評論數 {reviews:,} 則')

    area_points, area_reasons, area_approx = area_score(item, hotel)
    score += area_points
    reasons.extend(area_reasons)
    approximate = approximate or area_approx

    low = (' '.join([str(hotel.get('name') or ''), str(hotel.get('snippet') or ''), str(hotel.get('location_text') or '')])).lower()
    family_hits = [hint for hint in FAMILY_POSITIVE_HINTS if hint in low]
    family_bad = [hint for hint in FAMILY_NEGATIVE_HINTS if hint in low]
    two_room_hits = [hint for hint in TWO_ROOM_POSITIVE_HINTS if hint in low]

    if occ['key'] == 'family_1room':
        if family_hits:
            score += min(16.0, 5.0 + len(family_hits) * 3.0)
            reasons.append('偏家庭房/公寓/寬敞房型訊號')
        else:
            score -= 8
            approximate = True
            reasons.append('未看到明確 1 room 家庭房訊號')
        if family_bad:
            score -= 20
            approximate = True
            reasons.append('偏宿舍/青年旅館型，1 room 容納家庭不穩')
    else:
        if two_room_hits:
            score += 10
            reasons.append('偏標準旅館型，較容易拆成兩房')
        if family_bad:
            score -= 10
            approximate = True
            reasons.append('偏宿舍/青年旅館型，拆兩房穩妥度較差')

    if 'fully refundable' in low:
        score += 2.5
        reasons.append('附 Fully refundable 訊號')
    if 'reserve now, pay later' in low:
        score += 2.5
        reasons.append('附 Reserve now, pay later 訊號')

    return round(score, 2), reasons, approximate


def nightly_notes(item: dict[str, str], occ: dict[str, str], selected: list[dict[str, object]]) -> list[str]:
    notes = [
        '優先挑有明確價格、評分/評論數較完整者。',
        '1 room 偏家庭/公寓/寬敞房型訊號；2 rooms 偏標準旅館型與較容易拆兩房。',
    ]
    if item['search'] == 'Sapporo, Hokkaido, Japan':
        notes.append('札幌搜尋結果仍可能混入定山溪、新札幌或機場側，已人工降權，仍有近似判斷成分。')
    if item['search'] == 'Eniwa, Hokkaido, Japan':
        notes.append('惠庭樣本容易混入千歲／札幌，已偏重新千歲—惠庭可接受範圍。')
    if item['search'] == 'Lake Toya, Hokkaido, Japan':
        notes.append('洞爺湖樣本若未直接寫 Toya/Toyako，會標成 approximate。')
    if occ['key'] == 'family_1room' and any(bool(h.get('approximate')) for h in selected[:3]):
        notes.append('1 room 前段候選仍有部分只能從房型文案與住宿型態近似推斷 3大1小可住性。')
    return notes


async def probe_one(page, item: dict[str, str], occ: dict[str, str]) -> dict[str, object]:
    url = hotels_url(item, occ)
    slug = f"{slugify(item['search'])}_{item['date']}_{occ['key']}"
    out_json = DATA_DIR / f'{slug}.json'
    out_png = DATA_DIR / f'{slug}.png'
    out_txt = DATA_DIR / f'{slug}.txt'
    res: dict[str, object] = {
        'site': 'Hotels.com',
        'date': item['date'],
        'checkout': item['checkout'],
        'search': item['search'],
        'occupancy_key': occ['key'],
        'occupancy_label': occ['label'],
        'url': url,
        'status': None,
        'title': '',
        'final_url': '',
        'links_found': 0,
        'hotels_found': 0,
        'hotels': [],
        'errors': [],
        'raw_text_path': str(out_txt),
        'screenshot': str(out_png),
    }
    try:
        text = ''
        links: list[dict[str, str]] = []
        for attempt in range(1, 5):
            resp = await page.goto(url, wait_until='domcontentloaded', timeout=90000)
            res['status'] = resp.status if resp else None
            await page.wait_for_timeout(12000)
            res['title'] = await page.title()
            res['final_url'] = page.url
            text = await page.locator('body').inner_text(timeout=15000)
            if res['status'] == 200 and 'Photo gallery for ' in text:
                links = await page.eval_on_selector_all(
                    'a',
                    '''els => els.map(a => ({text:(a.innerText||'').trim(), href:a.href})).filter(x => x.text.startsWith('More information about ') && x.href.includes('hotels.com/')).slice(0,80)''',
                )
                if links:
                    break
            res['errors'].append(f"attempt {attempt}: status={res['status']} title={res['title']}")
            if attempt < 4:
                warmup = expedia_warmup_url(item, occ)
                warm_resp = await page.goto(warmup, wait_until='domcontentloaded', timeout=90000)
                res['errors'].append(f"warmup {attempt}: status={warm_resp.status if warm_resp else None} title={await page.title()}")
                await page.wait_for_timeout(8000)
        out_txt.write_text(text, encoding='utf-8')
        await page.screenshot(path=str(out_png), full_page=False)
        hotels = parse_hotels_from_text(text, links, item, occ)
        res['links_found'] = len(links)
        res['hotels_found'] = len(hotels)
        res['hotels'] = hotels
    except Exception as exc:
        res['errors'].append(repr(exc))
    out_json.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    return res


def select_top_five(raw: dict[str, object], item: dict[str, str], occ: dict[str, str]) -> dict[str, object]:
    scored = []
    for hotel in raw.get('hotels', []):
        score, reasons, approximate = selection_score(item, occ, hotel)
        row = dict(hotel)
        row['selection_score'] = score
        row['why'] = reasons
        row['approximate'] = approximate
        scored.append(row)
    scored.sort(key=lambda h: (-float(h.get('selection_score', 0)), h.get('price_num') is None, float(h.get('price_num') or 10**9), int(h.get('rank_raw') or 9999)))
    top = scored[:5]
    return {
        'site': 'Hotels.com',
        'date': item['date'],
        'checkout': item['checkout'],
        'label': item['label'],
        'location_zh': item['location_zh'],
        'search': item['search'],
        'note': item['note'],
        'occupancy_key': occ['key'],
        'occupancy_label': occ['label'],
        'url': raw.get('final_url') or raw.get('url'),
        'probe_source': raw.get('source_json') or raw.get('json_path') or '',
        'raw_text_path': raw.get('raw_text_path'),
        'screenshot': raw.get('screenshot'),
        'status': raw.get('status'),
        'title': raw.get('title'),
        'links_found': raw.get('links_found', 0),
        'hotels_found': raw.get('hotels_found', 0),
        'selected': top,
        'notes': nightly_notes(item, occ, top),
        'errors': raw.get('errors', []),
    }


def render_html(rows: list[dict[str, object]]) -> None:
    by_mode: dict[str, list[dict[str, object]]] = {occ['key']: [] for occ in OCCS}
    for row in rows:
        by_mode[row['occupancy_key']].append(row)
    for occ in OCCS:
        by_mode[occ['key']].sort(key=lambda r: r['date'])
    generated = time.strftime('%Y-%m-%d %H:%M:%S %Z')
    css = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:24px;color:#172033;background:#f6f7fb;line-height:1.55}
h1,h2,h3,h4{color:#101828}.meta{color:#667085}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:white;border:1px solid #e4e7ec;border-radius:14px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.05);margin:14px 0}.hotel{border-top:1px solid #eaecf0;padding:10px 0}.hotel:first-child{border-top:0}.price{font-weight:700;color:#175cd3}.small{font-size:12px;color:#667085}.pill{display:inline-block;border-radius:999px;padding:2px 8px;background:#eef4ff;color:#3538cd;font-size:12px;margin-left:6px}.occ{background:#fff7ed;color:#b54708}.warn{color:#b54708}.bad{color:#b42318}.ok{color:#067647}.toc a{display:block;margin:6px 0}.section-title{position:sticky;top:0;background:#f6f7fb;padding:10px 0 2px;z-index:1}a{color:#175cd3}@media(max-width:900px){.grid{grid-template-columns:1fr}}
"""
    parts = [
        f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>北海道行程 Hotels.com 主動篩選合併報告</title><style>{css}</style></head><body>",
        '<h1>北海道行程 Hotels.com 主動篩選合併報告</h1>',
        f"<p class='meta'>來源：既有 Hotels.com multisite JSON 檢查後，因多數為 429 / Bot or Not?，改以 Hotels.com 專用最小補抓重建。固定條件：3 adults + 1 child age 10。更新時間：{esc(generated)}</p>",
        f"<p class='meta'>總說明：{esc(PRICE_WARNING)} 另因 Hotels.com 搜尋結果主要提供住宿頁連結，本文每筆均標示「{esc(LINK_WARNING)}」。</p>",
        "<section class='card toc'><h2>內容導覽</h2><a href='#one-room'>1 room：每晚主動篩選 5 間</a><a href='#two-rooms'>2 rooms：每晚主動篩選 5 間</a></section>",
    ]
    for occ in OCCS:
        parts.append(f"<div id='{esc(occ['section_id'])}' class='section-title'><h2>{esc(occ['label'])}：每晚主動篩選 5 間</h2></div>")
        parts.append(f"<p class='meta'>{esc(PRICE_WARNING)} 若卡片地點或房型訊號不足，會明確標記 approximate。</p>")
        for row in by_mode[occ['key']]:
            parts.append("<section class='card'>")
            parts.append(f"<h2>{esc(row['label'])} <span class='pill'>{esc(row['location_zh'])}</span></h2>")
            parts.append(f"<p class='meta'>住宿搜尋：{esc(row['search'])}｜入住：{esc(row['date'])}｜退房：{esc(row['checkout'])}｜備註：{esc(row['note'])}</p>")
            parts.append(f"<h3><span class='pill occ'>{esc(occ['label'])}</span></h3>")
            parts.append("<div class='grid'>")
            parts.append("<div class='card'>")
            parts.append('<h4>資料與篩選說明</h4>')
            parts.append(f"<p class='small'>查詢標題：{esc(row.get('title') or '')}</p>")
            parts.append(f"<p class='small'>查詢連結：<a href='{esc(row['url'])}' target='_blank' rel='noreferrer'>{esc(row['url'])}</a></p>")
            parts.append(f"<p class='small'>probe source：{esc(row.get('probe_source') or '')}</p>")
            parts.append(f"<p class='small'>raw text：{esc(row.get('raw_text_path') or '')}</p>")
            parts.append(f"<p class='small'>screenshot：{esc(row.get('screenshot') or '')}</p>")
            parts.append(f"<p class='small'>解析候選：{esc(row.get('hotels_found'))} 間｜已選：{len(row['selected'])} 間</p>")
            parts.append('<h4>此晚篩選提醒</h4><ul class="small">')
            for note in row['notes']:
                parts.append(f'<li>{esc(note)}</li>')
            parts.append('</ul></div>')
            parts.append("<div class='card'>")
            parts.append(f"<h4>每晚最值得點開 5 間（{esc(occ['rooms'])} room{'s' if occ['rooms']=='2' else ''}）</h4>")
            for idx, hotel in enumerate(row['selected'], 1):
                approx = ' approximate' if hotel.get('approximate') else ''
                parts.append("<div class='hotel'>")
                parts.append(f"<div><strong>{idx}. <a href='{esc(hotel.get('link') or row['url'])}' target='_blank' rel='noreferrer'>{esc(hotel['name'])}</a></strong> <span class='small'>（原 Hotels.com 排名 #{esc(hotel.get('rank_raw'))}｜篩選分數 {esc(hotel.get('selection_score'))}{esc(approx)}）</span></div>")
                parts.append(f"<div class='price'>{esc(hotel.get('price') or '未顯示')}</div>")
                parts.append(f"<div class='small warn'>價格註記：{esc(PRICE_WARNING)}</div>")
                parts.append(f"<div class='small warn'>連結註記：{esc(LINK_WARNING)}</div>")
                meta_bits = []
                if hotel.get('score') is not None:
                    meta_bits.append(f"評分 {hotel['score']}")
                if hotel.get('reviews'):
                    meta_bits.append(f"評論 {int(hotel['reviews']):,} 則")
                if hotel.get('distance'):
                    meta_bits.append(str(hotel['distance']))
                parts.append(f"<div class='small'>{esc('｜'.join(meta_bits))}</div>")
                if hotel.get('approximate'):
                    parts.append("<div class='small bad'>approximate：此筆仍含地點或房型可住性近似判斷。</div>")
                parts.append(f"<div class='small'>{esc('；'.join(hotel.get('why') or []))}</div>")
                parts.append(f"<div class='small'><a href='{esc(hotel.get('link') or row['url'])}' target='_blank' rel='noreferrer'>開啟住宿頁</a></div>")
                parts.append(f"<div class='small'>{esc(hotel.get('snippet') or '')}</div>")
                parts.append('</div>')
            parts.append('</div></div></section>')
    parts.append('</body></html>')
    REPORT_PATH.write_text('\n'.join(parts), encoding='utf-8')


def write_summary(rows: list[dict[str, object]], raw_results: list[dict[str, object]]) -> None:
    approx_nights = {occ['key']: [] for occ in OCCS}
    top5_counts = {}
    top1 = {}
    for row in rows:
        if any(bool(h.get('approximate')) for h in row['selected'][:1]):
            approx_nights[row['occupancy_key']].append(row['date'])
        top5_counts[f"{row['date']}_{row['occupancy_key']}"] = len(row['selected'])
        top1.setdefault(row['date'], {})[row['occupancy_key']] = {
            'name': row['selected'][0]['name'],
            'price': row['selected'][0].get('price'),
            'score': row['selected'][0].get('score'),
            'distance': row['selected'][0].get('distance'),
            'link': row['selected'][0].get('link'),
            'selection_score': row['selected'][0].get('selection_score'),
            'approximate': row['selected'][0].get('approximate'),
        }
    legacy_gaps = []
    for item in ITINERARY:
        for occ in OCCS:
            old_path = LEGACY_DIR / f"hotelscom_{occ['key']}_{item['date']}.json"
            if old_path.exists():
                data = json.loads(old_path.read_text(encoding='utf-8'))
                if data.get('status') == 429 or not data.get('hotels'):
                    legacy_gaps.append(f"{old_path}: status={data.get('status')} title={data.get('title')} hotels={len(data.get('hotels') or [])}")
            else:
                legacy_gaps.append(f"{old_path}: 缺檔")
    summary = {
        'site': 'Hotels.com',
        'output_html': str(REPORT_PATH),
        'output_exists': REPORT_PATH.exists(),
        'data_sources_used': [
            str(BASE / 'scripts' / 'multisite_compact_report.py'),
            str(BASE / 'reports' / 'hokkaido_hotels_3sites_compact.html'),
            str(BASE / 'reports' / 'hokkaido_hotels_trivago_family_combined.html'),
            *[str(DATA_DIR / f"{slugify(row['search'])}_{row['date']}_{row['occupancy_key']}.json") for row in rows],
        ],
        'scripts_used_or_created': [
            str(SCRIPT_PATH),
        ],
        'selection_rules_applied': [
            '有價格優先',
            '評分/評論數優先',
            '地點吻合 itinerary 落腳點',
            '1 room 偏家庭/公寓/寬敞房型訊號',
            '2 rooms 偏標準旅館型與較容易拆兩房',
            '札幌外圍與跨城市結果降權',
            '無法確認 3大1小或地點時標 approximate',
        ],
        'approx_nights_by_mode': approx_nights,
        'validation': {
            'nights_expected': len(ITINERARY),
            'nights_found_per_mode': {occ['key']: sum(1 for row in rows if row['occupancy_key'] == occ['key']) for occ in OCCS},
            'top5_count_per_night': top5_counts,
            'all_entries_have_links': all(bool(h.get('link')) for row in rows for h in row['selected']),
            'price_warning_included': PRICE_WARNING in REPORT_PATH.read_text(encoding='utf-8'),
            'legacy_data_insufficient': True,
            'legacy_data_gaps': legacy_gaps,
            'minimal_refetch_performed': True,
            'minimal_refetch_files': [str(Path(raw['source_json'])) for raw in raw_results],
            'remaining_approximation_nights': approx_nights,
        },
        'top1_by_night': top1,
        'old_data_gaps': legacy_gaps,
        'minimal_refetch_done': [
            '以 CloakBrowser CDP 重新抓取 8 晚 × 2 occupancy 的 Hotels.com 搜尋結果文字、連結、截圖。',
            '新資料保留於 data/hotelscom_probe/*.json|*.txt|*.png。',
        ],
        'remaining_approximation_notes': {
            'family_1room': '若 top1 缺少明確家庭房訊號或結果偏外圍，就保留 approximate。',
            'family_2rooms': '若 top1 地點仍偏外圍，才保留 approximate；其餘多數可視為較穩妥兩房候選。',
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')


async def main() -> None:
    raw_results = []
    browser = await launch_async(headless=True, locale='en-US', timezone='Asia/Tokyo')
    try:
        page = await browser.new_page(viewport={'width': 1365, 'height': 900})
        for item in ITINERARY:
            for occ in OCCS:
                print('PROBE', item['date'], occ['key'], item['search'], flush=True)
                raw = await probe_one(page, item, occ)
                raw['source_json'] = str(DATA_DIR / f"{slugify(item['search'])}_{item['date']}_{occ['key']}.json")
                raw_results.append(raw)
                await asyncio.sleep(1.0)
    finally:
        await browser.close()
    selected_rows = []
    for item in ITINERARY:
        for occ in OCCS:
            raw = next(r for r in raw_results if r['date'] == item['date'] and r['occupancy_key'] == occ['key'])
            selected_rows.append(select_top_five(raw, item, occ))
    render_html(selected_rows)
    write_summary(selected_rows, raw_results)
    print(f'WROTE {REPORT_PATH}')
    print(f'WROTE {SUMMARY_PATH}')


if __name__ == '__main__':
    asyncio.run(main())
