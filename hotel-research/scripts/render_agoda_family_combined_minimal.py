#!/usr/bin/env python3
import difflib
import html
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

BASE = Path('/home/profe/hotel-research')
SOURCE = BASE / 'data' / 'multisite' / 'combined_3sites.json'
OUT_HTML = BASE / 'reports' / 'hokkaido_hotels_agoda_family_combined.html'
OUT_JSON = BASE / 'reports' / 'hokkaido_hotels_agoda_family_summary.json'
CACHE_JSON = BASE / 'data' / 'agoda_suggest_cache.json'
SUGGEST_URL = 'https://www.agoda.com/api/cronos/search/GetUnifiedSuggestResult/3/1/1/0/'
HEADERS = {
    'user-agent': 'Mozilla/5.0',
    'accept': 'application/json,text/plain,*/*',
    'referer': 'https://www.agoda.com/',
}
PRICE_WARNING = 'Agoda 此版僅完成 property-level 連結補全；未直接抓到同日期同入住條件的 Agoda dated card price，故所有價格統一標示為 price unavailable。'
GLOBAL_APPROX = '這是因 Agoda dated search 資料不足而做的近似補全：本報告先沿用既有他站候選池，再以 Agoda unified suggest API 對應成 Agoda property-level 連結。'
ITINERARY = [
    {'date': '2026-06-25', 'label': '6/25 抵達新千歲，惠庭緩衝', 'location_zh': '惠庭', 'search': 'Eniwa, Hokkaido, Japan', 'checkout': '2026-06-26', 'note': '抵達新千歲後在惠庭緩衝'},
    {'date': '2026-06-26', 'label': '6/26 惠庭親子活動、支笏湖，進登別', 'location_zh': '登別', 'search': 'Noboribetsu, Hokkaido, Japan', 'checkout': '2026-06-27', 'note': '經支笏湖後入住登別'},
    {'date': '2026-06-27', 'label': '6/27 登別、白老、室蘭，夜宿洞爺湖', 'location_zh': '洞爺湖', 'search': 'Lake Toya, Hokkaido, Japan', 'checkout': '2026-06-28', 'note': '夜宿洞爺湖'},
    {'date': '2026-06-28', 'label': '6/28 洞爺湖轉場小樽', 'location_zh': '小樽', 'search': 'Otaru, Hokkaido, Japan', 'checkout': '2026-06-29', 'note': '洞爺湖轉場小樽'},
    {'date': '2026-06-29', 'label': '6/29 鱗友朝市，小樽到札幌', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'checkout': '2026-06-30', 'note': '小樽到札幌'},
    {'date': '2026-06-30', 'label': '6/30 札幌購物與親子緩衝', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'checkout': '2026-07-01', 'note': '札幌購物與親子緩衝'},
    {'date': '2026-07-01', 'label': '7/1 札幌地下街、薄野與藻岩山', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'checkout': '2026-07-02', 'note': '札幌地下街、薄野與藻岩山'},
    {'date': '2026-07-02', 'label': '7/2 札幌自由日與機場巴士確認', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'checkout': '2026-07-03', 'note': '札幌自由日與機場巴士確認'},
]
OCCS = [
    ('family_1room', '1 room：每晚 5 間 Agoda property links', '3大1小（10歲）｜1間房'),
    ('family_2rooms', '2 rooms：每晚 5 間 Agoda property links', '3大1小（10歲）｜2間房'),
]
CITY_HINTS = {
    'Eniwa, Hokkaido, Japan': ['Eniwa', 'Chitose', 'Sapporo'],
    'Noboribetsu, Hokkaido, Japan': ['Noboribetsu'],
    'Lake Toya, Hokkaido, Japan': ['Lake Toya', 'Toya', 'Toyako', 'Toyoura', 'Sobetsu'],
    'Otaru, Hokkaido, Japan': ['Otaru'],
    'Sapporo, Hokkaido, Japan': ['Sapporo'],
}


def load_cache():
    if CACHE_JSON.exists():
        return json.loads(CACHE_JSON.read_text())
    return {}


def save_cache(cache):
    CACHE_JSON.write_text(json.dumps(cache, ensure_ascii=False, indent=2))


def normalize(text: str) -> str:
    text = (text or '').lower().strip()
    text = text.replace('’', "'").replace('【', '').replace('】', '')
    text = re.sub(r'\bhotel\b', ' hotel ', text)
    text = re.sub(r'[^\w\u3040-\u30ff\u4e00-\u9fff]+', '', text)
    return text


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def location_score(search: str, city_name: str) -> int:
    city = (city_name or '').lower()
    score = 0
    for hint in CITY_HINTS.get(search, []):
        if hint.lower() in city:
            score += 10
    return score


def build_query_variants(name: str, search: str):
    variants = [name]
    city_hints = CITY_HINTS.get(search, [])
    if city_hints:
        variants.append(f'{name} {city_hints[0]}')
    if ' - ' in name:
        variants.append(name.split(' - ')[0].strip())
    if ':' in name:
        variants.append(name.split(':')[0].strip())
    m = re.split(r'\s+[\-–]\s+|\s*\(.*?\)\s*', name)
    if m and m[0].strip() and m[0].strip() not in variants:
        variants.append(m[0].strip())
    dedup = []
    seen = set()
    for v in variants:
        key = v.strip().lower()
        if key and key not in seen:
            seen.add(key)
            dedup.append(v.strip())
    return dedup


def agoda_link(object_id: int, item: dict) -> str:
    params = {
        'checkIn': item['date'],
        'checkOut': item['checkout'],
        'rooms': '1' if item['occupancy_key'] == 'family_1room' else '2',
        'adults': '3',
        'children': '1',
        'childages': '10',
        'textToSearch': item['search'],
        'selectedproperty': str(object_id),
        'hotel': str(object_id),
        'familyMode': 'on',
    }
    return 'https://www.agoda.com/search?' + urlencode(params)


def choose_candidate(name: str, search: str, payload: dict):
    candidates = [x for x in (payload.get('ViewModelList') or []) if x.get('IsHotel') or x.get('PageTypeId') == 7]
    if not candidates:
        return None
    best = None
    best_score = -10**9
    for c in candidates:
        cand_name = c.get('Name') or ''
        ratio = similarity(name, cand_name)
        score = int(ratio * 100)
        if normalize(name) == normalize(cand_name):
            score += 100
        if c.get('CountryId') == 3:
            score += 20
        score += location_score(search, c.get('CityName') or '')
        if c.get('ObjectId'):
            score += 5
        if best is None or score > best_score:
            best = c
            best_score = score
    if best is None:
        return None
    return {
        'candidate': best,
        'match_score': best_score,
        'name_ratio': round(similarity(name, best.get('Name') or ''), 4),
    }


def lookup_agoda(name: str, search: str, item: dict, cache: dict):
    cache_key = f'{search}::{name}'
    if cache_key in cache:
        return cache[cache_key]
    best_result = None
    used_query = None
    for q in build_query_variants(name, search):
        resp = requests.get(SUGGEST_URL, params={'searchText': q}, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        chosen = choose_candidate(name, search, payload)
        if chosen and (best_result is None or chosen['match_score'] > best_result['match_score']):
            best_result = chosen
            used_query = q
        if chosen and chosen['match_score'] >= 130:
            break
    if not best_result:
        raise RuntimeError(f'No Agoda suggest match for {name} / {search}')
    c = best_result['candidate']
    match_level = 'high' if best_result['match_score'] >= 130 else ('medium' if best_result['match_score'] >= 90 else 'low')
    result = {
        'query_used': used_query,
        'match_level': match_level,
        'match_score': best_result['match_score'],
        'name_ratio': best_result['name_ratio'],
        'agoda_name': c.get('Name'),
        'agoda_city': c.get('CityName'),
        'object_id': c.get('ObjectId'),
        'page_type_id': c.get('PageTypeId'),
        'country_id': c.get('CountryId'),
        'link': agoda_link(c.get('ObjectId'), item),
    }
    cache[cache_key] = result
    return result


def load_source_sections():
    raw = json.loads(SOURCE.read_text())
    sections = {}
    for entry in raw:
        if entry.get('site') != 'Booking.com':
            continue
        key = (entry['date'], entry['occupancy_key'])
        sections[key] = entry
    return sections


def note_for(date: str, location: str, occ_key: str):
    notes = [
        '先沿用既有他站候選池，再逐筆用 Agoda unified suggest API 轉成 Agoda property-level link。',
        PRICE_WARNING,
        GLOBAL_APPROX,
    ]
    if location == '惠庭':
        notes.append('惠庭 Agoda suggest 對應常落在 Sapporo/Chitose 城市欄位，但 property 名稱可對上，故仍保留並標 approximate。')
    if location == '札幌':
        notes.append('札幌幾晚未另抓 Agoda dated search 卡片，因此此區全部屬 approximate 補全。')
    if occ_key == 'family_2rooms':
        notes.append('2 rooms 僅代表搜尋條件會帶 2 rooms；未抓到 Agoda 當日房型分配卡片，仍需點入房型頁確認。')
    return notes


def render_html(mapped_sections, summary):
    generated = time.strftime('%Y-%m-%d %H:%M:%S %Z')
    css = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:24px;color:#172033;background:#f6f7fb;line-height:1.55}
h1,h2,h3,h4{color:#101828}.meta{color:#667085}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:white;border:1px solid #e4e7ec;border-radius:14px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.05);margin:14px 0}.hotel{border-top:1px solid #eaecf0;padding:10px 0}.hotel:first-child{border-top:0}.price{font-weight:700;color:#175cd3}.small{font-size:12px;color:#667085}.warn{color:#b54708}.pill{display:inline-block;border-radius:999px;padding:2px 8px;background:#eef4ff;color:#3538cd;font-size:12px;margin-left:6px}.occ{background:#fff7ed;color:#b54708}.approx{background:#fff1f3;color:#c01048}.disclaimer{background:#fffbeb}.toc a{display:block;margin:6px 0;color:#175cd3}.section-title{position:sticky;top:0;background:#f6f7fb;padding:10px 0 2px;z-index:1}.ok{color:#067647}@media(max-width:900px){.grid{grid-template-columns:1fr}}a{color:#175cd3}
"""
    parts = [
        f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>北海道行程 Agoda family combined</title><style>{css}</style></head><body>",
        '<h1>北海道行程 Agoda family combined（minimal deliverable）</h1>',
        f"<p class='meta'>來源：data/multisite/combined_3sites.json 中既有 Booking.com nightly candidate pool + Agoda unified suggest API property mapping；固定住宿條件 3 adults + 1 child age 10；更新時間：{html.escape(generated)}</p>",
        f"<div class='card disclaimer'><strong>總說明：</strong>{html.escape(GLOBAL_APPROX)} {html.escape(PRICE_WARNING)} 因此本報告所有項目都會標示 approximate，但每筆都補上可點的 Agoda property-level link。</div>",
        '<section class="card toc"><h2>內容導覽</h2><a href="#family_1room">1 room：每晚 5 間 Agoda property links</a><a href="#family_2rooms">2 rooms：每晚 5 間 Agoda property links</a><p class="small">本次最小交付只完成 Agoda 單站 HTML，不重做 itinerary，不重跑其他站大抓取。</p></section>'
    ]
    for occ_key, title, occ_label in OCCS:
        parts.append(f"<div id='{occ_key}' class='section-title'><h2>{html.escape(title)}</h2></div>")
        parts.append(f"<p class='meta'>{html.escape(PRICE_WARNING)} 所有條目均標 approximate。</p>")
        for item in ITINERARY:
            hotels = mapped_sections[(item['date'], occ_key)]
            parts.append("<section class='card'>")
            parts.append(f"<h2>{html.escape(item['label'])} <span class='pill'>{html.escape(item['location_zh'])}</span></h2>")
            parts.append(f"<p class='meta'>住宿搜尋：{html.escape(item['search'])}｜入住：{item['date']}｜退房：{item['checkout']}｜備註：{html.escape(item['note'])}</p>")
            parts.append(f"<h3><span class='pill occ'>{html.escape(occ_label)}</span> <span class='pill approx'>all approximate</span></h3>")
            parts.append("<div class='grid'>")
            parts.append("<div class='card'>")
            parts.append('<h4>此晚補全提醒</h4><ul class="small">')
            for note in note_for(item['date'], item['location_zh'], occ_key):
                parts.append(f'<li>{html.escape(note)}</li>')
            parts.append('</ul>')
            parts.append(f"<p class='small'>來源候選池：Booking.com 既有 nightly candidates｜保留數：{len(hotels)}｜每筆皆有 Agoda 連結：<span class='ok'>{'yes' if all(h['agoda_link'] for h in hotels) else 'no'}</span></p>")
            parts.append('</div>')
            parts.append("<div class='card'>")
            parts.append("<h4>每晚 5 間 Agoda property-level links</h4>")
            for idx, h in enumerate(hotels, 1):
                name = html.escape(h['source_name'])
                link = html.escape(h['agoda_link'])
                match_badge = html.escape(h['match_level'])
                parts.append("<div class='hotel'>")
                parts.append(f"<div><strong>{idx}. <a href='{link}' target='_blank' rel='noreferrer'>{name}</a></strong> <span class='pill'>Agoda link</span> <span class='pill approx'>approximate</span> <span class='pill'>match {match_badge}</span></div>")
                parts.append("<div class='price'>price unavailable</div>")
                parts.append(f"<div class='small warn'>{html.escape(PRICE_WARNING)}</div>")
                parts.append(f"<div class='small'>來源候選池：{html.escape(h['source_site'])}｜來源參考價：{html.escape(h['source_price'] or 'unavailable')}｜來源評分：{html.escape(h['source_score'] or 'unavailable')}｜來源距離：{html.escape(h['source_distance'] or 'unavailable')}</div>")
                parts.append(f"<div class='small'>Agoda suggest 對應：{html.escape(h['agoda_name'])}｜city: {html.escape(h['agoda_city'] or 'unavailable')}｜selectedproperty: {h['object_id']}｜PageTypeId: {h['page_type_id']}</div>")
                parts.append(f"<div class='small'>近似判斷：僅完成 Agoda property mapping，未取得該晚 Agoda dated price / rating；occupancy 最終可售仍需點入房型頁確認。</div>")
                parts.append(f"<div class='small'>對應說明：query = {html.escape(h['query_used'])}｜name ratio = {h['name_ratio']:.2f}｜match score = {h['match_score']}</div>")
                parts.append(f"<div class='small'><a href='{link}' target='_blank' rel='noreferrer'>開啟 Agoda property-level link</a></div>")
                parts.append("</div>")
            parts.append("</div></div></section>")
    parts.append("</body></html>")
    OUT_HTML.write_text(''.join(parts))


def main():
    cache = load_cache()
    sections = load_source_sections()
    mapped_sections = {}
    approx_nights = {'family_1room': [], 'family_2rooms': []}
    for occ_key, _, _ in OCCS:
        approx_nights[occ_key] = [x['date'] for x in ITINERARY]
        for item in ITINERARY:
            key = (item['date'], occ_key)
            entry = sections[key]
            hotels = []
            for source_hotel in entry['hotels'][:5]:
                agoda = lookup_agoda(source_hotel['name'], entry['search'], {**item, 'occupancy_key': occ_key}, cache)
                hotels.append({
                    'source_site': entry['site'],
                    'source_name': source_hotel['name'],
                    'source_price': source_hotel.get('price') or 'unavailable',
                    'source_score': source_hotel.get('score') or 'unavailable',
                    'source_distance': source_hotel.get('distance') or 'unavailable',
                    'agoda_link': agoda['link'],
                    'agoda_name': agoda['agoda_name'],
                    'agoda_city': agoda['agoda_city'],
                    'object_id': agoda['object_id'],
                    'page_type_id': agoda['page_type_id'],
                    'match_level': agoda['match_level'],
                    'match_score': agoda['match_score'],
                    'name_ratio': agoda['name_ratio'],
                    'query_used': agoda['query_used'],
                    'approximate': True,
                })
            mapped_sections[key] = hotels
    save_cache(cache)
    summary = {
        'output_html': str(OUT_HTML),
        'source_file': str(SOURCE),
        'source_site_used_per_night': 'Booking.com entries embedded inside combined_3sites.json',
        'agoda_suggest_endpoint': SUGGEST_URL,
        'approx_nights_by_mode': approx_nights,
        'all_entries_approximate': True,
        'validation': {
            'night_sections_expected_total': len(ITINERARY) * len(OCCS),
            'night_sections_found_total': len(mapped_sections),
            'top5_count_per_night': {f'{date}_{occ}': len(hotels) for (date, occ), hotels in mapped_sections.items()},
            'all_entries_have_links': all(h['agoda_link'] for hotels in mapped_sections.values() for h in hotels),
            'all_entries_have_selectedproperty_links': all('selectedproperty=' in h['agoda_link'] and 'hotel=' in h['agoda_link'] for hotels in mapped_sections.values() for h in hotels),
        },
        'sample_mappings': {
            f'{date}_{occ}': [{'source_name': h['source_name'], 'agoda_name': h['agoda_name'], 'agoda_link': h['agoda_link']} for h in hotels[:2]]
            for (date, occ), hotels in list(mapped_sections.items())[:4]
        },
    }
    render_html(mapped_sections, summary)
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
