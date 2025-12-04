import asyncio
import csv
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

# -----------------------------------
# CONFIG
# -----------------------------------

FROM_DATE = "2025-11-17"
TO_DATE   = "2025-11-23"

OUTPUT_FILE = "match_links.csv"

FEDERATIONS = [
    "3","13","18","19","20","22","23","24","4","44","6","7","8","1",
    "9","10","11","12","14","17","15","21","5","16",
]

# match pattern: /sasong/43/serie/41140/match/1628521
MATCH_PATTERN = re.compile(r"^/sasong/\d+/serie/\d+/match/\d+$")

BLOCK_PATTERNS = [
    ".png",".jpg",".jpeg",".gif",".webp",".svg",
    ".woff",".woff2",".ttf",".otf",
    "googletagmanager","google-analytics","hotjar","doubleclick"
]


# -----------------------------------
# RESOURCE BLOCKING
# -----------------------------------

async def block_resources(route):
    url = route.request.url.lower()
    if route.request.resource_type in {"image", "media", "font"}:
        return await route.abort()
    if any(p in url for p in BLOCK_PATTERNS):
        return await route.abort()
    await route.continue_()


# -----------------------------------
# DATE RANGE GENERATOR
# -----------------------------------

def date_range(start, end):
    d1 = datetime.strptime(start, "%Y-%m-%d")
    d2 = datetime.strptime(end, "%Y-%m-%d")
    while d1 <= d2:
        yield d1.strftime("%Y-%m-%d")
        d1 += timedelta(days=1)


# -----------------------------------
# SCRAPE FOR ONE DAY + ONE FEDERATION
# -----------------------------------

async def scrape_day(page, date_str, federation_id):
    url = f"https://stats.innebandy.se/forbund/{federation_id}/livematches/{date_str}"

    try:
        await page.goto(url, timeout=20000)
        await page.wait_for_load_state("networkidle")
    except Exception:
        print(f"[WARN] Timeout on {url}")
        return []

    anchors = await page.locator('a[href^="/sasong/"]').all()

    links = []
    for a in anchors:
        href = await a.get_attribute("href")
        if href and MATCH_PATTERN.match(href):
            full_url = "https://stats.innebandy.se" + href + "/laguppstallning"
            links.append(full_url)

    print(f"[OK] {date_str} | federation {federation_id} | {len(links)} match links")
    return links


# -----------------------------------
# MAIN
# -----------------------------------

async def main():
    all_rows = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        await context.route("**/*", block_resources)
        page = await context.new_page()

        for date in date_range(FROM_DATE, TO_DATE):
            for fed in FEDERATIONS:
                links = await scrape_day(page, date, fed)
                for link in links:
                    all_rows.append([date, fed, link])

        await browser.close()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "federationId", "match_link"])
        writer.writerows(all_rows)

    print(f"\nSaved {len(all_rows)} rows → {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
