#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

BASE = Path('/home/profe/hotel-research')
SRC = BASE / 'scripts' / 'render_expedia_family_combined.py'
LEGACY_JSON = BASE / 'data' / 'multisite' / 'expedia_hotels_all.json'
OTARU_RICH = BASE / 'data' / 'expedia_probe' / 'otaru-hokkaido-japan_2026-06-28_family_1room.json'
TOYA_RICH = BASE / 'data' / 'expedia_probe' / 'lake-toya-hokkaido-japan_2026-06-27_family_2rooms.json'
REPORT_PATH = BASE / 'reports' / 'hokkaido_hotels_expedia_family_combined.html'
SUMMARY_PATH = BASE / 'reports' / 'hokkaido_hotels_expedia_family_summary.json'

spec = importlib.util.spec_from_file_location('render_expedia_family_combined', SRC)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def norm_name(text: str) -> str:
    return ' '.join((text or '').strip().lower().split())


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def hotel_keywords(hotel: dict) -> str:
    return ' '.join(
        str(hotel.get(k) or '')
        for k in ('name', 'distance', 'location_text', 'snippet')
    ).lower()


def clone_hotel(hotel: dict) -> dict:
    return copy.deepcopy(hotel)


def hydrate_legacy_hotel(hotel: dict, rank_raw: int, occ_key: str, search: str, link_index: dict[str, str]) -> dict:
    score = hotel.get('score')
    try:
        score = float(score) if score not in (None, '') else None
    except Exception:
        score = None
    link = link_index.get(norm_name(hotel.get('name', ''))) or hotel.get('link') or ''
    distance = hotel.get('distance') or ''
    row = {
        'name': hotel.get('name') or 'Unknown hotel',
        'rank_raw': rank_raw,
        'link': link,
        'link_type': 'property-level' if '/Hotel-Information' in link else 'search-result',
        'price': hotel.get('price') or '',
        'price_num': hotel.get('price_num'),
        'nightly_price': '',
        'total_price': hotel.get('price') if 'total' in str(hotel.get('price') or '').lower() else '',
        'score': score,
        'reviews': int(hotel.get('reviews') or 0),
        'distance': distance,
        'snippet': distance or hotel.get('name') or '',
        'location_text': distance,
        'occupancy_mode': occ_key,
        'target_search': search,
        'source_origin': 'legacy-multisite',
    }
    return row


def reoccupy(hotel: dict, occ_key: str, source_origin: str) -> dict:
    row = clone_hotel(hotel)
    row['occupancy_mode'] = occ_key
    row['source_origin'] = source_origin
    return row


def dedupe_hotels(hotels: list[dict]) -> list[dict]:
    out = []
    seen = set()
    for hotel in hotels:
        key = norm_name(hotel.get('name', ''))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(hotel)
    return out


def add_candidate(dest: list[dict], hotel: dict, item: dict, occ: dict, *, extra_approx: bool = False, extra_reasons: list[str] | None = None):
    row = clone_hotel(hotel)
    score, reasons, approximate = mod.selection_score(item, occ, row)
    reasons = list(reasons)
    if extra_reasons:
        reasons.extend(extra_reasons)
    if extra_approx:
        approximate = True
    row['selection_score'] = score
    row['why'] = reasons
    row['approximate'] = approximate
    row['approximate_reason'] = '；'.join(extra_reasons or [])
    dest.append(row)


def render_html(rows: list[dict]) -> None:
    by_mode = {occ['key']: [] for occ in mod.OCCS}
    for row in rows:
        by_mode[row['occupancy_key']].append(row)
    for occ in mod.OCCS:
        by_mode[occ['key']].sort(key=lambda r: r['date'])

    generated = mod.time.strftime('%Y-%m-%d %H:%M:%S %Z')
    css = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:24px;color:#172033;background:#f6f7fb;line-height:1.55}
h1,h2,h3,h4{color:#101828}.meta{color:#667085}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:white;border:1px solid #e4e7ec;border-radius:14px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.05);margin:14px 0}.hotel{border-top:1px solid #eaecf0;padding:10px 0}.hotel:first-child{border-top:0}.price{font-weight:700;color:#175cd3}.small{font-size:12px;color:#667085}.pill{display:inline-block;border-radius:999px;padding:2px 8px;background:#eef4ff;color:#3538cd;font-size:12px;margin-left:6px}.occ{background:#fff7ed;color:#b54708}.warn{color:#b54708}.bad{color:#b42318}.toc a{display:block;margin:6px 0}.section-title{position:sticky;top:0;background:#f6f7fb;padding:10px 0 2px;z-index:1}a{color:#175cd3}@media(max-width:900px){.grid{grid-template-columns:1fr}}
"""
    parts = [
        f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>北海道行程 Expedia 主動篩選合併報告</title><style>{css}</style></head><body>",
        '<h1>北海道行程 Expedia 主動篩選合併報告</h1>',
        f"<p class='meta'>來源：既有 Expedia property pool 重建；主體沿用 data/multisite/expedia_hotels_all.json，另補用 data/expedia_probe 中已成功留下的 Otaru 1 room（80 筆）與 Lake Toya 2 rooms（80 筆）property-level pool，對不足 5 間的夜晚做最小侵入補滿。固定條件：3 adults + 1 child age 10。更新時間：{mod.esc(generated)}</p>",
        f"<p class='meta'>總說明：{mod.esc(mod.PRICE_WARNING)} 另因 Expedia 搜尋頁多提供住宿頁（property-level）連結，本文每筆均保留可點連結；若補位來自另一 occupancy 或相近落腳點，會明確標記 approximate。</p>",
        "<section class='card toc'><h2>內容導覽</h2><a href='#one-room'>1 room：每晚主動篩選 5 間</a><a href='#two-rooms'>2 rooms：每晚主動篩選 5 間</a><p class='small'>本版為既有資料修補重建，不重跑 itinerary。</p></section>",
    ]
    for occ in mod.OCCS:
        parts.append(f"<div id='{mod.esc(occ['section_id'])}' class='section-title'><h2>{mod.esc(occ['label'])}：每晚主動篩選 5 間</h2></div>")
        parts.append(f"<p class='meta'>{mod.esc(mod.PRICE_WARNING)} 若卡片地點、房型可住性或補位來源不是同晚同 occupancy 原池，會明確標記 approximate。</p>")
        for row in by_mode[occ['key']]:
            parts.append("<section class='card'>")
            parts.append(f"<h2>{mod.esc(row['label'])} <span class='pill'>{mod.esc(row['location_zh'])}</span></h2>")
            parts.append(f"<p class='meta'>住宿搜尋：{mod.esc(row['search'])}｜入住：{mod.esc(row['date'])}｜退房：{mod.esc(row['checkout'])}｜備註：{mod.esc(row['note'])}</p>")
            parts.append(f"<h3><span class='pill occ'>{mod.esc(occ['label'])}</span></h3>")
            parts.append("<div class='grid'>")
            parts.append("<div class='card'>")
            parts.append('<h4>資料與篩選說明</h4>')
            parts.append(f"<p class='small'>查詢連結：<a href='{mod.esc(row['url'])}' target='_blank' rel='noreferrer'>{mod.esc(row['url'])}</a></p>")
            parts.append(f"<p class='small'>資料來源：{mod.esc('；'.join(row['sources']))}</p>")
            parts.append(f"<p class='small'>候選池：{len(row['candidate_pool'])} 間｜已選：{len(row['selected'])} 間</p>")
            parts.append('<h4>此晚篩選提醒</h4><ul class="small">')
            for note in row['notes']:
                parts.append(f'<li>{mod.esc(note)}</li>')
            parts.append('</ul></div>')
            parts.append("<div class='card'>")
            parts.append(f"<h4>每晚最值得點開 5 間（{mod.esc(occ['rooms'])} room{'s' if occ['rooms']=='2' else ''}）</h4>")
            for idx, hotel in enumerate(row['selected'], 1):
                approx = ' approximate' if hotel.get('approximate') else ''
                link = hotel.get('link') or row['url']
                parts.append("<div class='hotel'>")
                parts.append(f"<div><strong>{idx}. <a href='{mod.esc(link)}' target='_blank' rel='noreferrer'>{mod.esc(hotel['name'])}</a></strong> <span class='small'>（原 Expedia 排名 #{mod.esc(hotel.get('rank_raw'))}｜篩選分數 {mod.esc(hotel.get('selection_score'))}{mod.esc(approx)}）</span></div>")
                parts.append(f"<div class='price'>{mod.esc(hotel.get('price') or '未顯示')}</div>")
                parts.append(f"<div class='small warn'>價格註記：{mod.esc(mod.PRICE_WARNING)}</div>")
                parts.append(f"<div class='small warn'>連結註記：{mod.esc(mod.LINK_WARNING)}</div>")
                meta_bits = []
                if hotel.get('score') is not None:
                    meta_bits.append(f"評分 {hotel['score']}")
                if hotel.get('reviews'):
                    meta_bits.append(f"評論 {int(hotel['reviews']):,} 則")
                if hotel.get('distance'):
                    meta_bits.append(str(hotel['distance']))
                if hotel.get('source_origin'):
                    meta_bits.append(f"來源 {hotel['source_origin']}")
                parts.append(f"<div class='small'>{mod.esc('｜'.join(meta_bits))}</div>")
                if hotel.get('approximate'):
                    parts.append("<div class='small bad'>approximate：此筆含地點、房型可住性，或跨 occupancy / 相近落腳點補位判斷。</div>")
                if hotel.get('approximate_reason'):
                    parts.append(f"<div class='small bad'>approximate 原因：{mod.esc(hotel['approximate_reason'])}</div>")
                parts.append(f"<div class='small'>{mod.esc('；'.join(hotel.get('why') or []))}</div>")
                parts.append(f"<div class='small'><a href='{mod.esc(link)}' target='_blank' rel='noreferrer'>開啟 Expedia 住宿頁</a></div>")
                parts.append('</div>')
            parts.append('</div></div></section>')
    parts.append('</body></html>')
    REPORT_PATH.write_text('\n'.join(parts), encoding='utf-8')


def main() -> None:
    legacy_rows = load_json(LEGACY_JSON)
    otaru_rich = load_json(OTARU_RICH)
    toya_rich = load_json(TOYA_RICH)
    rich_rows = [otaru_rich, toya_rich]

    link_index: dict[str, str] = {}
    for rich in rich_rows:
        for hotel in rich.get('hotels', []):
            if hotel.get('link'):
                link_index.setdefault(norm_name(hotel.get('name', '')), hotel['link'])

    legacy_map: dict[tuple[str, str], dict] = {}
    for row in legacy_rows:
        legacy_map[(row['date'], row['occupancy_key'])] = row

    sapporo_pool: dict[str, list[dict]] = {occ['key']: [] for occ in mod.OCCS}
    for occ in mod.OCCS:
        seen = set()
        for row in legacy_rows:
            if row['search'] != 'Sapporo, Hokkaido, Japan' or row['occupancy_key'] != occ['key']:
                continue
            for idx, hotel in enumerate(row.get('hotels', []), 1):
                h = hydrate_legacy_hotel(hotel, idx, occ['key'], row['search'], link_index)
                key = norm_name(h['name'])
                if key not in seen:
                    seen.add(key)
                    sapporo_pool[occ['key']].append(h)

    noboribetsu_extras = []
    for hotel in toya_rich.get('hotels', []):
        low = hotel_keywords(hotel)
        if any(token in low for token in ['noboribetsu', 'muroran', 'date', 'toyako', 'toya']):
            noboribetsu_extras.append(reoccupy(hotel, 'family_1room', 'lake-toya-rich-nearby'))
            noboribetsu_extras.append(reoccupy(hotel, 'family_2rooms', 'lake-toya-rich-nearby'))

    selected_rows = []
    approx_nights = {occ['key']: [] for occ in mod.OCCS}
    top5_count_per_night = {}

    for item in mod.ITINERARY:
        for occ in mod.OCCS:
            legacy_row = legacy_map[(item['date'], occ['key'])]
            exact_candidates = []
            for idx, hotel in enumerate(legacy_row.get('hotels', []), 1):
                exact_candidates.append(hydrate_legacy_hotel(hotel, idx, occ['key'], item['search'], link_index))

            candidate_pool = []
            source_labels = [str(LEGACY_JSON)]
            base_extra_reasons = []

            if item['search'] == 'Otaru, Hokkaido, Japan' and occ['key'] == 'family_1room':
                candidate_pool = [reoccupy(h, occ['key'], 'otaru-rich-exact') for h in otaru_rich['hotels']]
                source_labels = [str(OTARU_RICH)]
            elif item['search'] == 'Lake Toya, Hokkaido, Japan' and occ['key'] == 'family_2rooms':
                candidate_pool = [reoccupy(h, occ['key'], 'lake-toya-rich-exact') for h in toya_rich['hotels']]
                source_labels = [str(TOYA_RICH)]
            else:
                candidate_pool.extend(exact_candidates)
                if item['search'] == 'Otaru, Hokkaido, Japan' and occ['key'] == 'family_2rooms':
                    candidate_pool.extend(reoccupy(h, occ['key'], 'otaru-rich-cross-occupancy') for h in otaru_rich['hotels'])
                    source_labels.append(str(OTARU_RICH))
                elif item['search'] == 'Lake Toya, Hokkaido, Japan' and occ['key'] == 'family_1room':
                    candidate_pool.extend(reoccupy(h, occ['key'], 'lake-toya-rich-cross-occupancy') for h in toya_rich['hotels'])
                    source_labels.append(str(TOYA_RICH))
                elif item['search'] == 'Eniwa, Hokkaido, Japan':
                    candidate_pool.extend(reoccupy(h, occ['key'], 'sapporo-nearby-fill') for h in sapporo_pool[occ['key']])
                    source_labels.append(str(LEGACY_JSON) + '::sapporo_pool')
                elif item['search'] == 'Noboribetsu, Hokkaido, Japan':
                    candidate_pool.extend(reoccupy(h, occ['key'], 'lake-toya-nearby-fill') for h in noboribetsu_extras if h['occupancy_mode'] == occ['key'])
                    source_labels.append(str(TOYA_RICH) + '::noboribetsu_nearby')
                elif item['search'] == 'Sapporo, Hokkaido, Japan':
                    candidate_pool.extend(reoccupy(h, occ['key'], 'sapporo-same-city-fill') for h in sapporo_pool[occ['key']])
                    source_labels.append(str(LEGACY_JSON) + '::sapporo_pool')

            candidate_pool = dedupe_hotels(candidate_pool)
            exact_name_set = {norm_name(h['name']) for h in exact_candidates}
            scored = []
            for hotel in candidate_pool:
                extra_approx = False
                extra_reasons = []
                origin = hotel.get('source_origin', '')
                if item['search'] == 'Otaru, Hokkaido, Japan' and occ['key'] == 'family_2rooms' and origin == 'otaru-rich-cross-occupancy':
                    extra_approx = True
                    extra_reasons.append('此筆來自 Otaru 1 room property pool，補作 2 rooms 近似候選')
                elif item['search'] == 'Lake Toya, Hokkaido, Japan' and occ['key'] == 'family_1room' and origin == 'lake-toya-rich-cross-occupancy':
                    extra_approx = True
                    extra_reasons.append('此筆來自 Lake Toya 2 rooms property pool，補作 1 room 近似候選')
                elif item['search'] == 'Eniwa, Hokkaido, Japan' and norm_name(hotel['name']) not in exact_name_set:
                    extra_approx = True
                    extra_reasons.append('惠庭原池不足 5 間，借用札幌同 occupancy pool 補位')
                elif item['search'] == 'Noboribetsu, Hokkaido, Japan' and norm_name(hotel['name']) not in exact_name_set:
                    extra_approx = True
                    extra_reasons.append('登別原池不足 5 間，借用 Lake Toya pool 中帶 Noboribetsu/Muroran/Date 訊號者補位')
                elif item['search'] == 'Sapporo, Hokkaido, Japan' and norm_name(hotel['name']) not in exact_name_set:
                    extra_approx = True
                    extra_reasons.append('札幌當晚原池不足 5 間，借用同城市同 occupancy 既有 Expedia pool 補位')
                add_candidate(scored, hotel, item, occ, extra_approx=extra_approx, extra_reasons=extra_reasons)

            scored.sort(key=lambda h: (-float(h.get('selection_score', 0)), h.get('price_num') is None, float(h.get('price_num') or 10**9), int(h.get('rank_raw') or 9999)))
            selected = scored[:5]
            notes = mod.nightly_notes(item, occ, selected)
            if item['search'] == 'Eniwa, Hokkaido, Japan':
                notes.append('因 Expedia 惠庭池只有 4 間且都偏札幌，追加同 occupancy 的札幌 pool 補到 5 間，均視為 approximate。')
            if item['search'] == 'Noboribetsu, Hokkaido, Japan':
                notes.append('因 Expedia 登別池只有 4 間，增補 Lake Toya 成功 pool 中帶 Noboribetsu/Muroran/Date 訊號者。')
            if item['search'] == 'Lake Toya, Hokkaido, Japan' and occ['key'] == 'family_1room':
                notes.append('Lake Toya 1 room 成功 probe 不可用，改用既有 4 筆 + Lake Toya 2 rooms property pool 重排補滿。')
            if item['search'] == 'Otaru, Hokkaido, Japan' and occ['key'] == 'family_2rooms':
                notes.append('Otaru 2 rooms 成功 probe 不可用，改用既有 4 筆 + Otaru 1 room property pool 重排補滿。')
            if item['search'] == 'Sapporo, Hokkaido, Japan':
                notes.append('札幌每晚原池只有 3 筆，改從同城市同 occupancy 的既有 Expedia pool 整體重排補滿到 5 間。')

            row = {
                'site': 'Expedia',
                'date': item['date'],
                'checkout': item['checkout'],
                'label': item['label'],
                'location_zh': item['location_zh'],
                'search': item['search'],
                'note': item['note'],
                'occupancy_key': occ['key'],
                'occupancy_label': occ['label'],
                'url': legacy_row.get('final_url') or legacy_row.get('url') or '',
                'probe_source': source_labels[0],
                'raw_text_path': '',
                'screenshot': legacy_row.get('screenshot') or '',
                'status': legacy_row.get('status'),
                'title': legacy_row.get('title'),
                'links_found': len(candidate_pool),
                'hotels_found': len(candidate_pool),
                'selected': selected,
                'notes': notes,
                'errors': [],
                'candidate_pool': candidate_pool,
                'sources': source_labels,
            }
            if any(h.get('approximate') for h in selected):
                approx_nights[occ['key']].append(item['date'])
            top5_count_per_night[f"{item['date']}_{occ['key']}"] = len(selected)
            selected_rows.append(row)

    render_html(selected_rows)

    summary = {
        'site': 'Expedia',
        'output_html': str(REPORT_PATH),
        'output_exists': REPORT_PATH.exists(),
        'data_sources_used': [
            str(LEGACY_JSON),
            str(OTARU_RICH),
            str(TOYA_RICH),
            str(SRC),
        ],
        'scripts_used_or_created': [str(Path(__file__))],
        'selection_rules_applied': [
            '同晚同 occupancy Expedia 候選優先',
            '不足 5 間時，先借同城市同 occupancy 或同城市另一 occupancy 的既有 Expedia property pool',
            '若同城市仍不足，借相近落腳點成功 pool 補位並標 approximate',
            '有價格、評分/評論數、落腳點訊號、1 room 家庭型訊號、2 rooms 標準旅館型訊號優先',
        ],
        'approx_nights_by_mode': approx_nights,
        'validation': {
            'nights_expected': len(mod.ITINERARY),
            'nights_found_per_mode': {occ['key']: sum(1 for row in selected_rows if row['occupancy_key'] == occ['key']) for occ in mod.OCCS},
            'top5_count_per_night': top5_count_per_night,
            'all_entries_have_links': all(bool(h.get('link')) for row in selected_rows for h in row['selected']),
            'price_warning_included': mod.PRICE_WARNING in REPORT_PATH.read_text(encoding='utf-8'),
        },
        'top1_by_night': {
            row['date'] + '::' + row['occupancy_key']: {
                'name': row['selected'][0]['name'],
                'link': row['selected'][0]['link'],
                'price': row['selected'][0]['price'],
                'approximate': row['selected'][0]['approximate'],
            }
            for row in selected_rows
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'WROTE {REPORT_PATH}')
    print(f'WROTE {SUMMARY_PATH}')


if __name__ == '__main__':
    main()
