#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

PRICE_RE = re.compile(r"(?:TWD|JPY|USD|EUR|NT\$|¥|\$)\s?[0-9][0-9,]*(?:\.\d+)?")
DEFAULT_OUT = Path("/home/profe/hotel-research/data/trivago_probe")


def normalize_child_ages(value: str | int | Iterable[object] | None) -> list[int]:
    if value is None or value == "":
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
        return [int(part) for part in parts]
    ages: list[int] = []
    for item in value:
        if item in (None, ""):
            continue
        ages.append(int(item))
    return ages


def replace_date_range(url: str, checkin: str, checkout: str) -> str:
    compact = f"dr-{checkin.replace('-', '')}-{checkout.replace('-', '')}"
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    search_value = query.get("search", [""])[0]
    if ";dr-" in search_value:
        search_value = re.sub(r"dr-\d{8}-\d{8}", compact, search_value)
    else:
        search_value = f"{search_value};{compact}" if search_value else compact

    query_parts: list[str] = []
    seen_search = False
    for key, values in query.items():
        if key == "search":
            query_parts.append(f"search={search_value}")
            seen_search = True
        else:
            for value in values:
                query_parts.append(urlencode({key: value}))
    if not seen_search:
        query_parts.append(f"search={search_value}")

    return urlunparse(parsed._replace(query="&".join(query_parts)))


def slugify_destination(destination: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", destination.lower()).strip("-")
    return slug or "destination"


def parse_guest_summary(text: str) -> dict[str, int]:
    guests = 0
    rooms = 1
    guest_match = re.search(r"(\d+)\s+Guests?", text)
    room_match = re.search(r"(\d+)\s+Rooms?", text)
    if guest_match:
        guests = int(guest_match.group(1))
    if room_match:
        rooms = int(room_match.group(1))
    return {
        "guests": guests,
        "rooms": rooms,
        "adults": guests,
        "children": 0,
    }


def build_guest_adjustments(current: dict[str, int], target: dict[str, int]) -> list[tuple[str, int]]:
    plan: list[tuple[str, int]] = []
    for field in ("adults", "children", "rooms"):
        delta = target[field] - current[field]
        if delta > 0:
            plan.append((f"{field}-amount-plus-button", delta))
        elif delta < 0:
            plan.append((f"{field}-amount-minus-button", abs(delta)))
    return plan


def build_artifact_stem(destination: str, checkin: str, checkout: str, adults: int, child_ages: list[int], rooms: int) -> str:
    return f"{slugify_destination(destination)}_{checkin}_{checkout}_a{adults}_c{len(child_ages)}_r{rooms}"


async def safe_inner_text(locator, timeout: int = 1500) -> str:
    try:
        return (await locator.inner_text(timeout=timeout)).strip()
    except Exception:
        return ""


async def dismiss_overlays(page) -> None:
    js = """
() => {
  const selectors = [
    '#usercentrics-cmp-ui',
    'aside[data-nosnippet="1"]',
    '[data-testid="uc-privacy-wall"]',
    '[data-testid="privacy-banner"]'
  ];
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el) el.remove();
  }
}
"""
    try:
        await page.evaluate(js)
    except Exception:
        pass


async def apply_guest_configuration(page, adults: int, child_ages: list[int], rooms: int) -> dict[str, object]:
    await page.locator('[data-testid="search-form-guest-selector"]').click(force=True)
    await page.wait_for_timeout(800)
    before_text = await safe_inner_text(page.locator('[data-testid="search-form-guest-selector-value"]').first)
    current = parse_guest_summary(before_text)
    current["children"] = int(await page.locator('[data-testid="children-amount"]').input_value())
    current["adults"] = int(await page.locator('[data-testid="adults-amount"]').input_value())
    current["rooms"] = int(await page.locator('[data-testid="rooms-amount"]').input_value())
    target = {"adults": adults, "children": len(child_ages), "rooms": rooms}
    plan = build_guest_adjustments(current=current, target=target)
    for button_id, clicks in plan:
        button = page.locator(f'[data-testid="{button_id}"]')
        for _ in range(clicks):
            await button.click(force=True)
            await page.wait_for_timeout(250)
    await page.locator('[data-testid="guest-selector-apply"]').click(force=True)
    await page.wait_for_timeout(800)
    after_text = await safe_inner_text(page.locator('[data-testid="search-form-guest-selector-value"]').first)
    return {
        "before": before_text,
        "after": after_text,
        "current": current,
        "target": target,
        "plan": [{"button": b, "clicks": c} for b, c in plan],
        "child_ages_note": child_ages,
    }


async def choose_destination_and_search(page, destination: str) -> dict:
    result: dict[str, object] = {"destination": destination}
    await page.goto("https://www.trivago.com/en-US", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_timeout(3000)
    await dismiss_overlays(page)

    search_input = page.locator('[data-testid="search-form-input"]').first
    await search_input.fill(destination)
    await page.wait_for_timeout(2500)

    suggestions = page.locator('[data-testid="suggested-item"]')
    result["suggestion_count"] = await suggestions.count()
    result["suggestions"] = []
    for idx in range(min(await suggestions.count(), 6)):
        result["suggestions"].append(await safe_inner_text(suggestions.nth(idx)))

    if await suggestions.count() == 0:
        raise RuntimeError("No trivago destination suggestions appeared")

    await suggestions.nth(0).click(force=True)
    await page.wait_for_timeout(1200)
    await page.locator('[data-testid="search-button-with-loader"]').click(force=True)
    await page.wait_for_timeout(7000)
    result["search_url"] = page.url
    result["search_title"] = await page.title()
    return result


async def extract_cards(page, limit: int = 20) -> list[dict[str, object]]:
    cards = page.locator('[data-testid="accommodation-list-element"]')
    count = await cards.count()
    rows: list[dict[str, object]] = []
    for idx in range(min(count, limit)):
        card = cards.nth(idx)
        text = await safe_inner_text(card, timeout=2500)
        name_link = card.locator('[data-testid="item-name-link"]').first
        name = await safe_inner_text(name_link)
        href = await name_link.get_attribute('href')
        prices = PRICE_RE.findall(text)
        rows.append(
            {
                "rank": idx + 1,
                "name": name,
                "link": href,
                "price_matches": prices[:5],
                "text_sample": text[:800],
            }
        )
    return rows


async def run_probe(args: argparse.Namespace) -> dict:
    from cloakbrowser import launch_async

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    child_ages = normalize_child_ages(args.children)
    stem = build_artifact_stem(
        destination=args.destination,
        checkin=args.checkin,
        checkout=args.checkout,
        adults=args.adults,
        child_ages=child_ages,
        rooms=args.rooms,
    )

    browser = await launch_async(headless=args.headless, locale=args.locale, timezone=args.timezone)
    page = await browser.new_page(viewport={"width": 1365, "height": 900})

    payload: dict[str, object] = {
        "destination": args.destination,
        "checkin": args.checkin,
        "checkout": args.checkout,
        "adults_requested": args.adults,
        "children_requested": child_ages,
        "rooms_requested": args.rooms,
        "locale": args.locale,
        "timezone": args.timezone,
        "currency_note": "trivago locale/currency is whatever the session renders; child ages are recorded but the current UI automation only applies adult/children count and room count.",
    }

    try:
        payload["selection"] = await choose_destination_and_search(page, args.destination)
        payload["guest_configuration"] = await apply_guest_configuration(
            page,
            adults=args.adults,
            child_ages=payload["children_requested"],
            rooms=args.rooms,
        )
        dated_url = replace_date_range(page.url, args.checkin, args.checkout)
        payload["dated_url"] = dated_url
        await page.goto(dated_url, wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_timeout(6000)
        await dismiss_overlays(page)

        payload["final_url"] = page.url
        payload["title"] = await page.title()
        payload["search_form_calendar_value"] = await safe_inner_text(page.locator('[data-testid="search-form-calendar-value"]').first)
        payload["search_form_guest_value"] = await safe_inner_text(page.locator('[data-testid="search-form-guest-selector-value"]').first)
        payload["summary_text"] = (await page.locator("body").inner_text(timeout=10000))[:5000]
        payload["hotels_found_text"] = ""
        body_text = await page.locator("body").inner_text(timeout=10000)
        m = re.search(r"We found\s+([^\n]+)", body_text)
        if m:
            payload["hotels_found_text"] = m.group(0)
        payload["cards"] = await extract_cards(page, limit=args.limit)
        payload["card_count"] = len(payload["cards"])

        screenshot_path = out_dir / f"{stem}.png"
        html_path = out_dir / f"{stem}.html"
        json_path = out_dir / f"{stem}.json"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        html_path.write_text(await page.content(), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["artifacts"] = {
            "json": str(json_path),
            "html": str(html_path),
            "screenshot": str(screenshot_path),
        }
    finally:
        await browser.close()

    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe trivago search results with CloakBrowser")
    parser.add_argument("--destination", default="Eniwa, Hokkaido, Japan")
    parser.add_argument("--checkin", default="2026-06-25")
    parser.add_argument("--checkout", default="2026-06-26")
    parser.add_argument("--adults", type=int, default=3)
    parser.add_argument("--children", default="10")
    parser.add_argument("--rooms", type=int, default=1)
    parser.add_argument("--locale", default="en-US")
    parser.add_argument("--timezone", default="Asia/Taipei")
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--headed", action="store_true", help="Run non-headless for debugging")
    args = parser.parse_args()
    args.headless = not args.headed
    return args


async def _amain() -> None:
    args = parse_args()
    result = await run_probe(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(_amain())
