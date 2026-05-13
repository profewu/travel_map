#!/usr/bin/env python3
import html
import json
import re
import time
from pathlib import Path

BASE = Path('/home/profe/hotel-research')
DATA = BASE / 'data' / 'booking_ab' / 'cloak_all.json'
REPORT = BASE / 'reports' / 'hokkaido_hotels_booking_cloak_only_select.html'

ITINERARY_ORDER = [
    ('2026-06-25', '惠庭'),
    ('2026-06-26', '登別'),
    ('2026-06-27', '洞爺湖'),
    ('2026-06-28', '小樽'),
    ('2026-06-29', '札幌'),
    ('2026-06-30', '札幌'),
    ('2026-07-01', '札幌'),
    ('2026-07-02', '札幌'),
]
OCCUPANCY_ORDER = ['family_1room', 'family_2rooms']


def price_num(s):
    m = re.search(r'[0-9][0-9,]*', s or '')
    return int(m.group(0).replace(',', '')) if m else None


def score_num(s):
    nums = re.findall(r'\d+(?:\.\d+)?', s or '')
    return nums[0] if nums else ''


def infer_three_star(name, score_text):
    # Existing search-card extraction does not include official star rating.
    # Leave unchecked, but mark hotels/chains that often appear as 3-star/business hotels as "unknown" rather than claiming facts.
    return False


def render(arr):
    by_key = {(r['date'], r.get('occupancy_key')): r for r in arr}
    generated = time.strftime('%Y-%m-%d %H:%M:%S %Z')
    css = """
    :root{--bg:#f6f7fb;--card:#fff;--line:#e4e7ec;--text:#172033;--muted:#667085;--blue:#175cd3;--green:#067647;--orange:#b54708}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:24px;background:var(--bg);color:var(--text)}
    h1,h2,h3{color:#101828}.meta{color:var(--muted);line-height:1.6}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.05);margin:14px 0}.pill{display:inline-block;border-radius:999px;padding:3px 9px;background:#eef4ff;color:#3538cd;font-size:12px;margin-left:6px}.occ{background:#fff7ed;color:var(--orange)}
    table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;margin:10px 0 22px}th,td{border-bottom:1px solid #eaecf0;padding:9px 8px;text-align:left;vertical-align:top;font-size:14px}th{background:#f9fafb;color:#344054;font-size:13px}.num{width:36px;color:var(--muted)}.price{font-weight:700;color:var(--blue);white-space:nowrap}.small{font-size:12px;color:var(--muted);line-height:1.45}.select{text-align:center;width:82px}.note{width:160px}.ok{color:var(--green)}.warn{color:var(--orange)}a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}input[type='checkbox']{transform:scale(1.25)}input[type='text']{width:95%;border:1px solid #d0d5dd;border-radius:8px;padding:6px}.summary{display:flex;gap:12px;flex-wrap:wrap}.summary span{background:#fff;border:1px solid var(--line);border-radius:999px;padding:7px 10px;font-size:13px}.disclaimer{background:#fffbeb;border-color:#fedf89}@media(max-width:900px){body{margin:12px}table{display:block;overflow-x:auto}th,td{min-width:90px}.note{min-width:180px}}
    """
    total_hotels = sum(len(r.get('hotels') or []) for r in arr)
    parts = ["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>",
             "<title>北海道行程飯店清單（CloakBrowser）</title>",
             f"<style>{css}</style></head><body>",
             "<h1>北海道行程飯店清單（CloakBrowser）</h1>",
             f"<p class='meta'>來源網站：Booking.com｜查詢工具：CloakBrowser｜條件：3 大 + 1 小（10歲），比較 1間房與2間房，JPY，en-US，Asia/Tokyo｜產生時間：{html.escape(generated)}</p>",
             "<div class='summary'>",
             f"<span>查詢組數：{len(arr)}</span>",
             f"<span>飯店列數：{total_hotels}</span>",
             "<span>已移除 Playwright 欄位</span>",
             "<span>新增選擇欄：3星級 / 高樓層</span>",
             "</div>",
             "<div class='card disclaimer'><strong>欄位說明：</strong><br>「3星級」：Booking.com 搜尋卡片目前未穩定提供官方星級，本欄做為人工篩選/後續查證勾選。<br>「高樓層」：通常屬於訂房備註/房間偏好，不是搜尋結果頁可直接確認的保證條件，本欄做為偏好選擇。</div>"]
    for date, loc in ITINERARY_ORDER:
        matching = [r for r in arr if r['date'] == date]
        if not matching:
            continue
        first = matching[0]
        parts.append(f"<section class='card'><h2>{html.escape(first['label'])} <span class='pill'>{html.escape(loc)}</span></h2>")
        parts.append(f"<p class='meta'>住宿搜尋：{html.escape(first['search'])}｜入住：{date}｜退房：{html.escape(first.get('checkout',''))}｜備註：{html.escape(first.get('note',''))}</p>")
        for occ in OCCUPANCY_ORDER:
            r = by_key.get((date, occ))
            if not r:
                continue
            parts.append(f"<h3><span class='pill occ'>{html.escape(r.get('occupancy_label', occ))}</span></h3>")
            parts.append("<table><thead><tr>"
                         "<th class='num'>#</th><th>飯店</th><th>價格</th><th>評分/距離</th><th class='select'>3星級</th><th class='select'>高樓層</th><th class='note'>備註</th>"
                         "</tr></thead><tbody>")
            hotels = r.get('hotels') or []
            if not hotels:
                parts.append("<tr><td colspan='7' class='warn'>此查詢未取得飯店結果。</td></tr>")
            for idx, h in enumerate(hotels, 1):
                name = html.escape(h.get('name',''))
                link = h.get('link') or ''
                name_html = f"<a href='{html.escape(link)}' target='_blank' rel='noreferrer'>{name}</a>" if link else name
                score = score_num(h.get('score',''))
                score_line = html.escape(h.get('score',''))
                dist = html.escape(h.get('distance',''))
                addr = html.escape(h.get('address',''))
                detail = '<br>'.join(x for x in [score_line, dist, addr] if x)
                pnum = price_num(h.get('price',''))
                price = html.escape(h.get('price') or '價格未顯示')
                # default unchecked: this avoids falsely asserting star/floor facts.
                parts.append("<tr>")
                parts.append(f"<td class='num'>{idx}</td>")
                parts.append(f"<td>{name_html}<div class='small'>{html.escape(h.get('name',''))}</div></td>")
                parts.append(f"<td class='price' data-price='{pnum or ''}'>{price}</td>")
                parts.append(f"<td class='small'>{detail}</td>")
                parts.append(f"<td class='select'><input type='checkbox' aria-label='3星級 {name}'></td>")
                parts.append(f"<td class='select'><input type='checkbox' aria-label='高樓層 {name}'></td>")
                parts.append("<td class='note'><input type='text' placeholder='例如：親子友善/近車站/待查星級'></td>")
                parts.append("</tr>")
            parts.append("</tbody></table>")
        parts.append("</section>")
    parts.append("</body></html>")
    return '\n'.join(parts)


def main():
    arr = json.loads(DATA.read_text(encoding='utf-8'))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render(arr), encoding='utf-8')
    print(REPORT)
    print('runs', len(arr), 'hotels', sum(len(r.get('hotels') or []) for r in arr))

if __name__ == '__main__':
    main()
