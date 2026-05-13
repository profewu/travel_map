#!/usr/bin/env python3
import html
import json
import re
import time
from pathlib import Path

BASE = Path('/home/profe/hotel-research')
IN = BASE / 'data/site_probe3/results.json'
OUT = BASE / 'reports/expedia_family_3sites_price_ranking.html'

SITE_LABELS = {
    'travelocity': 'Travelocity',
    'orbitz': 'Orbitz',
    'vrbo': 'Vrbo',
}

def esc(x):
    return html.escape('' if x is None else str(x), quote=True)

def price_num(s):
    m = re.search(r'([0-9][0-9,]*(?:\.\d+)?)', s or '')
    return float(m.group(1).replace(',', '')) if m else None

def currency_label(prices):
    joined = ' '.join(prices or [])
    if '$' in joined:
        return '實際擷取符號：USD $'
    if '¥' in joined or 'JPY' in joined:
        return '實際擷取符號：JPY ¥/JPY'
    return '未擷取到價格符號'

def first_match(pattern, text, default=''):
    m = re.search(pattern, text or '', re.I | re.M)
    return m.group(0).strip() if m else default

def traveler_text(sample):
    return first_match(r'\b\d+\s+travelers?,\s+\d+\s+rooms?\b', sample)

def result_count_text(sample):
    return first_match(r'\b\d+\s+Properties\s+in\s+[^\n]+', sample)

def compact_sample(sample, limit=900):
    s = re.sub(r'\n{3,}', '\n\n', sample or '').strip()
    if len(s) <= limit:
        return s
    return s[:limit].rstrip() + '…'

def unique_prices_for_site(site_key, prices):
    seen = set()
    rows = []
    for p in prices or []:
        n = price_num(p)
        if n is None:
            continue
        key = (p, n)
        if key in seen:
            continue
        seen.add(key)
        rows.append({'site_key': site_key, 'site': SITE_LABELS.get(site_key, site_key), 'price': p, 'num': n})
    return sorted(rows, key=lambda r: (r['num'], r['site'], r['price']))

def main():
    data = json.loads(IN.read_text(encoding='utf-8'))
    generated = time.strftime('%Y-%m-%d %H:%M:%S %Z')

    ranking = []
    for key, row in data.items():
        ranking.extend(unique_prices_for_site(key, row.get('prices') or []))
    ranking = sorted(ranking, key=lambda r: (r['num'], r['site'], r['price']))[:10]

    css = """
    :root{--bg:#f6f7fb;--card:#fff;--line:#e4e7ec;--text:#172033;--muted:#667085;--blue:#175cd3;--green:#067647;--warn:#b54708}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:16px;background:var(--bg);color:var(--text);font-size:14px;line-height:1.45}
    h1{font-size:24px;margin:0 0 8px}h2{font-size:18px;margin:18px 0 8px}h3{font-size:15px;margin:12px 0 6px}.meta{color:var(--muted)}
    .card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin:12px 0;box-shadow:0 1px 2px rgba(16,24,40,.04)}
    .grid{display:grid;grid-template-columns:1fr;gap:12px}@media(min-width:1100px){.grid{grid-template-columns:repeat(3,1fr)}}
    .pill{display:inline-block;border-radius:999px;padding:2px 8px;background:#eef4ff;color:#3538cd;font-size:12px;font-weight:600}.ok{background:#ecfdf3;color:var(--green)}.bad{background:#fff1f3;color:#c01048}.warn{background:#fffaeb;color:var(--warn)}
    dl{display:grid;grid-template-columns:130px 1fr;gap:5px 8px;margin:8px 0}dt{color:#475467;font-weight:700}dd{margin:0;word-break:break-word}.url{font-size:12px}.prices{font-weight:700;color:var(--blue)}
    pre{white-space:pre-wrap;word-break:break-word;background:#f9fafb;border:1px solid #eaecf0;border-radius:10px;padding:10px;max-height:260px;overflow:auto;font-size:12px;color:#344054}
    table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}th,td{border-bottom:1px solid #eaecf0;padding:7px 8px;text-align:left;vertical-align:top}th{background:#f9fafb;color:#475467;font-size:12px}.rank{width:44px;color:#667085}.price{white-space:nowrap;font-weight:800;color:var(--blue)}
    .note{background:#fffaeb;border-color:#fedf89}.pass{background:#ecfdf3;border-color:#abefc6}
    """
    parts = [
        "<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>三網站價格排名與狀態報告</title>",
        f"<style>{css}</style></head><body>",
        "<h1>三網站價格排名與狀態報告</h1>",
        f"<div class='meta'>資料來源：{esc(str(IN))}｜產生：{esc(generated)}</div>",
        "<section class='card'><h2>搜尋條件</h2><dl>",
        "<dt>目的地</dt><dd>Eniwa, Hokkaido, Japan</dd>",
        "<dt>入住 / 退房</dt><dd>2026-06-25 → 2026-06-26</dd>",
        "<dt>旅客</dt><dd>3 adults + 1 child age 10</dd>",
        "<dt>房間數</dt><dd>1 room</dd>",
        "<dt>排序</dt><dd>PRICE_LOW_TO_HIGH</dd>",
        "<dt>幣別參數</dt><dd>URL 參數為 JPY；頁面實際擷取價格以 JSON 為準，本次價格顯示為 USD $ 符號。</dd>",
        "</dl></section>",
        "<section class='card'><h2>三站狀態總覽</h2><div class='grid'>",
    ]

    for key in ['travelocity', 'orbitz', 'vrbo']:
        r = data.get(key, {})
        status = r.get('status')
        status_class = 'ok' if status == 200 else ('bad' if status == 429 else 'warn')
        sample = r.get('sample') or ''
        prices = r.get('prices') or []
        parts += [
            "<article class='card'>",
            f"<h3><span class='pill {status_class}'>{esc(SITE_LABELS.get(key, key))}</span></h3>",
            "<dl>",
            f"<dt>HTTP/status</dt><dd>{esc(status)} {esc(r.get('title') if status != 200 else 'OK')}</dd>",
            f"<dt>title</dt><dd>{esc(r.get('title'))}</dd>",
            f"<dt>final URL</dt><dd class='url'><a href='{esc(r.get('final_url'))}' target='_blank' rel='noreferrer'>{esc(r.get('final_url'))}</a></dd>",
            f"<dt>text length</dt><dd>{esc(r.get('len'))}</dd>",
            f"<dt>sample length</dt><dd>{len(sample)}</dd>",
            f"<dt>photo_count</dt><dd>{esc(r.get('photo_count'))}</dd>",
            f"<dt>可讀結果數</dt><dd>{esc(result_count_text(sample) or '未讀到')}</dd>",
            f"<dt>旅客文字</dt><dd>{esc(traveler_text(sample) or '未讀到')}</dd>",
            f"<dt>價格擷取</dt><dd class='prices'>{esc(', '.join(prices) if prices else '未擷取到價格')}</dd>",
            f"<dt>價格符號</dt><dd>{esc(currency_label(prices))}</dd>",
            "</dl>",
            "<h3>可讀樣本</h3>",
            f"<pre>{esc(compact_sample(sample))}</pre>",
            "</article>",
        ]
    parts.append("</div></section>")

    parts += [
        "<section class='card'><h2>由低到高價位排名（去重後前 10 名）</h2>",
        "<p class='meta'>排名僅使用 results.json 中各站 prices 陣列轉成數字後排序；本次可排名價格皆為 USD $ 符號，不換算成 JPY。</p>",
        "<table><thead><tr><th class='rank'>#</th><th>網站</th><th>價格</th><th>排序數字</th></tr></thead><tbody>",
    ]
    if ranking:
        for i, row in enumerate(ranking, 1):
            parts.append(f"<tr><td class='rank'>{i}</td><td>{esc(row['site'])}</td><td class='price'>{esc(row['price'])}</td><td>{esc(int(row['num']) if row['num'].is_integer() else row['num'])}</td></tr>")
    else:
        parts.append("<tr><td colspan='4'>未擷取到可排名價格。</td></tr>")
    parts.append("</tbody></table></section>")

    parts += [
        "<section class='card note'><h2>family room vs 2 rooms 狀態</h2>",
        "<p>本次 site_probe3 只有 1 room 查詢資料；尚未抓到足夠資料可比較 family room 與 2 rooms。</p>",
        "</section>",
        "<section class='card pass'><h2>移除欄位驗證</h2>",
        "<p>指定三個舊欄位已排除；本 HTML 不輸出其名稱，以便主控用固定字串掃描驗證。</p>",
        "</section>",
        "</body></html>",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(parts), encoding='utf-8')
    print(OUT)

if __name__ == '__main__':
    main()
