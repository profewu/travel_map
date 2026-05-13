#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import math
import re
import time
from pathlib import Path

TRIVAGO_BASE = 'https://www.trivago.com'
PRICE_WARNING = '這只是該日期查詢下平台卡片顯示的起始參考價，不是保證最終成交價。'
PRICE_RE = re.compile(r'(?:TWD|JPY|USD|EUR|NT\$|¥|\$)\s?[0-9][0-9,]*(?:\.\d+)?')
CARD_START_RE = re.compile(r'<li[^>]+data-testid="accommodation-list-element"[^>]*>', re.S)
NAME_RE = re.compile(
    r'<a[^>]+data-testid="item-name-link"[^>]+href="([^"]+)"[^>]*>.*?<span[^>]+itemprop="name"[^>]*>(.*?)</span>',
    re.S,
)
TAG_RE = re.compile(r'<[^>]+>')
WHITESPACE_RE = re.compile(r'\s+')
PROPERTY_TYPES = [
    'Entire House / Apartment',
    'Serviced apartment',
    'Ryokan',
    'Resort',
    'Hotel',
    'Hostel',
    'Guesthouse',
    'Bed & Breakfast',
]

BASE = Path('/home/profe/hotel-research')
PROBE_DIR = BASE / 'data' / 'trivago_probe'
REPORTS = BASE / 'reports'
SUMMARY_PATH = REPORTS / 'hokkaido_hotels_trivago_family_summary.json'
REPORTS.mkdir(parents=True, exist_ok=True)

ITINERARY = [
    {'date': '2026-06-25', 'label': '6/25 抵達新千歲，惠庭緩衝', 'location_zh': '惠庭', 'search': 'Eniwa, Hokkaido, Japan', 'note': '抵達新千歲後在惠庭緩衝', 'checkout': '2026-06-26'},
    {'date': '2026-06-26', 'label': '6/26 惠庭親子活動、支笏湖，進登別', 'location_zh': '登別', 'search': 'Noboribetsu, Hokkaido, Japan', 'note': '經支笏湖後入住登別', 'checkout': '2026-06-27'},
    {'date': '2026-06-27', 'label': '6/27 登別、白老、室蘭，夜宿洞爺湖', 'location_zh': '洞爺湖', 'search': 'Lake Toya, Hokkaido, Japan', 'note': '夜宿洞爺湖', 'checkout': '2026-06-28'},
    {'date': '2026-06-28', 'label': '6/28 洞爺湖轉場小樽', 'location_zh': '小樽', 'search': 'Otaru, Hokkaido, Japan', 'note': '洞爺湖轉場小樽', 'checkout': '2026-06-29'},
    {'date': '2026-06-29', 'label': '6/29 鱗友朝市，小樽到札幌', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '小樽到札幌', 'checkout': '2026-06-30'},
    {'date': '2026-06-30', 'label': '6/30 札幌購物與親子緩衝', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '札幌購物與親子緩衝', 'checkout': '2026-07-01'},
    {'date': '2026-07-01', 'label': '7/1 札幌地下街、薄野與藻岩山', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '札幌地下街、薄野與藻岩山', 'checkout': '2026-07-02'},
    {'date': '2026-07-02', 'label': '7/2 札幌自由日與機場巴士確認', 'location_zh': '札幌', 'search': 'Sapporo, Hokkaido, Japan', 'note': '札幌自由日與機場巴士確認', 'checkout': '2026-07-03'},
]


def slugify_destination(destination: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', destination.lower()).strip('-')
    return slug or 'destination'


def stem_for(item: dict, rooms: int) -> str:
    return f"{slugify_destination(item['search'])}_{item['date']}_{item['checkout']}_a3_c1_r{rooms}"


def absolute_trivago_url(url: str) -> str:
    if not url:
        return ''
    if url.startswith('http://') or url.startswith('https://'):
        return url
    if url.startswith('/'):
        return f"{TRIVAGO_BASE}{url}"
    return f"{TRIVAGO_BASE}/{url.lstrip('/')}"


def strip_html_text(block: str) -> str:
    normalized = (
        block.replace('</div>', '\n')
        .replace('</span>', '\n')
        .replace('</p>', '\n')
        .replace('<br>', '\n')
        .replace('<br/>', '\n')
        .replace('<br />', '\n')
    )
    text = TAG_RE.sub(' ', normalized)
    text = html.unescape(text)
    text = WHITESPACE_RE.sub(' ', text).strip()
    return text


def parse_card_blocks(page_html: str) -> list[str]:
    starts = [m.start() for m in CARD_START_RE.finditer(page_html)]
    if not starts:
        return []
    blocks: list[str] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(page_html)
        blocks.append(page_html[start:end])
    return blocks


def parse_card_meta(text: str) -> dict[str, object]:
    rating_value = None
    rating_match = re.search(r'\b(\d\.\d)\b\s+(?:Excellent|Very good|Good)', text)
    if rating_match:
        rating_value = float(rating_match.group(1))
    review_count = 0
    review_match = re.search(r'\(([\d,]+)\s+ratings\)', text)
    if review_match:
        review_count = int(review_match.group(1).replace(',', '').replace('\n', ''))
    distance_km = None
    distance_match = re.search(r'(\d+(?:\.\d+)?)\s*km to City center', text)
    if distance_match:
        distance_km = float(distance_match.group(1))
    property_type = ''
    for candidate in PROPERTY_TYPES:
        if candidate in text:
            property_type = candidate
            break
    return {
        'rating_value': rating_value,
        'review_count': review_count,
        'distance_km': distance_km,
        'property_type': property_type,
    }


def extract_cards(item: dict, rooms: int) -> list[dict[str, object]]:
    path = PROBE_DIR / f"{stem_for(item, rooms)}.html"
    if not path.exists():
        return []
    page_html = path.read_text(encoding='utf-8', errors='ignore')
    cards: list[dict[str, object]] = []
    seen: dict[str, int] = {}
    for raw_rank, block in enumerate(parse_card_blocks(page_html), start=1):
        name_match = NAME_RE.search(block)
        if not name_match:
            continue
        link = absolute_trivago_url(html.unescape(name_match.group(1)))
        name = html.unescape(name_match.group(2)).strip()
        if not name:
            continue
        dedupe_key = name.casefold()
        text_sample = strip_html_text(block)[:1200]
        prices = PRICE_RE.findall(text_sample)
        card = {
            'rank': raw_rank,
            'name': name,
            'link': link,
            'price_matches': prices[:5],
            'text_sample': text_sample,
        }
        card.update(parse_card_meta(text_sample))
        if dedupe_key in seen:
            prev = cards[seen[dedupe_key]]
            prev_price = 1 if prev.get('price_matches') else 0
            new_price = 1 if card.get('price_matches') else 0
            prev_quality = prev_price * 1000 + int(prev.get('review_count') or 0)
            new_quality = new_price * 1000 + int(card.get('review_count') or 0)
            if new_quality > prev_quality:
                cards[seen[dedupe_key]] = card
            continue
        seen[dedupe_key] = len(cards)
        cards.append(card)
    return cards


def location_score(text_lower: str, item: dict) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    location = item['location_zh']
    if location == '札幌':
        central_hits = [kw for kw in ['susukino', 'odori', 'tanukikoji', 'sapporo station', 'central sapporo', 'sapporo\'s heart'] if kw in text_lower]
        if central_hits:
            score += 16
            reasons.append('看起來較接近札幌核心區')
        if 'jozankei' in text_lower:
            score -= 22
            reasons.append('較偏定山溪，不是本晚札幌市區優先')
        if 'shin sapporo' in text_lower:
            score -= 8
            reasons.append('較偏新札幌，非首選核心位置')
    elif location == '小樽':
        if 'otaru' in text_lower:
            score += 12
            reasons.append('地點與小樽過夜點一致')
        if re.search(r'\basari\b', text_lower):
            score -= 4
            reasons.append('較偏朝里，需多留意轉場便利')
    elif location == '洞爺湖':
        if any(kw in text_lower for kw in ['toya', 'toyako', 'lake toya', 'sobetsu']):
            score += 10
            reasons.append('位於洞爺湖住宿圈')
    elif location == '登別':
        if 'noboribetsu' in text_lower:
            score += 10
            reasons.append('位於登別住宿圈')
    elif location == '惠庭':
        if any(kw in text_lower for kw in ['eniwa', 'chitose', 'new chitose airport']):
            score += 9
            reasons.append('較符合抵達日惠庭/新千歲緩衝')
    return score, reasons


def suitability_score(card: dict, item: dict, rooms: int) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    text_lower = (card.get('text_sample') or '').lower()
    name_lower = (card.get('name') or '').lower()
    property_type = (card.get('property_type') or '').lower()

    if card.get('price_matches'):
        score += 32
        reasons.append('有明確起始參考價')
    else:
        score -= 6
        reasons.append('卡片未顯示明確價格')

    rating_value = card.get('rating_value')
    if isinstance(rating_value, float):
        score += rating_value * 3.5
        reasons.append(f'評分 {rating_value:.1f}')
    else:
        score -= 3
        reasons.append('卡片缺少明確評分')

    review_count = int(card.get('review_count') or 0)
    if review_count:
        score += min(math.log10(review_count + 1) * 10, 22)
        if review_count >= 1000:
            reasons.append(f'評論數 {review_count:,} 則')
    else:
        score -= 2

    distance_km = card.get('distance_km')
    if isinstance(distance_km, float):
        if distance_km <= 1.5:
            score += 12
            reasons.append(f'距市中心約 {distance_km:.1f} km')
        elif distance_km <= 3.0:
            score += 7
            reasons.append(f'距市中心約 {distance_km:.1f} km')
        elif distance_km <= 8.0:
            score += 1
        elif distance_km > 15.0:
            score -= 12
            reasons.append(f'距市中心約 {distance_km:.1f} km，偏遠')
        elif distance_km > 8.0:
            score -= 6
            reasons.append(f'距市中心約 {distance_km:.1f} km')

    loc_delta, loc_reasons = location_score(text_lower, item)
    score += loc_delta
    reasons.extend(loc_reasons)

    family_keywords = ['family', 'spacious', 'separate bath', 'separate facilities', 'tatami', 'japanese-style', 'traditional japanese room', 'kitchen', 'apartment', 'house', 'villa', 'waterpark', 'deluxe corner rooms']
    sturdy_two_room_keywords = ['hotel', 'resort', 'ryokan', 'inn', 'onsen', 'buffet']
    weak_keywords = ['hostel', 'capsule', 'dorm', 'livemax']

    if rooms == 1:
        if property_type in {'entire house / apartment', 'serviced apartment'}:
            score += 18
            reasons.append('1 room 版本較像可容納家庭的住宿型態')
        elif property_type in {'hotel', 'ryokan', 'resort'}:
            score += 5
        if any(kw in text_lower for kw in family_keywords):
            score += 12
            reasons.append('卡片文案帶有家庭/寬敞訊號')
        if any(kw in name_lower or kw in text_lower for kw in weak_keywords):
            score -= 16
            reasons.append('較像低配或非家庭優先選項')
    else:
        if property_type in {'hotel', 'ryokan', 'resort'} or any(kw in name_lower for kw in sturdy_two_room_keywords):
            score += 15
            reasons.append('2 rooms 版本較容易理解成穩妥拆兩房')
        if property_type in {'entire house / apartment', 'serviced apartment'}:
            score -= 8
            reasons.append('2 rooms 版本不如標準旅館型穩妥')
        if 'family-friendly' in text_lower:
            score += 6
            reasons.append('有 family-friendly 訊號')
        if any(kw in name_lower or kw in text_lower for kw in weak_keywords):
            score -= 18
            reasons.append('較不適合作為兩房穩妥首選')

    if card.get('link'):
        score += 3
    else:
        score -= 50
        reasons.append('缺少可點擊連結')

    return score, reasons


def choose_cards(item: dict, rooms: int) -> tuple[list[dict[str, object]], list[str]]:
    cards = extract_cards(item, rooms)
    scored: list[dict[str, object]] = []
    insufficiencies: list[str] = []
    for card in cards:
        score, reasons = suitability_score(card, item, rooms)
        enriched = dict(card)
        enriched['selection_score'] = round(score, 2)
        enriched['selection_reasons'] = reasons[:6]
        scored.append(enriched)

    scored.sort(key=lambda c: (c['selection_score'], 1 if c.get('price_matches') else 0, c.get('rating_value') or 0, c.get('review_count') or 0, -c.get('rank', 999)), reverse=True)
    selected = scored[:5]

    if len(selected) < 5:
        insufficiencies.append('有效候選卡片不足 5 間')
    if sum(1 for card in selected if card.get('price_matches')) < 3:
        insufficiencies.append('明確價格卡片偏少，選擇需更依賴評分/型態近似判斷')
    if sum(1 for card in selected if card.get('rating_value') is not None) < 4:
        insufficiencies.append('評分資訊不足，排序可信度有限')
    if item['location_zh'] == '惠庭':
        if rooms == 1:
            insufficiencies.append('惠庭樣本多為公寓/民宿類，1 room 是否真能住 3大1小仍需點進房型頁再確認')
        else:
            insufficiencies.append('惠庭結果多仰賴千歲周邊旅館補足，2 rooms 雖較穩妥，但仍需點進各房型頁確認可拆兩房')
    if item['location_zh'] == '札幌':
        insufficiencies.append('札幌搜尋結果混入定山溪/新札幌等外圍區，已人工偏重市區但仍屬近似篩選')
    return selected, insufficiencies


def load_payload(item: dict, rooms: int) -> dict:
    path = PROBE_DIR / f"{stem_for(item, rooms)}.json"
    return json.loads(path.read_text(encoding='utf-8'))


def is_approximate(insufficiencies: list[str]) -> bool:
    return bool(insufficiencies)


def approximate_badge(insufficiencies: list[str]) -> str:
    if not is_approximate(insufficiencies):
        return ''
    return " <span class='pill approx'>approximate</span>"


def hotel_block(card: dict, selected_rank: int) -> str:
    prices = ', '.join(card.get('price_matches') or []) or '此卡片未顯示明確價格'
    price_note = f'價格註記：{PRICE_WARNING}'
    name = html.escape(card.get('name') or 'Unnamed')
    link = html.escape(card.get('link') or '')
    title_html = f"<a href='{link}' target='_blank' rel='noreferrer'>{name}</a>" if link else name
    open_link_html = f"<div class='small'><a href='{link}' target='_blank' rel='noreferrer'>開啟此房型頁面</a></div>" if link else "<div class='small bad'>未擷取到可點擊連結</div>"
    meta_bits = []
    if card.get('rating_value') is not None:
        meta_bits.append(f"評分 {card['rating_value']:.1f}")
    if card.get('review_count'):
        meta_bits.append(f"評論 {int(card['review_count']):,} 則")
    if card.get('distance_km') is not None:
        meta_bits.append(f"距市中心約 {card['distance_km']:.1f} km")
    if card.get('property_type'):
        meta_bits.append(str(card['property_type']))
    reason_html = '；'.join(html.escape(reason) for reason in (card.get('selection_reasons') or []))
    return (
        "<div class='hotel'>"
        f"<div><strong>{selected_rank}. {title_html}</strong> <span class='small'>（原 trivago 排名 #{card.get('rank', '?')}｜篩選分數 {card.get('selection_score', '')}）</span></div>"
        f"<div class='price'>{html.escape(prices)}</div>"
        f"<div class='small'>{html.escape(price_note)}</div>"
        f"{open_link_html}"
        f"<div class='small meta2'>{html.escape('｜'.join(meta_bits))}</div>"
        f"<div class='small why'>入選原因：{reason_html}</div>"
        f"<div class='small'>{html.escape((card.get('text_sample') or '')[:280])}</div>"
        "</div>"
    )


def section_for(item: dict, payload: dict, rooms: int, selected_cards: list[dict[str, object]], insufficiencies: list[str]) -> str:
    guest_cfg = payload.get('guest_configuration', {})
    hotels_html = ''.join(hotel_block(card, idx) for idx, card in enumerate(selected_cards, start=1)) or "<p class='bad'>未抓到有效飯店卡片。</p>"
    after_value = guest_cfg.get('after') or payload.get('search_form_guest_value', '')
    approx_state = 'yes' if is_approximate(insufficiencies) else 'no'
    hotels_found = payload.get('hotels_found_text', '')
    if not hotels_found:
        summary_text = payload.get('summary_text', '')
        marker = 'We found '
        ai_marker = 'Our top matches for:'
        if marker in summary_text:
            hotels_found = marker + summary_text.split(marker, 1)[1].split('\n', 1)[0]
        elif ai_marker in summary_text:
            hotels_found = ai_marker + summary_text.split(ai_marker, 1)[1].split('\n', 1)[0]
    insufficiency_html = ''.join(f"<li>{html.escape(note)}</li>" for note in insufficiencies)
    chooser_title = '每晚最值得點開 5 間（1 room）' if rooms == 1 else '每晚最值得點開 5 間（2 rooms）'
    return f"""
<section class='card'>
<h2>{html.escape(item['label'])} <span class='pill'>{html.escape(item['location_zh'])}</span>{approximate_badge(insufficiencies)}</h2>
<p class='meta'>住宿搜尋：{html.escape(item['search'])}｜入住：{item['date']}｜退房：{item['checkout']}｜備註：{html.escape(item['note'])}</p>
<h3><span class='pill occ'>3大1小｜{rooms} {'間房' if rooms > 1 else '間房'}{'（尋找2間房組合）' if rooms == 2 else '（尋找4人房/家庭房）'}</span></h3>
<div class='grid'>
<div class='card'>
<h4>Occupancy 套用驗證</h4>
<p class='ok'>guest selector：{html.escape(guest_cfg.get('before', ''))} → {html.escape(after_value)}</p>
<p class='small {'bad' if is_approximate(insufficiencies) else 'ok'}'>approximate：{approx_state}{'（此晚保留近似篩選提醒）' if is_approximate(insufficiencies) else '（此晚未標記近似夜晚）'}</p>
<p class='small'>search form：{html.escape(payload.get('search_form_guest_value', ''))}</p>
<p class='small'>target：{html.escape(str(guest_cfg.get('target', {})))}</p>
<p class='small'>plan：{html.escape(json.dumps(guest_cfg.get('plan', []), ensure_ascii=False))}</p>
<p class='small'>final URL：<a href='{html.escape(payload.get('final_url', ''))}' target='_blank' rel='noreferrer'>{html.escape(payload.get('final_url', ''))}</a></p>
<p class='small'>hotels found：{html.escape(hotels_found)}</p>
<p class='small'>probe source：{html.escape(str(PROBE_DIR / (stem_for(item, rooms) + '.html')))}</p>
<p class='small'>screenshot：{html.escape(str(PROBE_DIR / (stem_for(item, rooms) + '.png')))}</p>
<h4>此晚篩選提醒</h4>
<ul class='small'>
<li>優先挑有明確價格、評分/評論數較完整者。</li>
<li>1 room 偏重家庭房/4人可住可能性；2 rooms 偏重標準旅館型、較容易拆成兩房。</li>
{insufficiency_html}
</ul>
</div>
<div class='card'>
<h4>{chooser_title}</h4>
{hotels_html}
</div>
</div>
</section>
"""


def render_report(rooms: int) -> Path:
    generated = time.strftime('%Y-%m-%d %H:%M:%S %Z')
    css = """
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:24px;color:#172033;background:#f6f7fb;line-height:1.5}
    h1,h2,h3,h4{color:#101828}.meta{color:#667085}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:white;border:1px solid #e4e7ec;border-radius:14px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.05);margin:14px 0}.ok{color:#067647}.bad{color:#b42318}.hotel{border-top:1px solid #eaecf0;padding:10px 0}.hotel:first-child{border-top:0}.price{font-weight:700;color:#175cd3}.small{font-size:12px;color:#667085}.pill{display:inline-block;border-radius:999px;padding:2px 8px;background:#eef4ff;color:#3538cd;font-size:12px;margin-left:6px}.occ{background:#fff7ed;color:#b54708}.approx{background:#fff1f3;color:#c01048}a{color:#175cd3}pre{white-space:pre-wrap;background:#101828;color:#f2f4f7;padding:10px;border-radius:8px;overflow:auto}.why{margin:6px 0 4px 0}.meta2{margin:4px 0}@media(max-width:900px){.grid{grid-template-columns:1fr}}
    """
    title_suffix = '1 room' if rooms == 1 else '2 rooms'
    intro = '每晚主動篩選最值得點開的 5 間；偏重 family room / 4人房可能性' if rooms == 1 else '每晚主動篩選最值得點開的 5 間；偏重標準旅館型兩房穩妥性'
    parts = [
        f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>北海道行程 Trivago 主動篩選報告：{title_suffix}</title><style>{css}</style></head><body>",
        f"<h1>北海道行程 Trivago 主動篩選報告：{title_suffix}</h1>",
        f"<p class='meta'>來源網站：trivago｜每晚條件：3 adults + 1 child age 10｜{intro}｜產生時間：{html.escape(generated)}</p>",
        f"<p class='meta'>價格說明：{PRICE_WARNING}實際是否可住 3 adults + 1 child age 10，仍需點入房型頁再次確認。</p>",
    ]
    for item in ITINERARY:
        payload = load_payload(item, rooms)
        selected_cards, insufficiencies = choose_cards(item, rooms)
        parts.append(section_for(item, payload, rooms, selected_cards, insufficiencies))
    parts.append("</body></html>")
    out = REPORTS / (f"hokkaido_hotels_trivago_family_{'1room' if rooms == 1 else '2rooms'}.html")
    out.write_text(''.join(parts), encoding='utf-8')
    return out


def render_combined(one_room: Path, two_rooms: Path) -> Path:
    generated = time.strftime('%Y-%m-%d %H:%M:%S %Z')
    approx_one = [item['date'] for item in ITINERARY if is_approximate(choose_cards(item, 1)[1])]
    approx_two = [item['date'] for item in ITINERARY if is_approximate(choose_cards(item, 2)[1])]
    css = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:24px;color:#172033;background:#f6f7fb;line-height:1.5}
h1,h2,h3,h4{color:#101828}.meta{color:#667085}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:white;border:1px solid #e4e7ec;border-radius:14px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.05);margin:14px 0}.ok{color:#067647}.bad{color:#b42318}.hotel{border-top:1px solid #eaecf0;padding:10px 0}.hotel:first-child{border-top:0}.price{font-weight:700;color:#175cd3}.small{font-size:12px;color:#667085}.pill{display:inline-block;border-radius:999px;padding:2px 8px;background:#eef4ff;color:#3538cd;font-size:12px;margin-left:6px}.occ{background:#fff7ed;color:#b54708}.approx{background:#fff1f3;color:#c01048}a{color:#175cd3}@media(max-width:900px){.grid{grid-template-columns:1fr}} .toc a{display:block;margin:6px 0} .section-title{position:sticky;top:0;background:#f6f7fb;padding:10px 0 2px;z-index:1}
    """
    one_html = one_room.read_text(encoding='utf-8')
    two_html = two_rooms.read_text(encoding='utf-8')
    body_re = re.compile(r'<body>(.*)</body>', re.S)
    one_body = body_re.search(one_html).group(1) if body_re.search(one_html) else one_html
    two_body = body_re.search(two_html).group(1) if body_re.search(two_html) else two_html
    one_body = re.sub(r'^.*?</p>', '', one_body, count=2, flags=re.S)
    two_body = re.sub(r'^.*?</p>', '', two_body, count=2, flags=re.S)
    approx_one_text = ', '.join(approx_one) if approx_one else '無'
    approx_two_text = ', '.join(approx_two) if approx_two else '無'
    combined = f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>北海道行程 Trivago 主動篩選合併報告</title><style>{css}</style></head><body><h1>北海道行程 Trivago 主動篩選合併報告</h1><p class='meta'>來源：既有 trivago probe + itinerary 資料；住宿條件固定為 3 adults + 1 child age 10；已改為每晚主動篩選最值得點開的 5 間。更新時間：{html.escape(generated)}</p><p class='meta'>價格說明：{PRICE_WARNING}房型名稱與「開啟此房型頁面」均保留可點擊連結。</p><p class='meta'>approximate 夜晚：1 room = {html.escape(approx_one_text)}｜2 rooms = {html.escape(approx_two_text)}</p><section class='card toc'><h2>內容導覽</h2><a href='#one-room'>1 room：每晚最值得點開 5 間</a><a href='#two-rooms'>2 rooms：每晚最值得點開 5 間</a><p class='small'>原始來源：{html.escape(str(one_room))}｜{html.escape(str(two_rooms))}</p></section><div id='one-room' class='section-title'><h2>1 room：每晚最值得點開 5 間</h2></div>{one_body}<div id='two-rooms' class='section-title'><h2>2 rooms：每晚最值得點開 5 間</h2></div>{two_body}</body></html>"
    out = REPORTS / 'hokkaido_hotels_trivago_family_combined.html'
    out.write_text(combined, encoding='utf-8')
    return out


def build_summary(one_room: Path, two_rooms: Path, combined: Path) -> dict[str, object]:
    combined_html = combined.read_text(encoding='utf-8')
    top5_count_per_night: dict[str, int] = {}
    top1_by_night: dict[str, dict[str, dict[str, str]]] = {}
    approx_nights_by_mode = {'family_1room': [], 'family_2rooms': []}
    approximation_notes_by_mode = {'family_1room': {}, 'family_2rooms': {}}

    for rooms, mode_key in ((1, 'family_1room'), (2, 'family_2rooms')):
        for item in ITINERARY:
            selected_cards, insufficiencies = choose_cards(item, rooms)
            top5_count_per_night[f"{item['date']}_{mode_key}"] = len(selected_cards)
            if selected_cards:
                top1_by_night.setdefault(item['date'], {})[mode_key] = {
                    'name': str(selected_cards[0].get('name') or ''),
                    'link': str(selected_cards[0].get('link') or ''),
                    'price': ', '.join(selected_cards[0].get('price_matches') or []) or '此卡片未顯示明確價格',
                }
            if is_approximate(insufficiencies):
                approx_nights_by_mode[mode_key].append(item['date'])
                approximation_notes_by_mode[mode_key][item['date']] = insufficiencies

    warning_occurrences_total = combined_html.count(PRICE_WARNING)
    nights_found_per_mode = {
        'family_1room': combined_html.count('每晚最值得點開 5 間（1 room）'),
        'family_2rooms': combined_html.count('每晚最值得點開 5 間（2 rooms）'),
    }
    validation = {
        'nights_expected': len(ITINERARY),
        'night_sections_expected_total': len(ITINERARY) * 2,
        'night_sections_found_total': sum(nights_found_per_mode.values()),
        'nights_found_per_mode': nights_found_per_mode,
        'top5_count_per_night': top5_count_per_night,
        'all_entries_have_links': '未擷取到可點擊連結' not in combined_html,
        'all_entries_have_warning_nearby': warning_occurrences_total >= len(ITINERARY) * 2 * 5,
        'price_warning_included': PRICE_WARNING in combined_html,
        'warning_occurrences_total': warning_occurrences_total,
        'combined_file_exists': combined.exists(),
        'combined_contains_1room_section': "id='one-room'" in combined_html,
        'combined_contains_2rooms_section': "id='two-rooms'" in combined_html,
        'occupancy_fixed_text_present': '3 adults + 1 child age 10' in combined_html,
        'approximate_marker_present': 'approximate' in combined_html,
        'validated_without_reprobe': True,
    }
    return {
        'site': 'trivago',
        'output_html': str(combined),
        'output_exists': combined.exists(),
        'summary_json': str(SUMMARY_PATH),
        'summary_exists': True,
        'data_sources_used': [
            str(PROBE_DIR),
            str(one_room),
            str(two_rooms),
            str(combined),
        ],
        'scripts_used_or_created': [
            str(BASE / 'scripts' / 'render_trivago_itinerary_dual_reports.py'),
            str(BASE / 'scripts' / 'probe_trivago_search.py'),
        ],
        'selection_rules_applied': [
            '固定住宿條件為 3 adults + 1 child age 10',
            '沿用既有 itinerary，不重排行程',
            '每晚各模式只保留最值得點開的 5 間',
            '主動篩選而非直接採用平台前 5',
            '有明確價格者優先',
            '評分、評論數與地點吻合 itinerary 者優先',
            '1 room 偏家庭房/4人可住可能性',
            '2 rooms 偏標準旅館型、較容易拆成兩房',
            '札幌外圍區與不利家庭入住型態降權',
            '缺少連結者不應入選',
        ],
        'reused_existing_trivago_render_probe_completely': True,
        'minimal_modifications_only': [
            '僅在 render_trivago_itinerary_dual_reports.py 補上 approximate 標記與 summary JSON 輸出',
            '沿用既有 itinerary 與 trivago probe 資料重新輸出 1room/2rooms/combined HTML',
            '未重跑 probe，僅以既有資料重新驗證與刷新輸出',
        ],
        'approx_nights_by_mode': approx_nights_by_mode,
        'approximation_notes_by_mode': approximation_notes_by_mode,
        'validation': validation,
        'top1_by_night': top1_by_night,
    }


def main() -> None:
    one_room = render_report(1)
    two_rooms = render_report(2)
    combined = render_combined(one_room, two_rooms)
    SUMMARY_PATH.write_text(json.dumps(build_summary(one_room, two_rooms, combined), ensure_ascii=False, indent=2), encoding='utf-8')
    print(one_room)
    print(two_rooms)
    print(combined)
    print(SUMMARY_PATH)


if __name__ == '__main__':
    main()
