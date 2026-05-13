#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup


BASE = Path(__file__).resolve().parents[1]
REPORTS = BASE / "reports"
OUT_HTML = REPORTS / "master_summary.html"
OUT_VALIDATION = REPORTS / "master_summary_validation.json"

ITINERARY = [
    {"date": "2026-06-25", "checkout": "2026-06-26", "place": "Eniwa", "place_zh": "惠庭"},
    {"date": "2026-06-26", "checkout": "2026-06-27", "place": "Noboribetsu", "place_zh": "登別"},
    {"date": "2026-06-27", "checkout": "2026-06-28", "place": "Lake Toya", "place_zh": "洞爺湖"},
    {"date": "2026-06-28", "checkout": "2026-06-29", "place": "Otaru", "place_zh": "小樽"},
    {"date": "2026-06-29", "checkout": "2026-06-30", "place": "Sapporo", "place_zh": "札幌"},
    {"date": "2026-06-30", "checkout": "2026-07-01", "place": "Sapporo", "place_zh": "札幌"},
    {"date": "2026-07-01", "checkout": "2026-07-02", "place": "Sapporo", "place_zh": "札幌"},
    {"date": "2026-07-02", "checkout": "2026-07-03", "place": "Sapporo", "place_zh": "札幌"},
]

SITE_REPORTS = [
    ("Agoda", "hokkaido_hotels_agoda_family_combined.html"),
    ("Booking.com", "hokkaido_hotels_booking_family_combined.html"),
    ("Hotels.com", "hokkaido_hotels_hotelscom_family_combined.html"),
    ("Expedia", "hokkaido_hotels_expedia_family_combined.html"),
    ("trivago", "hokkaido_hotels_trivago_family_combined.html"),
]

OCC_LABELS = {
    "family_1room": "1 room",
    "family_2rooms": "2 rooms",
}

OCC_ID_ALIASES = {
    "family_1room": "family_1room",
    "family_2rooms": "family_2rooms",
    "one-room": "family_1room",
    "two-rooms": "family_2rooms",
}

SITE_ORDER = {site: index for index, (site, _) in enumerate(SITE_REPORTS)}


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def clean_text(value: str, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def section_date(section: object) -> str | None:
    text = section.get_text(" ", strip=True)
    match = re.search(r"20\d\d-\d\d-\d\d", text)
    if match:
        return match.group(0)
    short = re.search(r"\b([67])/(\d{1,2})\b", text)
    if short:
        month, day = int(short.group(1)), int(short.group(2))
        return f"2026-{month:02d}-{day:02d}"
    return None


def section_occ(section: object) -> str | None:
    h3_text = clean_text(" ".join(h.get_text(" ", strip=True) for h in section.find_all("h3")))
    haystack = f"{h3_text} {section.get_text(' ', strip=True)[:800]}".lower()
    if "2 rooms" in haystack or "2 room" in haystack:
        return "family_2rooms"
    if "1 room" in haystack:
        return "family_1room"
    return None


def hotel_rank_and_name(text: str) -> tuple[int | None, str]:
    text = clean_text(text)
    match = re.match(r"(\d+)\.\s*(.+)", text)
    if not match:
        return None, text
    return int(match.group(1)), match.group(2).strip()


def compact_details(hotel_div: object, price: str) -> str:
    bits: list[str] = []
    for node in hotel_div.find_all(class_="small"):
        text = clean_text(node.get_text(" ", strip=True), 180)
        lower = text.lower()
        if not text or text == price:
            continue
        if any(token in lower for token in ["scored", "reviews", "out of 10", " km", " mi ", "rating"]):
            bits.append(text)
        elif any(token in lower for token in ["room-level", "property-level", "approximate"]):
            bits.append(text)
        elif any(token in lower for token in ["opening", "candidate", "reference", "source"]):
            bits.append(text)
        if len(bits) >= 2:
            break
    return " | ".join(dict.fromkeys(bits))


def link_query_dates(link: str) -> tuple[str, str]:
    if not link:
        return "", ""
    query = parse_qs(urlparse(link).query)
    checkin = query.get("checkin", [""])[0] or query.get("chkin", [""])[0] or query.get("startDate", [""])[0]
    checkout = query.get("checkout", [""])[0] or query.get("chkout", [""])[0] or query.get("endDate", [""])[0]
    return checkin, checkout


def link_rooms(link: str) -> str:
    if not link:
        return ""
    query = parse_qs(urlparse(link).query)
    return query.get("rooms", [""])[0] or query.get("no_rooms", [""])[0]


def booking_price_block_count(link: str) -> int:
    if not link:
        return 0
    query = parse_qs(urlparse(link).query)
    value = query.get("sr_pri_blocks", [""])[0]
    if not value:
        return 0
    return len([part for part in value.split(",") if part.strip()])


def normalize_price(price: str) -> str:
    price = clean_text(price)
    if not price:
        return "unavailable"
    if "unavailable" in price.lower():
        return price
    if not re.search(r"\d", price):
        return "unavailable"
    return price


def audit_row(row: dict[str, object]) -> tuple[str, str]:
    site = str(row["site"])
    date = str(row["date"])
    checkout = next((item["checkout"] for item in ITINERARY if item["date"] == date), "")
    price = str(row.get("price") or "")
    details = str(row.get("details") or "")
    badges = [str(b) for b in row.get("badges", [])]
    badge_text = " ".join(badges).lower()
    detail_text = details.lower()
    link = str(row.get("link") or "")
    link_checkin, link_checkout = link_query_dates(link)
    rooms = link_rooms(link)
    expected_rooms = "2" if row.get("occupancy") == "family_2rooms" else "1"
    mismatched_dates = link_checkin and (link_checkin != date or (checkout and link_checkout and link_checkout != checkout))
    mismatched_rooms = rooms and rooms != expected_rooms

    if site == "Booking.com":
        if mismatched_rooms:
            return "room-count mismatch", f"Link has rooms={rooms}; this table section expects {expected_rooms} room(s)."
        block_count = booking_price_block_count(link)
        if expected_rooms == "2" and block_count == 1:
            return "single-block 2-room", "Booking link has no_rooms=2 but only one sr_pri_blocks price component; re-open room page before treating this as a confirmed two-room total."
        if "room-level" in badge_text and not mismatched_dates:
            return "saved room-level", "Saved Booking row includes room-level pricing for this date and occupancy; re-open before purchase because inventory changes and some prices are rounded."
        if mismatched_dates:
            return "needs live recheck", f"Booking link date is {link_checkin} to {link_checkout}, not {date} to {checkout}."
        return "needs live recheck", "Booking row lacks a clear room-level marker in the saved report."

    if site == "Agoda":
        if mismatched_dates and mismatched_rooms:
            return "date/room mismatch", f"Agoda link points to {link_checkin} to {link_checkout} with rooms={rooms}; this section expects {date} to {checkout}, rooms={expected_rooms}."
        if mismatched_dates:
            return "date mismatch", f"Agoda link points to {link_checkin} to {link_checkout}; this section expects {date} to {checkout}."
        if mismatched_rooms:
            return "room-count mismatch", f"Agoda link has rooms={rooms}; this table section expects rooms={expected_rooms}."
        return "property mapped only", "Agoda property link was mapped from another source; no dated Agoda card price was captured."

    if site in {"Expedia", "Hotels.com"}:
        if mismatched_dates:
            return "date mismatch", f"Link query points to {link_checkin} to {link_checkout}; do not treat this price as confirmed for {date} to {checkout}."
        if "approximate" in badge_text or "approximate" in detail_text:
            return "approximate", "Saved source marks this as approximate/property-level; room availability and final taxes must be rechecked."
        if "selectedRoomType" in link and "selectedRatePlan" in link:
            return "property rate link", "Link carries room/rate parameters and matching dates, but source notes still require live confirmation."
        return "search/property link", "Search/property-level link; final room price is not confirmed."

    if site == "trivago":
        return "metasearch reference", "trivago price is a starting reference from metasearch, not a confirmed final booking-room price; child age 10 was not fully validated by the saved UI automation."

    if not price or price.lower() in {"unavailable", "price unavailable"}:
        return "missing price", "No price was captured in the saved source."
    return "needs live recheck", "No site-specific audit rule matched this row."


def parse_site_report(site: str, filename: str) -> list[dict[str, object]]:
    path = REPORTS / filename
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    current_occ: str | None = None

    for node in soup.body.descendants if soup.body else soup.descendants:
        if not getattr(node, "name", None):
            continue
        node_id = node.get("id")
        if node_id in OCC_ID_ALIASES:
            current_occ = OCC_ID_ALIASES[str(node_id)]
            continue
        if node.name != "section":
            continue
        classes = node.get("class") or []
        if "card" not in classes:
            continue

        hotels = node.select("div.hotel")
        if not hotels:
            continue
        date = section_date(node)
        occ = current_occ or section_occ(node)
        if not date or not occ:
            continue

        for fallback_rank, hotel_div in enumerate(hotels, start=1):
            strong = hotel_div.find("strong")
            if not strong:
                continue
            rank, name = hotel_rank_and_name(strong.get_text(" ", strip=True))
            link = ""
            link_node = strong.find("a") or hotel_div.find("a")
            if link_node and link_node.get("href"):
                link = str(link_node["href"])
            price_node = hotel_div.find(class_="price")
            price = normalize_price(price_node.get_text(" ", strip=True) if price_node else "")
            badges = [
                clean_text(span.get_text(" ", strip=True))
                for span in hotel_div.find_all(class_="pill")
                if clean_text(span.get_text(" ", strip=True))
            ]
            key = (site, date, occ, name.lower(), link)
            if key in seen:
                continue
            seen.add(key)
            row = {
                "site": site,
                "date": date,
                "occupancy": occ,
                "rank": rank or fallback_rank,
                "name": name,
                "price": price,
                "details": compact_details(hotel_div, price),
                "badges": badges,
                "link": link,
            }
            row["audit_status"], row["audit_note"] = audit_row(row)
            rows.append(row)
    return rows


def status_class(status: str) -> str:
    key = status.lower().replace(" ", "-")
    if status in {"saved room-level"}:
        return "status-ok"
    if status in {"date mismatch", "needs live recheck", "property mapped only"}:
        return "status-warn"
    return "status-info"


def render_table(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "<p class='empty'>No downloaded comparison rows found for this room mode.</p>"
    lines = [
        "<div class='table-wrap'><table>",
        "<thead><tr><th>Site</th><th>Rank</th><th>Hotel</th><th>Price</th><th>Status</th><th>Audit note</th><th>Source details</th><th>Link</th></tr></thead>",
        "<tbody>",
    ]
    for row in sorted(rows, key=lambda r: (SITE_ORDER.get(str(r["site"]), 99), int(r["rank"] or 999), str(r["name"]).lower())):
        name_html = esc(row["name"])
        link = str(row.get("link") or "")
        hotel_html = f"<a href='{esc(link)}' target='_blank' rel='noreferrer'>{name_html}</a>" if link else name_html
        badge_html = " ".join(f"<span class='badge'>{esc(b)}</span>" for b in row.get("badges", [])[:3])
        details = clean_text(str(row.get("details") or ""), 260)
        source_details = f"{badge_html}<div class='detail'>{esc(details)}</div>" if badge_html else esc(details)
        status = str(row.get("audit_status") or "needs live recheck")
        link_html = f"<a href='{esc(link)}' target='_blank' rel='noreferrer'>Open</a>" if link else "<span class='muted'>missing</span>"
        lines.append(
            "<tr>"
            f"<td>{esc(row['site'])}</td>"
            f"<td>{esc(row['rank'])}</td>"
            f"<td class='hotel-name'>{hotel_html}</td>"
            f"<td class='price'>{esc(row.get('price') or 'unavailable')}</td>"
            f"<td><span class='status {status_class(status)}'>{esc(status)}</span></td>"
            f"<td class='audit-note'>{esc(row.get('audit_note') or '')}</td>"
            f"<td>{source_details}</td>"
            f"<td>{link_html}</td>"
            "</tr>"
        )
    lines.extend(["</tbody></table></div>"])
    return "\n".join(lines)


def render_summary_counts(all_rows: list[dict[str, object]]) -> str:
    counts = Counter(str(row.get("audit_status") or "unknown") for row in all_rows)
    chips = "".join(f"<span class='metric'><strong>{esc(count)}</strong> {esc(status)}</span>" for status, count in sorted(counts.items()))
    return f"<div class='metrics'>{chips}</div>"


def main() -> None:
    all_rows: list[dict[str, object]] = []
    source_counts: dict[str, int] = {}
    for site, filename in SITE_REPORTS:
        rows = parse_site_report(site, filename)
        all_rows.extend(rows)
        source_counts[filename] = len(rows)

    by_key: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in all_rows:
        by_key[(str(row["date"]), str(row["occupancy"]))].append(row)

    generated = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    css = """
:root{color-scheme:light}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'Noto Sans TC',sans-serif;margin:0;color:#172033;background:#f5f7fb;line-height:1.5}main{max-width:1380px;margin:0 auto;padding:28px 18px 44px}h1{font-size:28px;margin:0 0 8px}h2{font-size:22px;margin:0 0 8px}h3{font-size:17px;margin:18px 0 8px}.meta{color:#667085}.summary{background:#fff;border:1px solid #d0d5dd;border-radius:8px;padding:16px;margin:16px 0 20px}.day{background:#fff;border:1px solid #d0d5dd;border-radius:8px;padding:16px;margin:18px 0}.pill,.badge,.metric,.status{display:inline-block;border-radius:999px;padding:2px 8px;font-size:12px;margin:0 4px 4px 0;white-space:nowrap}.pill{background:#eef4ff;color:#3538cd}.badge{background:#f2f4f7;color:#344054}.metric{background:#f9fafb;border:1px solid #eaecf0;color:#344054}.status{font-weight:700}.status-ok{background:#ecfdf3;color:#027a48}.status-info{background:#eff8ff;color:#175cd3}.status-warn{background:#fff4e5;color:#b54708}.room-block{margin-top:12px}.table-wrap{overflow-x:auto;border:1px solid #eaecf0;border-radius:8px;background:#fff}table{border-collapse:collapse;width:100%;min-width:1180px;table-layout:fixed}th,td{border-bottom:1px solid #eaecf0;padding:9px 10px;text-align:left;vertical-align:top;font-size:13px;overflow-wrap:anywhere}th{background:#f9fafb;color:#344054;font-weight:700;position:sticky;top:0}tr:last-child td{border-bottom:0}th:nth-child(1),td:nth-child(1){width:92px}th:nth-child(2),td:nth-child(2){width:52px;text-align:right}th:nth-child(3),td:nth-child(3){width:230px}th:nth-child(4),td:nth-child(4){width:100px}th:nth-child(5),td:nth-child(5){width:140px}th:nth-child(6),td:nth-child(6){width:280px}th:nth-child(8),td:nth-child(8){width:62px}.hotel-name{font-weight:650}.price{font-variant-numeric:tabular-nums}.detail,.audit-note{color:#667085;font-size:12px}.muted,.empty{color:#667085}.toc a{margin-right:10px;color:#175cd3}a{color:#175cd3}@media(max-width:760px){main{padding:18px 10px}h1{font-size:22px}.day{padding:12px}th,td{font-size:12px;padding:8px}.summary{padding:12px}table{min-width:1080px}}
"""
    parts = [
        "<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>北海道住宿比價總表</title>",
        f"<style>{css}</style></head><body><main>",
        "<h1>北海道住宿比價總表</h1>",
        f"<p class='meta'>來源：hotel-research/reports 內的各站 combined report。重新審定時間：{esc(generated)}</p>",
        "<section class='summary'><h2>審定說明</h2>",
        "<p>每個日期/地點分成 1 room 與 2 rooms。價格欄保留來源報告抓到的值，但新增 Status 與 Audit note：只有 Booking.com 的 saved room-level 代表本機保存資料有房型層級證據；Agoda、trivago、Expedia、Hotels.com 多數仍需點入訂房頁確認最終房型、稅費與庫存。</p>",
        "<p>Expedia / Hotels.com 已自動檢查連結 query date；若連結日期不是該列住宿日期，Status 會標成 date mismatch，不應視為該晚確認價。</p>",
        render_summary_counts(all_rows),
        "<div class='toc'>"
        + "".join(f"<a href='#{item['date']}'>{item['date']} {esc(item['place'])}</a>" for item in ITINERARY)
        + "</div></section>",
    ]
    for item in ITINERARY:
        parts.append(f"<section id='{esc(item['date'])}' class='day'>")
        parts.append(
            f"<h2>{esc(item['date'])} {esc(item['place_zh'])} / {esc(item['place'])} "
            f"<span class='pill'>checkout {esc(item['checkout'])}</span></h2>"
        )
        for occ, label in OCC_LABELS.items():
            rows = by_key.get((item["date"], occ), [])
            parts.append(f"<div class='room-block'><h3>{esc(label)} <span class='pill'>{len(rows)} rows</span></h3>")
            parts.append(render_table(rows))
            parts.append("</div>")
        parts.append("</section>")
    parts.append("</main></body></html>")
    OUT_HTML.write_text("\n".join(parts), encoding="utf-8")

    status_counts = Counter(str(row.get("audit_status") or "unknown") for row in all_rows)
    validation = {
        "output_html": str(OUT_HTML),
        "exists": OUT_HTML.exists(),
        "source_counts": source_counts,
        "total_rows": len(all_rows),
        "night_sections": len(ITINERARY),
        "expected_date_room_sections": len(ITINERARY) * len(OCC_LABELS),
        "date_room_sections_with_rows": sum(1 for key in by_key if by_key[key]),
        "all_dates_present": all(any(row["date"] == item["date"] for row in all_rows) for item in ITINERARY),
        "all_date_room_sections_present": all((item["date"], occ) in by_key for item in ITINERARY for occ in OCC_LABELS),
        "sites": [site for site, _ in SITE_REPORTS],
        "audit_status_counts": dict(sorted(status_counts.items())),
        "date_mismatch_rows": [
            {
                "site": row["site"],
                "date": row["date"],
                "occupancy": row["occupancy"],
                "rank": row["rank"],
                "name": row["name"],
                "price": row["price"],
                "audit_note": row["audit_note"],
            }
            for row in all_rows
            if row.get("audit_status") == "date mismatch"
        ],
    }
    OUT_VALIDATION.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
