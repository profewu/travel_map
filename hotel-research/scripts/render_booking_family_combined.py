#!/usr/bin/env python3
import html
import json
import re
import time
from pathlib import Path

BASE = Path('/home/profe/hotel-research')
DATA = BASE / 'data' / 'booking_ab' / 'cloak_all.json'
OUT_HTML = BASE / 'reports' / 'hokkaido_hotels_booking_family_combined.html'
OUT_JSON = BASE / 'reports' / 'hokkaido_hotels_booking_family_summary.json'

PRICE_WARNING = '這只是該日期查詢下平台卡片顯示的起始參考價，不是保證最終成交價。'
SELECTION_RULES = [
    '有價格優先',
    '評分/評論數優先',
    '地點吻合 itinerary 落腳點',
    '符合 3大1小住宿型態',
    '1 room 偏家庭/4人房訊號',
    '2 rooms 偏標準旅館型拆兩房穩妥度',
    '外圍區域降權',
    '無法確認 3大1小時標 approximate',
]
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
    ('family_1room', '1 room：每晚主動篩選 5 間', '3大1小（10歲）｜1間房（偏家庭/4人房訊號）'),
    ('family_2rooms', '2 rooms：每晚主動篩選 5 間', '3大1小（10歲）｜2間房（偏標準旅館型拆兩房）'),
]


def price_num(s: str):
    m = re.search(r'([0-9][0-9,]*)', s or '')
    return int(m.group(1).replace(',', '')) if m else None


def parse_score(score_text: str):
    m = re.search(r'Scored\s+([0-9.]+)', score_text or '')
    return float(m.group(1)) if m else None


def parse_reviews(score_text: str):
    m = re.search(r'([0-9][0-9,]*)\s+reviews', score_text or '', re.I)
    return int(m.group(1).replace(',', '')) if m else 0


def parse_distance(dist: str):
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*km', dist or '', re.I)
    return float(m.group(1)) if m else None


def detect_link_type(link: str):
    s = link or ''
    if not s:
        return 'missing'
    if any(k in s for k in ['matching_block_id=', 'all_sr_blocks=', 'highlighted_blocks=', 'sr_pri_blocks=']):
        return 'room-level'
    return 'property-level'


def search_area(search: str):
    s = (search or '').lower()
    if 'eniwa' in s:
        return 'eniwa'
    if 'noboribetsu' in s:
        return 'noboribetsu'
    if 'lake toya' in s:
        return 'lake_toya'
    if 'otaru' in s:
        return 'otaru'
    return 'sapporo'


def location_score(name: str, search: str, distance: float | None):
    n = (name or '').lower()
    area = search_area(search)
    score = 0.0
    notes = []
    if distance is not None:
        if distance <= 1.5:
            score += 18; notes.append('距離較接近核心區')
        elif distance <= 3:
            score += 12; notes.append('距離尚可')
        elif distance <= 5:
            score += 6
        elif distance <= 7:
            score += 2
        else:
            score -= 10; notes.append('距離偏外圍，已降權')
    if area == 'eniwa':
        if 'eniwa' in n or 'izari' in n:
            score += 16; notes.append('名稱較貼近惠庭/在地落腳點')
        if 'chitose' in n:
            score += 5; notes.append('接近新千歲緩衝圈')
        if 'village' in n and distance and distance > 7:
            score -= 6
    elif area == 'noboribetsu':
        if any(k in n for k in ['noboribetsu', 'takimoto', 'yumoto', 'miyabitei']):
            score += 16; notes.append('較貼近登別溫泉住宿圈')
        if 'green house' in n or 'horomisou' in n:
            score += 7
    elif area == 'lake_toya':
        if 'toya' in n:
            score += 14; notes.append('名稱貼近洞爺湖住宿圈')
        if 'windsor' in n:
            score -= 3
    elif area == 'otaru':
        if 'otaru' in n:
            score += 14; notes.append('名稱貼近小樽落腳點')
        if 'geihinkan' in n and distance and distance > 10:
            score -= 8; notes.append('距小樽核心較遠')
    elif area == 'sapporo':
        if any(k in n for k in ['odori', 'susukino', 'gracery', 'aspen', 'lamp light', 'koko', 'keio', 'bespoke', 'nakajima', 'sapporo']):
            score += 14; notes.append('看起來較接近札幌核心住宿圈')
        if 'moiwayama' in n:
            score -= 12; notes.append('偏藻岩山外圍，已降權')
    return score, notes


def occupancy_score(name: str, occ_key: str):
    n = (name or '').lower()
    score = 0.0
    approx = False
    notes = []
    familyish = ['family', 'minn', 'house', 'village', 'vacation', 'stay', 'guest house', 'garden', 'resort']
    standardish = ['hotel', 'inn', 'mystays', 'gracery', 'koko', 'keio', 'marriott', 'daiwa', 'vessel', 'park hotel']
    if occ_key == 'family_1room':
        if any(k in n for k in familyish):
            score += 14; notes.append('有家庭/整戶/度假型訊號')
        if any(k in n for k in ['hotel', 'inn']) and not any(k in n for k in ['resort', 'minn']):
            score -= 2
            approx = True
            notes.append('1 room 是否真能住 3大1小仍待房型頁確認')
        if 'minn' in n or 'stay' in n or 'house' in n:
            score += 5
        if 'moiwayama' in n:
            approx = True
    else:
        if any(k in n for k in standardish):
            score += 14; notes.append('偏標準旅館型，拆兩房較穩妥')
        if any(k in n for k in ['house', 'garden', 'guest house', 'village', 'vacation', 'minn', 'stay']):
            score += 4
            approx = True
            notes.append('可拆兩房可能性尚可，但仍需進房型頁確認')
        if 'resort' in n:
            score += 4
    return score, approx, notes


def rank_hotels(entry):
    ranked = []
    for idx, h in enumerate(entry.get('hotels') or [], 1):
        price = price_num(h.get('price', ''))
        score = parse_score(h.get('score', ''))
        reviews = parse_reviews(h.get('score', ''))
        distance = parse_distance(h.get('distance', ''))
        total = 0.0
        reasons = []
        approx_reasons = []
        if price is not None:
            total += 30
            reasons.append('有價格')
        else:
            total -= 20
            approx_reasons.append('卡片未顯示價格')
        if score is not None:
            total += score * 5
            reasons.append(f'評分 {score:.1f}')
        else:
            total -= 10
            approx_reasons.append('卡片缺少評分')
        if reviews:
            total += min(reviews / 120, 20)
            reasons.append(f'評論數 {reviews:,} 則')
        loc_score, loc_notes = location_score(h.get('name', ''), entry.get('search', ''), distance)
        total += loc_score
        reasons.extend(loc_notes)
        occ_score, approx, occ_notes = occupancy_score(h.get('name', ''), entry.get('occupancy_key', ''))
        total += occ_score
        reasons.extend(occ_notes)
        if approx:
            approx_reasons.append('住宿型態僅能近似判斷')
        ranked.append({
            **h,
            'source_rank': idx,
            'link_type': detect_link_type(h.get('link', '')),
            'price_num': price,
            'score_num': score,
            'reviews_num': reviews,
            'distance_km': distance,
            'selection_score': round(total, 2),
            'selection_reasons': reasons,
            'approximate': bool(approx_reasons),
            'approximate_reasons': approx_reasons,
        })
    ranked.sort(key=lambda x: (-x['selection_score'], x['source_rank']))
    return ranked


def note_for_entry(date: str, location: str, occ_key: str):
    notes = [
        '先按價格、評分/評論數與落腳點吻合度重排，不直接照 Booking 卡片原順序。',
        '所有價格都只可視為當次查詢卡片起始參考價。',
    ]
    if location == '札幌':
        notes.append('札幌搜尋仍可能混入藻岩山等外圍點，已人工降權，但仍屬近似篩選。')
    if location == '惠庭' and occ_key == 'family_1room':
        notes.append('惠庭樣本偏民宿/小型住宿，1 room 是否真能住 3大1小，多數仍需房型頁再確認。')
    if location == '洞爺湖' and occ_key == 'family_2rooms':
        notes.append('洞爺湖 2 rooms 多為高價溫泉/度假型或旅館，拆兩房可行性高於 1 room，但仍需看房型頁。')
    return notes


def render_html(entries_by_key, ranked_by_key):
    generated = time.strftime('%Y-%m-%d %H:%M:%S %Z')
    css = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:24px;color:#172033;background:#f6f7fb;line-height:1.55}
h1,h2,h3,h4{color:#101828}.meta{color:#667085}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:white;border:1px solid #e4e7ec;border-radius:14px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.05);margin:14px 0}.ok{color:#067647}.warn{color:#b54708}.bad{color:#b42318}.hotel{border-top:1px solid #eaecf0;padding:10px 0}.hotel:first-child{border-top:0}.price{font-weight:700;color:#175cd3}.small{font-size:12px;color:#667085}.pill{display:inline-block;border-radius:999px;padding:2px 8px;background:#eef4ff;color:#3538cd;font-size:12px;margin-left:6px}.occ{background:#fff7ed;color:#b54708}.approx{background:#fff1f3;color:#c01048}.why{margin-top:4px}.toc a{display:block;margin:6px 0;color:#175cd3}.section-title{position:sticky;top:0;background:#f6f7fb;padding:10px 0 2px;z-index:1}.disclaimer{background:#fffbeb}.rank{color:#667085}.score{color:#475467}@media(max-width:900px){.grid{grid-template-columns:1fr}}
a{color:#175cd3}
"""
    parts = [
        f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>北海道行程 Booking 主動篩選合併報告</title><style>{css}</style></head><body>",
        '<h1>北海道行程 Booking 主動篩選合併報告</h1>',
        f"<p class='meta'>來源：Booking CloakBrowser 既有 JSON + 既有 Booking 報告；住宿條件固定為 3 adults + 1 child age 10；依既有 itinerary 逐晚整理。更新時間：{html.escape(generated)}</p>",
        f"<div class='card disclaimer'><strong>總說明：</strong>此報告不是直接照平台原始前 5，而是以既有 Booking Cloak JSON 中可用樣本重新排序；{html.escape(PRICE_WARNING)} 由於目前優先重用既有 cloak JSON，未再做額外大抓取；若卡片本身無法確認 3大1小是否最終可住，會標示 approximate。</div>",
        '<section class="card toc"><h2>內容導覽</h2><a href="#family_1room">1 room：每晚主動篩選 5 間</a><a href="#family_2rooms">2 rooms：每晚主動篩選 5 間</a><p class="small">主要沿用：data/booking_ab/cloak_all.json、reports/hokkaido_hotels_booking_cloak_only_select.html、reports/hokkaido_hotels_booking_playwright_vs_cloak.html；格式參考：reports/hokkaido_hotels_trivago_family_combined.html</p></section>'
    ]
    for occ_key, section_title, occ_label in OCCS:
        parts.append(f"<div id='{occ_key}' class='section-title'><h2>{html.escape(section_title)}</h2></div>")
        parts.append(f"<p class='meta'>{html.escape(PRICE_WARNING)} 若條件符合度無法由卡片直接確認，會在每筆附近標 approximate。</p>")
        for item in ITINERARY:
            entry = entries_by_key[(item['date'], occ_key)]
            hotels = ranked_by_key[(item['date'], occ_key)]
            parts.append("<section class='card'>")
            parts.append(f"<h2>{html.escape(item['label'])} <span class='pill'>{html.escape(item['location_zh'])}</span></h2>")
            parts.append(f"<p class='meta'>住宿搜尋：{html.escape(item['search'])}｜入住：{item['date']}｜退房：{item['checkout']}｜備註：{html.escape(item['note'])}</p>")
            parts.append(f"<h3><span class='pill occ'>{html.escape(occ_label)}</span></h3>")
            parts.append("<div class='grid'>")
            parts.append("<div class='card'>")
            parts.append('<h4>此晚篩選提醒</h4><ul class="small">')
            for note in note_for_entry(item['date'], item['location_zh'], occ_key):
                parts.append(f'<li>{html.escape(note)}</li>')
            parts.append('</ul>')
            parts.append(f"<p class='small'>原始候選數：{len(entry.get('hotels') or [])}｜報告保留數：{len(hotels[:5])}｜property cards：{entry.get('property_card_count', 0)}</p>")
            parts.append('</div>')
            parts.append("<div class='card'>")
            parts.append(f"<h4>每晚最值得點開 5 間（{html.escape('1 room' if occ_key=='family_1room' else '2 rooms')}）</h4>")
            for idx, h in enumerate(hotels[:5], 1):
                name = html.escape(h.get('name', ''))
                link = h.get('link') or ''
                link_type = h.get('link_type', 'missing')
                link_html = f"<a href='{html.escape(link)}' target='_blank' rel='noreferrer'>{name}</a>" if link else name
                approx_badge = " <span class='pill approx'>approximate</span>" if h['approximate'] else ''
                link_badge = f" <span class='pill'>{html.escape(link_type)}</span>" if link else " <span class='pill approx'>missing link</span>"
                detail_bits = []
                if h.get('score'):
                    detail_bits.append(h['score'])
                if h.get('distance'):
                    detail_bits.append(h['distance'])
                parts.append("<div class='hotel'>")
                parts.append(f"<div><strong>{idx}. {link_html}</strong>{link_badge}{approx_badge} <span class='small rank'>（原 Booking 卡片序位 #{h['source_rank']}）</span></div>")
                parts.append(f"<div class='price'>{html.escape(h.get('price') or '價格未顯示')}</div>")
                parts.append(f"<div class='small'>{html.escape(PRICE_WARNING)}</div>")
                if detail_bits:
                    parts.append(f"<div class='small'>{html.escape('｜'.join(detail_bits))}</div>")
                parts.append(f"<div class='small score'>篩選分數：{h['selection_score']}</div>")
                parts.append(f"<div class='small why'>入選原因：{html.escape('；'.join(h['selection_reasons']) or '依綜合規則保留')}</div>")
                if h['approximate_reasons']:
                    parts.append(f"<div class='small warn'>approximate 原因：{html.escape('；'.join(h['approximate_reasons']))}</div>")
                parts.append(f"<div class='small'><a href='{html.escape(link)}' target='_blank' rel='noreferrer'>開啟 Booking {html.escape(link_type)} 連結</a></div>" if link else "<div class='small bad'>缺少連結</div>")
                parts.append("</div>")
            parts.append('</div></div></section>')
    parts.append('</body></html>')
    return '\n'.join(parts)


def build_summary(entries_by_key, ranked_by_key):
    approx = {'family_1room': [], 'family_2rooms': []}
    top1 = {}
    for item in ITINERARY:
        top1[item['date']] = {}
        for occ_key, _, _ in OCCS:
            ranked = ranked_by_key[(item['date'], occ_key)]
            approx_hit = any(h['approximate'] for h in ranked[:5])
            if approx_hit:
                approx[occ_key].append(item['date'])
            h = ranked[0]
            top1[item['date']][occ_key] = {
                'name': h['name'],
                'price': h.get('price'),
                'score': h.get('score'),
                'distance': h.get('distance'),
                'link': h.get('link'),
                'link_type': h.get('link_type'),
                'selection_score': h['selection_score'],
                'approximate': h['approximate'],
            }
    top5_link_types = {f"{item['date']}_{occ_key}": [h.get('link_type') for h in ranked_by_key[(item['date'], occ_key)][:5]] for item in ITINERARY for occ_key, _, _ in OCCS}
    return {
        'site': 'Booking.com',
        'output_html': str(OUT_HTML),
        'output_exists': OUT_HTML.exists(),
        'data_sources_used': [
            str(DATA),
            str(BASE / 'reports' / 'hokkaido_hotels_booking_cloak_only_select.html'),
            str(BASE / 'reports' / 'hokkaido_hotels_booking_playwright_vs_cloak.html'),
            str(BASE / 'scripts' / 'booking_itinerary_ab.py'),
            str(BASE / 'reports' / 'hokkaido_hotels_trivago_family_combined.html'),
        ],
        'scripts_used_or_created': [
            str(BASE / 'scripts' / 'render_cloak_only_report.py'),
            str(BASE / 'scripts' / 'render_booking_family_combined.py'),
        ],
        'selection_rules_applied': SELECTION_RULES,
        'approx_nights_by_mode': approx,
        'validation': {
            'nights_expected': len(ITINERARY),
            'nights_found_per_mode': {occ_key: sum(1 for item in ITINERARY if (item['date'], occ_key) in entries_by_key) for occ_key, _, _ in OCCS},
            'top5_count_per_night': {f"{item['date']}_{occ_key}": len(ranked_by_key[(item['date'], occ_key)][:5]) for item in ITINERARY for occ_key, _, _ in OCCS},
            'all_entries_have_links': all(bool(h.get('link')) for ranked in ranked_by_key.values() for h in ranked[:5]),
            'all_top5_links_labeled': all(h.get('link_type') in {'room-level', 'property-level'} for ranked in ranked_by_key.values() for h in ranked[:5]),
            'top5_link_types_per_night': top5_link_types,
            'used_existing_cloak_json_only': True,
            'minimal_refetch_performed': False,
            'price_warning_included': True,
        },
        'top1_by_night': top1,
    }


def main():
    arr = json.loads(DATA.read_text(encoding='utf-8'))
    entries_by_key = {(r['date'], r['occupancy_key']): r for r in arr}
    ranked_by_key = {}
    for item in ITINERARY:
        for occ_key, _, _ in OCCS:
            ranked_by_key[(item['date'], occ_key)] = rank_hotels(entries_by_key[(item['date'], occ_key)])
    OUT_HTML.write_text(render_html(entries_by_key, ranked_by_key), encoding='utf-8')
    summary = build_summary(entries_by_key, ranked_by_key)
    summary['output_exists'] = OUT_HTML.exists()
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(OUT_HTML)
    print(OUT_JSON)


if __name__ == '__main__':
    main()
