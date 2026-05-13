#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import re
import socket
import tempfile
import time
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlencode

from cloakbrowser import build_args, ensure_binary
from playwright.async_api import async_playwright

OUT = Path("/home/profe/hotel-research/data/site_probe3")
OUT.mkdir(parents=True, exist_ok=True)

BASE = {
    "destination": "Eniwa, Hokkaido, Japan",
    "startDate": "2026-06-25",
    "endDate": "2026-06-26",
    "rooms": "1",
    "adults": "3",
    "children": "1_10",
    "sort": "PRICE_LOW_TO_HIGH",
    "currency": "JPY",
    "locale": "en_US",
}
URLS = {site: f"https://www.{site}.com/Hotel-Search?" + urlencode(BASE) for site in ["travelocity", "orbitz", "vrbo"]}
PRICE_RE = re.compile(r"(?:NT\$|\$|¥|JPY\s*)\s?[0-9][0-9,]*(?:\.\d+)?")


def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def make_cdp_args(port: int, user_data_dir: str, headless: bool, locale: str, timezone: str) -> list[str]:
    extra_args = [
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if headless:
        extra_args.append("--headless=new")
    return build_args(True, extra_args, timezone=timezone, locale=locale, headless=headless)


async def wait_for_cdp_endpoint(port: int, timeout: float = 30.0) -> str:
    endpoint = f"http://127.0.0.1:{port}"
    version_url = f"{endpoint}/json/version"
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            await asyncio.to_thread(lambda: urllib.request.urlopen(version_url, timeout=1).read())
            return endpoint
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.2)

    raise RuntimeError(f"CDP endpoint did not become ready at {version_url}: {last_error!r}")


@asynccontextmanager
async def cloakbrowser_cdp(headless: bool = True, locale: str = "en-US", timezone: str = "Asia/Tokyo"):
    binary_path = ensure_binary()
    port = pick_free_port()
    profile = tempfile.TemporaryDirectory(prefix="cloakbrowser-cdp-")
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
        profile.cleanup()


async def new_cdp_page(browser, viewport: dict[str, int]):
    context = browser.contexts[0] if browser.contexts else await browser.new_context()
    page = context.pages[0] if context.pages else await context.new_page()
    await page.set_viewport_size(viewport)
    return page


async def main() -> None:
    async with cloakbrowser_cdp(headless=True, locale="en-US", timezone="Asia/Tokyo") as browser:
        page = await new_cdp_page(browser, {"width": 1365, "height": 900})
        results = {}

        for site, url in URLS.items():
            print("OPEN", site, flush=True)
            row = {"url": url}
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=90000)
                row["status"] = resp.status if resp else None
                await page.wait_for_timeout(9000)
                row["title"] = await page.title()
                row["final_url"] = page.url
                text = await page.locator("body").inner_text(timeout=10000)
                row["len"] = len(text)
                row["sample"] = text[:2000]
                row["photo_count"] = text.count("Photo gallery for ")
                row["prices"] = PRICE_RE.findall(text)[:20]
            except Exception as exc:
                row["fatal"] = repr(exc)
            results[site] = row

    out = OUT / "results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"WROTE {out}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
