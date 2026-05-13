#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import html
import json
import math
import re
import socket
import tempfile
import time
import urllib.request
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlencode

from cloakbrowser import build_args, ensure_binary
from playwright.async_api import async_playwright

BASE = Path('/home/profe/hotel-research')
DATA_DIR = BASE / 'data' / 'expedia_probe'
LEGACY_DIR = BASE / 'data' / 'multisite'
REPORT_PATH = BASE / 'reports' / 'hokkaido_hotels_expedia_family_combined.html'
SUMMARY_PATH = BASE / 'reports' / 'hokkaido_hotels_expedia_family_summary.json'
SCRIPT_PATH = BASE / 'scripts' / 'render_expedia_family_combined.py'
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

PRICE_WARNING = '這只是該日期查詢下平台卡片顯示的起始參考價，不是保證最終成交價。'
LINK_WARNING = '此連結為 Expedia 住宿頁連結，非精確 room-level 連結。'

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
    'Eniwa, Hokkaido, Japan': ['eniwa', 'chitose', 'new chitose', 'cts-new chitose', 'atsuma'],
    'Noboribetsu, Hokkaido, Japan': ['noboribetsu', 'noboribetsuonsen', 'noboribetsu onsen', 'date', 'muroran'],
    'Lake Toya, Hokkaido, Japan': ['toyako', 'lake toya', 'toya', 'toyako-cho'],
    'Otaru, Hokkaido, Japan': ['otaru'],
    'Sapporo, Hokkaido, Japan': ['sapporo', 'susukino', 'odori', 'tanukikoji', 'nakajima', 'sapporo station'],
}
CORE_SAPPORO_HINTS = ['susukino', 'odori', 'tanukikoji', 'sapporo station', 'odori park', 'nakajima']
OUTER_SAPPORO_HINTS = ['jozankei', 'shin-sapporo', 'teine', 'atsubetsu', 'airport', 'cts-new chitose', 'chitose']
FAMILY_POSITIVE_HINTS = ['apartment', 'suite', 'kitchen', 'kitchenette', 'family', 'sofa bed', 'spacious', 'entire property', 'vrbo']
FAMILY_NEGATIVE_HINTS = ['hostel', 'capsule', 'cabin', 'dormitory', 'shared bathroom']
TWO_ROOM_POSITIVE_HINTS = ['hotel', 'ryokan', 'resort', 'inn']

PRICE_RE = re.compile(r'\$\s?([0-9][0-9,]*)')
TOTAL_RE = re.compile(r'The current price is (\$\s?[0-9][0-9,]*) total', re.I)
NIGHTLY_RE = re.compile(r'(\$\s?[0-9][0-9,]*) nightly', re.I)
RATING_RE = re.compile(r'(\d+(?:\.\d+)?)\s+out of 10')
REVIEWS_RE = re.compile(r'([0-9][0-9,]*) reviews')
DIST_RE = re.compile(r'([0-9]+(?:\.[0-9]+)?)\s+mi from\s+(.+)$', re.I)
MORE_INFO_RE = re.compile(r'More information about\s+(.*?),\s+opens in a new tab')


def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def esc(value: object) -> str:
    return html.escape(str(value or ''))


def price_num(text: str) -> float | None:
    m = PRICE_RE.search(text or '')
    return float(m.group(1).replace(',', '')) if m else None


def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return int(sock.getsockname()[1])


def make_cdp_args(port: int, user_data_dir: str, headless: bool, locale: str, timezone: str) -> list[str]:
    extra_args = [
        f'--remote-debugging-port={port}',
        f'--user-data-dir={user_data_dir}',
        '--no-first-run',
        '--no-default-browser-check',
        '--headless=new',
    ]
    return build_args(True, extra_args, timezone=timezone, locale=locale, headless=headless)


async def wait_for_cdp_endpoint(port: int, timeout: float = 30.0) -> str:
    endpoint = f'http://127.0.0.1:{port}'
    version_url = f'{endpoint}/json/version'
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            await asyncio.to_thread(lambda: urllib.request.urlopen(version_url, timeout=1).read())
            return endpoint
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.2)
    raise RuntimeError(f'CDP endpoint did not become ready at {version_url}: {last_error!r}')


@asynccontextmanager
async def cloakbrowser_cdp(headless: bool = True, locale: str = 'en-US', timezone: str = 'Asia/Tokyo'):
    binary_path = ensure_binary()
    port = pick_free_port()
    profile = tempfile.TemporaryDirectory(prefix='cloakbrowser-cdp-')
    process = None
    playwright = None
    browser = None
    try:
        args = make_cdp_args(port, profile.name, headless=headless, locale=locale, timezone=timezone)
        process = await asyncio.create_subprocess_exec(
            binary_path,
            *args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        endpoint = await wait_for_cdp_endpoint(port)
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(endpoint)
        yield browser
    finally:
        if browser is not None:
            await browser.close()
        if playwright is not None:
            await playwright.stop()
        if process is not None and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        try:
            profile.cleanup()
        except Exception:
            pass


async def new_cdp_page(browser, viewport: dict[str, int]):
    context = browser.contexts[0] if browser.contexts else await browser.new_context()
    page = context.pages[0] if context.pages else await context.new_page()
    await page.set_viewport_size(viewport)
    return page


def expedia_url(item: dict[str, str], occ: dict[str, str]) -> str:
    return 'https://www.expedia.com/Hotel-Search?' + urlencode({
        'destination': item['search'],
        'startDate': item['date'],
        'endDate': item['checkout'],
        'rooms': occ['rooms'],
        'adults': '3',
        'children': '1_10',
        'sort': 'PRICE_LOW_TO_HIGH',
        'useRewards': 'false',
        'currency': 'JPY',
        'locale': 'en_US',
    })


def normalize_name(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').strip()).lower()


def nearest_anchor_lines(lines: list[str], search_text: str, start_idx: int) -> int:
    for i in range(start_idx, len(lines)):
        if lines[i] == search_text:
            return i
    return -1


def detect_area_line(lines: list[str], item: dict[str, str], name: str) -> str:
    name_low = name.lower()
    for line in lines:
        low = line.lower()
        if low == name_low:
            continue
        if ' mi from ' in low:
            return line
        if any(hint in low for hint in TARGET_HINTS[item['search']]):
            return line
        if low.startswith(('susukino', 'odori', 'nakajima', 'kita ward', 'chuo-ku', 'otaru', 'toyako', 'lake toya', 'noboribetsu', 'muroran', 'date', 'chitose', 'eniwa')):
            return line
    return ''


def parse_hotels_from_text(text: str, links: list[dict[str, str]], item: dict[str, str], occ: dict[str, str]) -> list[dict[str, object]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    hotels = []
    cursor = 0
    for rank_raw, row in enumerate(links, 1):
        anchor_text = row.get('text', '').strip()
        href = row.get('href', '').strip()
        match = MORE_INFO_RE.match(anchor_text)
        if not match or not href:
            continue
        name = match.group(1).strip()
        anchor_idx = nearest_anchor_lines(lines, anchor_text, cursor)
        if anchor_idx < 0:
            continue
        block = lines[max(cursor, anchor_idx - 24):anchor_idx]
        cursor = anchor_idx + 1
        if not block:
            continue
        photo_positions = [i for i, line in enumerate(block) if line.startswith('Photo gallery for ')]
        if photo_positions:
            block = block[photo_positions[-1]:]
        name_positions = [i for i, line in enumerate(block) if normalize_name(line) == normalize_name(name)]
        if name_positions:
            block = block[max(0, name_positions[-1] - 1):]
        chunk_lines = block[-18:]
        chunk = '\n'.join(chunk_lines)
        total_match = TOTAL_RE.search(chunk)
        nightly_match = NIGHTLY_RE.search(chunk)
        any_price = PRICE_RE.search(chunk)
        total_price = total_match.group(1) + ' total' if total_match else ''
        nightly_price = nightly_match.group(1) + ' nightly' if nightly_match else ''
        price = total_price or nightly_price or (any_price.group(0) if any_price else '')
        score_match = RATING_RE.search(chunk)
        review_match = REVIEWS_RE.search(chunk)
        area_line = detect_area_line(chunk_lines, item, name)
        hotels.append({
            'name': name,
            'rank_raw': rank_raw,
            'link': href,
            'link_type': 'property-level',
            'price': price,
            'price_num': price_num(price),
            'nightly_price': nightly_price,
            'total_price': total_price,
            'score': float(score_match.group(1)) if score_match else None,
            'reviews': int(review_match.group(1).replace(',', '')) if review_match else 0,
            'distance': area_line,
            'snippet': ' | '.join(chunk_lines),
            'location_text': area_line,
            'occupancy_mode': occ['key'],
            'target_search': item['search'],
        })
    deduped = []
    seen = set()
    for hotel in hotels:
        key = (normalize_name(str(hotel.get('name') or '')), str(hotel.get('price') or ''))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hotel)
    return deduped


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
        score -= 12
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
    if item['search'] == 'Eniwa, Hokkaido, Japan' and 'sapporo' in low and 'chitose' not in low and 'new chitose' not in low:
        score -= 20
        approximate = True
        reasons.append('結果偏札幌市區，離惠庭較遠')
    if item['search'] == 'Noboribetsu, Hokkaido, Japan' and 'rusutsu' in low:
        score -= 24
        approximate = True
        reasons.append('結果偏留壽都，不是登別住宿圈')
    if item['search'] == 'Lake Toya, Hokkaido, Japan' and 'toyako' not in low and 'lake toya' not in low and 'toya' not in low:
        score -= 18
        approximate = True
        reasons.append('未明確落在洞爺湖圈')
    if item['search'] == 'Otaru, Hokkaido, Japan' and 'sapporo' in low:
        score -= 24
        approximate = True
        reasons.append('結果偏札幌，不是小樽核心')
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
        '1 room 偏家庭房/公寓/整戶型訊號；2 rooms 偏標準旅館型與較容易拆兩房。',
    ]
    if item['search'] == 'Eniwa, Hokkaido, Japan':
        notes.append('Expedia 的惠庭搜尋明顯混入札幌與新千歲周邊，已優先保留較接近機場緩衝邏輯者。')
    if item['search'] == 'Noboribetsu, Hokkaido, Japan':
        notes.append('登別搜尋容易外擴到室蘭／伊達／留壽都，非登別核心者已降權。')
    if item['search'] == 'Lake Toya, Hokkaido, Japan':
        notes.append('洞爺湖若未直接寫 Toya/Toyako，多數只能做近似判斷。')
    if item['search'] == 'Otaru, Hokkaido, Japan':
        notes.append('小樽搜尋會混入札幌；已人工偏重 Otaru 字樣與非宿舍型結果。')
    if item['search'] == 'Sapporo, Hokkaido, Japan':
        notes.append('札幌樣本相對可用，但仍可能混入外圍區；已偏重核心區與家庭/標準旅館訊號。')
    if occ['key'] == 'family_1room' and any(bool(h.get('approximate')) for h in selected[:3]):
        notes.append('1 room 前段候選仍有部分只能從房型文案與住宿型態近似推斷 3大1小可住性。')
    return notes


async def probe_one(page, item: dict[str, str], occ: dict[str, str]) -> dict[str, object]:
    url = expedia_url(item, occ)
    slug = f"{slugify(item['search'])}_{item['date']}_{occ['key']}"
    out_json = DATA_DIR / f'{slug}.json'
    out_png = DATA_DIR / f'{slug}.png'
    out_txt = DATA_DIR / f'{slug}.txt'
    res: dict[str, object] = {
        'site': 'Expedia',
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
        resp = await page.goto(url, wait_until='domcontentloaded', timeout=90000)
        res['status'] = resp.status if resp else None
        await page.wait_for_timeout(12000)
        res['title'] = await page.title()
        res['final_url'] = page.url
        text = await page.locator('body').inner_text(timeout=15000)
        out_txt.write_text(text, encoding='utf-8')
        links = await page.eval_on_selector_all(
            'a',
            '''els => els.map(a => ({text:(a.innerText||'').trim(), href:a.href})).filter(x => x.text.startsWith('More information about ') && x.href.includes('expedia.com/')).slice(0,80)''',
        )
        await page.screenshot(path=str(out_png), full_page=False)
        hotels = parse_hotels_from_text(text, links, item, occ)
        res['links_found'] = len(links)
        res['hotels_found'] = len(hotels)
        res['hotels'] = hotels
    except Exception as exc:
        res['errors'].append(repr(exc))
    out_json.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    return res


def probe_usable(raw: dict[str, object]) -> bool:
    title = str(raw.get('title') or '').strip().lower()
    return title != 'bot or not?' and int(raw.get('hotels_found') or 0) >= 5 and bool(raw.get('hotels'))


async def probe_with_retries(item: dict[str, str], occ: dict[str, str], attempts: int = 3) -> dict[str, object]:
    last_raw: dict[str, object] | None = None
    for attempt in range(1, attempts + 1):
        async with cloakbrowser_cdp(headless=True, locale='en-US', timezone='Asia/Tokyo') as browser:
            page = await new_cdp_page(browser, {'width': 1365, 'height': 900})
            raw = await probe_one(page, item, occ)
        raw['source_json'] = str(DATA_DIR / f"{slugify(item['search'])}_{item['date']}_{occ['key']}.json")
        raw['attempt'] = attempt
        raw['used_fresh_browser'] = True
        last_raw = raw
        if probe_usable(raw):
            return raw
        await asyncio.sleep(min(8, 2 * attempt))
    assert last_raw is not None
    return last_raw


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
        'site': 'Expedia',
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
h1,h2,h3,h4{color:#101828}.meta{color:#667085}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:white;border:1px solid #e4e7ec;border-radius:14px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.05);margin:14px 0}.hotel{border-top:1px solid #eaecf0;padding:10px 0}.hotel:first-child{border-top:0}.price{font-weight:700;color:#175cd3}.small{font-size:12px;color:#667085}.pill{display:inline-block;border-radius:999px;padding:2px 8px;background:#eef4ff;color:#3538cd;font-size:12px;margin-left:6px}.occ{background:#fff7ed;color:#b54708}.warn{color:#b54708}.bad{color:#b42318}.toc a{display:block;margin:6px 0}.section-title{position:sticky;top:0;background:#f6f7fb;padding:10px 0 2px;z-index:1}a{color:#175cd3}@media(max-width:900px){.grid{grid-template-columns:1fr}}
"""
    parts = [
        f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>北海道行程 Expedia 主動篩選合併報告</title><style>{css}</style></head><body>",
        '<h1>北海道行程 Expedia 主動篩選合併報告</h1>',
        f"<p class='meta'>來源：先盤點既有 Expedia multisite JSON，確認惠庭／登別／洞爺湖／小樽結果有明顯目的地偏移且多晚不足 5 筆，因此只對 Expedia 單站做最小必要補抓與重解析。固定條件：3 adults + 1 child age 10。更新時間：{esc(generated)}</p>",
        f"<p class='meta'>總說明：{esc(PRICE_WARNING)} 另因 Expedia 搜尋頁多提供住宿頁（property-level）連結，本文每筆均標示「{esc(LINK_WARNING)}」。</p>",
        "<section class='card toc'><h2>內容導覽</h2><a href='#one-room'>1 room：每晚主動篩選 5 間</a><a href='#two-rooms'>2 rooms：每晚主動篩選 5 間</a><p class='small'>參考格式：reports/hokkaido_hotels_trivago_family_combined.html</p></section>",
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
                parts.append(f"<div><strong>{idx}. <a href='{esc(hotel.get('link') or row['url'])}' target='_blank' rel='noreferrer'>{esc(hotel['name'])}</a></strong> <span class='small'>（原 Expedia 排名 #{esc(hotel.get('rank_raw'))}｜篩選分數 {esc(hotel.get('selection_score'))}{esc(approx)}）</span></div>")
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
                parts.append(f"<div class='small'><a href='{esc(hotel.get('link') or row['url'])}' target='_blank' rel='noreferrer'>開啟 Expedia 住宿頁</a></div>")
                parts.append(f"<div class='small'>{esc(hotel.get('snippet') or '')}</div>")
                parts.append('</div>')
            parts.append('</div></div></section>')
    parts.append('</body></html>')
    REPORT_PATH.write_text('\n'.join(parts), encoding='utf-8')


def assess_legacy_data() -> tuple[list[str], dict[str, object]]:
    untrusted = []
    detail = {}
    for item in ITINERARY:
        for occ in OCCS:
            path = LEGACY_DIR / f"expedia_{occ['key']}_{item['date']}.json"
            key = f"{item['date']}_{occ['key']}"
            if not path.exists():
                detail[key] = {'path': str(path), 'exists': False, 'trusted': False, 'reason': '缺檔'}
                untrusted.append(f"{item['date']} {item['location_zh']} {occ['key']}：缺檔")
                continue
            data = json.loads(path.read_text(encoding='utf-8'))
            hotels = data.get('hotels') or []
            names = ' | '.join(str(h.get('name') or '') for h in hotels[:5]).lower()
            reasons = []
            if len(hotels) < 5:
                reasons.append(f'僅 {len(hotels)} 筆')
            if item['search'] != 'Sapporo, Hokkaido, Japan':
                target = item['location_zh']
                if item['search'] == 'Eniwa, Hokkaido, Japan' and 'sapporo' in names and 'eniwa' not in names and 'chitose' not in names:
                    reasons.append('結果偏札幌')
                if item['search'] == 'Noboribetsu, Hokkaido, Japan' and ('rusutsu' in names or 'muroran' in names):
                    reasons.append('結果偏留壽都/室蘭')
                if item['search'] == 'Lake Toya, Hokkaido, Japan' and 'toya' not in names and 'toyako' not in names:
                    reasons.append('結果不在洞爺湖圈')
                if item['search'] == 'Otaru, Hokkaido, Japan' and 'sapporo' in names:
                    reasons.append('結果混入札幌')
            trusted = not reasons
            detail[key] = {
                'path': str(path),
                'exists': True,
                'trusted': trusted,
                'reason': '；'.join(reasons) if reasons else '勉強可參考',
                'sample_names': [h.get('name') for h in hotels[:5]],
            }
            if not trusted:
                untrusted.append(f"{item['date']} {item['location_zh']} {occ['key']}：{'；'.join(reasons)}")
    return untrusted, detail


def write_summary(rows: list[dict[str, object]], raw_results: list[dict[str, object]]) -> None:
    approx_nights = {occ['key']: [] for occ in OCCS}
    top5_counts = {}
    top1 = {}
    for row in rows:
        selected = row.get('selected') or []
        if any(bool(h.get('approximate')) for h in selected[:1]):
            approx_nights[row['occupancy_key']].append(row['date'])
        top5_counts[f"{row['date']}_{row['occupancy_key']}"] = len(selected)
        if selected:
            top1.setdefault(row['date'], {})[row['occupancy_key']] = {
                'name': selected[0]['name'],
                'price': selected[0].get('price'),
                'score': selected[0].get('score'),
                'distance': selected[0].get('distance'),
                'link': selected[0].get('link'),
                'selection_score': selected[0].get('selection_score'),
                'approximate': selected[0].get('approximate'),
            }
        else:
            top1.setdefault(row['date'], {})[row['occupancy_key']] = None
    untrusted, legacy_detail = assess_legacy_data()
    summary = {
        'site': 'Expedia',
        'output_html': str(REPORT_PATH),
        'output_exists': REPORT_PATH.exists(),
        'data_sources_used': [
            str(BASE / 'scripts' / 'multisite_compact_report.py'),
            str(BASE / 'data' / 'multisite' / 'expedia_hotels_all.json'),
            str(BASE / 'reports' / 'expedia_family_3sites_price_ranking.html'),
            str(BASE / 'reports' / 'hokkaido_hotels_3sites_compact.html'),
            str(BASE / 'reports' / 'hokkaido_hotels_trivago_family_combined.html'),
            *[str(Path(raw['source_json'])) for raw in raw_results],
        ],
        'scripts_used_or_created': [
            str(SCRIPT_PATH),
        ],
        'selection_rules_applied': [
            '有價格優先',
            '評分/評論數優先',
            '地點吻合 itinerary 落腳點',
            '1 room 偏家庭/公寓/整戶型訊號',
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
            'legacy_data_untrusted_nights': untrusted,
            'legacy_data_detail': legacy_detail,
            'minimal_refetch_performed': True,
            'minimal_refetch_scope': 'Expedia 單站 8 晚 × 2 occupancy，重抓搜尋頁文字、連結、截圖並重解析。',
            'remaining_approximation_nights': approx_nights,
        },
        'top1_by_night': top1,
        'legacy_expedia_untrusted': untrusted,
        'did_minimal_refetch_or_reparse': True,
        'minimal_refetch_or_reparse_notes': [
            '既有 Expedia JSON 多晚只有 3–4 筆，且惠庭／登別／洞爺湖／小樽出現明顯跨城市結果。',
            '因此新增 Expedia 專用腳本，僅重抓 Expedia 單站搜尋頁，不改共享 multisite 流程。',
            '新資料保留於 data/expedia_probe/*.json|*.txt|*.png。',
        ],
        'remaining_approximation_notes': {
            'family_1room': '多數非札幌夜晚仍受 Expedia 目的地外擴影響，只能依地點與家庭房訊號近似判斷。',
            'family_2rooms': '兩房模式相對可依標準旅館型判斷，但惠庭／登別／洞爺湖／小樽仍有跨城市近似成分。',
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')


async def main() -> None:
    raw_results = []
    for item in ITINERARY:
        for occ in OCCS:
            print('PROBE', item['date'], occ['key'], item['search'], flush=True)
            raw = await probe_with_retries(item, occ)
            raw_results.append(raw)
            await asyncio.sleep(1.0)
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
