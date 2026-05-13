#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode

BASE = Path('/home/profe/hotel-research')
DATA_DIR = BASE / 'data' / 'hotelscom_probe'
REPORT_PATH = BASE / 'reports' / 'hokkaido_hotels_hotelscom_family_combined.html'
SUMMARY_PATH = BASE / 'reports' / 'hokkaido_hotels_hotelscom_family_summary.json'

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
OCC_BY_KEY = {occ['key']: occ for occ in OCCS}

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

FALLBACK_SEARCH_ORDER = {
    'Eniwa, Hokkaido, Japan': ['Sapporo, Hokkaido, Japan'],
    'Noboribetsu, Hokkaido, Japan': ['Lake Toya, Hokkaido, Japan'],
    'Lake Toya, Hokkaido, Japan': ['Noboribetsu, Hokkaido, Japan'],
    'Otaru, Hokkaido, Japan': ['Sapporo, Hokkaido, Japan'],
    'Sapporo, Hokkaido, Japan': [],
}

PRICE_TOKEN = r'(?:NT\$|US\$|TWD|JPY|¥|￥|\$)\s?[0-9][0-9,]*(?:\.\d+)?'
PRICE_RE = re.compile(PRICE_TOKEN)
RATING_RE = re.compile(r'(\d+(?:\.\d+)?)\s+out of 10')
REVIEWS_RE = re.compile(r'([0-9][0-9,]*) reviews')


def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def esc(value: object) -> str:
    return html.escape(str(value or ''))


def normalize_name(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').strip()).lower()


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


def candidate_sort_key(h: dict[str, object]) -> tuple[float, bool, float, int]:
    return (-float(h.get('selection_score', 0)), h.get('price_num') is None, float(h.get('price_num') or 10**9), int(h.get('rank_raw') or 9999))


def parse_existing_report_pool() -> list[dict[str, object]]:
    if not REPORT_PATH.exists():
        return []
    text = REPORT_PATH.read_text(encoding='utf-8')
    blocks = text.split("<section class='card'>")
    pool = []
    for block in blocks:
        if '住宿搜尋：' not in block or "<div class='hotel'>" not in block:
            continue
        search_m = re.search(r'住宿搜尋：([^｜<]+)｜入住：([0-9\-]+)｜退房：([0-9\-]+)', block)
        occ_m = re.search(r"<h3><span class='pill occ'>([^<]+)</span></h3>", block)
        if not search_m or not occ_m:
            continue
        search = html.unescape(search_m.group(1)).strip()
        date = search_m.group(2)
        occ_key = 'family_2rooms' if '2 rooms' in occ_m.group(1) else 'family_1room'
        for idx, chunk in enumerate(block.split("<div class='hotel'>")[1:], 1):
            a_m = re.search(r"<strong>\d+\. <a href='([^']+)'[^>]*>(.*?)</a></strong>", chunk, re.S)
            if not a_m:
                continue
            name = re.sub(r'<[^>]+>', '', html.unescape(a_m.group(2))).strip()
            price_m = re.search(r"<div class='price'>(.*?)</div>", chunk, re.S)
            smalls = re.findall(r"<div class='small(?: [^']+)?'>(.*?)</div>", chunk, re.S)
            plain_smalls = [re.sub(r'<[^>]+>', '', html.unescape(s)).strip() for s in smalls]
            snippet = plain_smalls[-1] if plain_smalls else ''
            score = None
            reviews = 0
            for text_small in plain_smalls:
                m = re.search(r'評分\s+([0-9.]+)', text_small)
                if m:
                    score = float(m.group(1))
                m = re.search(r'評論\s+([0-9,]+)\s+則', text_small)
                if m:
                    reviews = int(m.group(1).replace(',', ''))
            pool.append({
                'name': name,
                'link': html.unescape(a_m.group(1)),
                'price': html.unescape(price_m.group(1)).strip() if price_m else '',
                'price_num': price_num(html.unescape(price_m.group(1))) if price_m else None,
                'score': score,
                'reviews': reviews,
                'snippet': snippet,
                'location_text': '',
                'rank_raw': idx,
                'occupancy_mode': occ_key,
                'target_search': search,
                'source_date': date,
                'source_kind': 'existing_report',
            })
    return pool


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
    if any('補位來源' in '；'.join(h.get('why') or []) for h in selected):
        notes.append('若同晚原始 Hotels.com 候選不足 5 間，會沿用同城市／另一 occupancy／相鄰落腳點既有 Hotels.com property pool 補位，並標示 approximate。')
    return notes


def build_scored(hotels: list[dict[str, object]], item: dict[str, str], occ: dict[str, str]) -> list[dict[str, object]]:
    scored = []
    for hotel in hotels:
        row = dict(hotel)
        score, reasons, approximate = selection_score(item, occ, row)
        row['selection_score'] = score
        row['why'] = reasons
        row['approximate'] = approximate
        scored.append(row)
    scored.sort(key=candidate_sort_key)
    return scored


def supplement_reason(source: str, item: dict[str, str], occ: dict[str, str], cand: dict[str, object]) -> str:
    src_occ = OCC_BY_KEY.get(str(cand.get('occupancy_mode') or occ['key']), occ)
    src_date = str(cand.get('source_date') or item['date'])
    src_search = str(cand.get('target_search') or item['search'])
    if source == 'same_date_other_occ':
        return f'補位來源：同晚另一 occupancy（{src_occ["label"]}）'
    if source == 'same_search_other_date_same_occ':
        return f'補位來源：同城市其他夜晚（{src_date}，{src_occ["label"]}）'
    if source == 'same_search_other_date_other_occ':
        return f'補位來源：同城市其他夜晚且另一 occupancy（{src_date}，{src_occ["label"]}）'
    if source == 'neighbor_search':
        return f'補位來源：相鄰落腳點 {src_search}（{src_date}，{src_occ["label"]}）'
    return '補位來源：既有 Hotels.com property pool'


def choose_five(item: dict[str, str], occ: dict[str, str], raw: dict[str, object], scored_lookup: dict[tuple[str, str], list[dict[str, object]]]) -> list[dict[str, object]]:
    selected = []
    seen = set()
    def add_many(cands: list[dict[str, object]], source: str | None = None):
        for cand in sorted(cands, key=candidate_sort_key):
            key = normalize_name(str(cand.get('name') or ''))
            if not key or key in seen:
                continue
            row = dict(cand)
            row['link'] = row.get('link') or str(raw.get('final_url') or raw.get('url') or hotels_url(item, occ))
            row.setdefault('target_search', item['search'])
            row.setdefault('source_date', item['date'])
            row.setdefault('occupancy_mode', occ['key'])
            if source:
                why = list(row.get('why') or [])
                why.append(supplement_reason(source, item, occ, row))
                row['why'] = why
                row['approximate'] = True
            selected.append(row)
            seen.add(key)
            if len(selected) >= 5:
                return
    add_many(scored_lookup.get((item['date'], occ['key']), []))
    other_occ = 'family_2rooms' if occ['key'] == 'family_1room' else 'family_1room'
    add_many(scored_lookup.get((item['date'], other_occ), []), 'same_date_other_occ')
    same_search_same_occ, same_search_other_occ, neighbor = [], [], []
    for other in ITINERARY:
        if other['date'] == item['date']:
            continue
        if other['search'] == item['search']:
            same_search_same_occ.extend(scored_lookup.get((other['date'], occ['key']), []))
            same_search_other_occ.extend(scored_lookup.get((other['date'], other_occ), []))
        elif other['search'] in FALLBACK_SEARCH_ORDER.get(item['search'], []):
            neighbor.extend(scored_lookup.get((other['date'], occ['key']), []))
            neighbor.extend(scored_lookup.get((other['date'], other_occ), []))
    add_many(same_search_same_occ, 'same_search_other_date_same_occ')
    add_many(same_search_other_occ, 'same_search_other_date_other_occ')
    add_many(neighbor, 'neighbor_search')
    return selected[:5]


def render_html(rows: list[dict[str, object]]):
    by_mode = {occ['key']: [] for occ in OCCS}
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
        f"<p class='meta'>來源：既有 Hotels.com probe JSON + 既有 Hotels.com family combined HTML property pool；在不重做 itinerary 的前提下，以最小侵入方式補齊每晚 5 間。固定條件：3 adults + 1 child age 10。更新時間：{esc(generated)}</p>",
        f"<p class='meta'>總說明：{esc(PRICE_WARNING)} 另因 Hotels.com 搜尋結果主要提供住宿頁連結，本文每筆均標示「{esc(LINK_WARNING)}」。若同晚不足 5 間，會沿用同城市／另一 occupancy／相鄰落腳點既有 Hotels.com property pool 補位，並標示 approximate。</p>",
        "<section class='card toc'><h2>內容導覽</h2><a href='#one-room'>1 room：每晚主動篩選 5 間</a><a href='#two-rooms'>2 rooms：每晚主動篩選 5 間</a></section>",
    ]
    for occ in OCCS:
        parts.append(f"<div id='{esc(occ['section_id'])}' class='section-title'><h2>{esc(occ['label'])}：每晚主動篩選 5 間</h2></div>")
        parts.append(f"<p class='meta'>{esc(PRICE_WARNING)} 若卡片地點或房型訊號不足，或需借用既有 Hotels.com pool 補位，會明確標記 approximate。</p>")
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


def main():
    existing_pool = parse_existing_report_pool()
    existing_by_name = defaultdict(list)
    for hotel in existing_pool:
        existing_by_name[normalize_name(str(hotel.get('name') or ''))].append(hotel)
    raw_lookup = {}
    for item in ITINERARY:
        for occ in OCCS:
            path = DATA_DIR / f"{slugify(item['search'])}_{item['date']}_{occ['key']}.json"
            raw = json.loads(path.read_text(encoding='utf-8'))
            raw['source_json'] = str(path)
            for hotel in raw.get('hotels', []):
                norm = normalize_name(str(hotel.get('name') or ''))
                if not hotel.get('link') and existing_by_name.get(norm):
                    hotel['link'] = existing_by_name[norm][0].get('link', '')
            raw_lookup[(item['date'], occ['key'])] = raw
    scored_lookup = {}
    for item in ITINERARY:
        for occ in OCCS:
            raw = raw_lookup[(item['date'], occ['key'])]
            hotels = list(raw.get('hotels', []))
            for hotel in existing_pool:
                if hotel.get('target_search') == item['search']:
                    hotels.append(dict(hotel))
            scored_lookup[(item['date'], occ['key'])] = build_scored(hotels, item, occ)
    rows = []
    for item in ITINERARY:
        for occ in OCCS:
            raw = raw_lookup[(item['date'], occ['key'])]
            selected = choose_five(item, occ, raw, scored_lookup)
            rows.append({
                'site': 'Hotels.com',
                'date': item['date'],
                'checkout': item['checkout'],
                'label': item['label'],
                'location_zh': item['location_zh'],
                'search': item['search'],
                'note': item['note'],
                'occupancy_key': occ['key'],
                'occupancy_label': occ['label'],
                'url': raw.get('final_url') or raw.get('url') or hotels_url(item, occ),
                'probe_source': raw.get('source_json'),
                'raw_text_path': raw.get('raw_text_path'),
                'screenshot': raw.get('screenshot'),
                'status': raw.get('status'),
                'title': raw.get('title'),
                'links_found': raw.get('links_found', 0),
                'hotels_found': raw.get('hotels_found', 0),
                'selected': selected,
                'notes': nightly_notes(item, occ, selected),
                'errors': raw.get('errors', []),
            })
    render_html(rows)
    approx = {occ['key']: [] for occ in OCCS}
    top5 = {}
    all_links = True
    for row in rows:
        if any(h.get('approximate') for h in row['selected']):
            approx[row['occupancy_key']].append(row['date'])
        top5[f"{row['date']}_{row['occupancy_key']}"] = len(row['selected'])
        all_links = all_links and all(bool(h.get('link')) for h in row['selected'])
    summary = {
        'site': 'Hotels.com',
        'output_html': str(REPORT_PATH),
        'data_sources_used': [str(DATA_DIR), str(REPORT_PATH), str(BASE / 'scripts' / 'rebuild_hotelscom_family_combined_minimal.py')],
        'approx_nights_by_mode': approx,
        'validation': {
            'top5_count_per_night': top5,
            'all_entries_have_links': all_links,
            'price_warning_included': PRICE_WARNING in REPORT_PATH.read_text(encoding='utf-8'),
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(REPORT_PATH)
    print(SUMMARY_PATH)


if __name__ == '__main__':
    main()
