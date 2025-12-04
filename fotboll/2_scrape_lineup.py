import asyncio
import csv
from playwright.async_api import async_playwright

INPUT_FILE = "match_links.csv"
OUTPUT_FILE = "match_details.csv"


def clean_text(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = s.replace("\n", " ").replace("\r", " ")
    s = s.replace("\"", "")
    s = " ".join(s.split())
    return s


async def scrape_match(page, date, federationId, link):
    base_link = link.replace("/laguppstallning", "")

    try:
        await page.goto(link, timeout=20000)
        await page.wait_for_load_state("networkidle")
    except Exception:
        print(f"[WARN] Timeout: {link}")
        return None

    # Säsong
    season_node = page.locator("span.rum5v").first
    season = clean_text(await season_node.text_content() if await season_node.count() > 0 else "")

    # Serie
    serie_node = page.locator("h1").first
    serie = clean_text(await serie_node.text_content() if await serie_node.count() > 0 else "")

    # -------------------------
    # ARENA (3rd strong)
    # MATCHNR (last strong)
    # -------------------------

    arena = ""
    matchnr = ""

    header_strongs = page.locator("div.FMsFg strong")
    count = await header_strongs.count()

    # Arena = third <strong>
    if count >= 3:
        arena = clean_text(await header_strongs.nth(2).text_content())

    # Matchnr = LAST <strong> in the header
    if count >= 1:
        matchnr = clean_text(await header_strongs.nth(count - 1).text_content())

    # Home & away
    teams = await page.locator("h3.QmXlT").all_text_contents()
    home = clean_text(teams[0] if len(teams) >= 1 else "")
    away = clean_text(teams[1] if len(teams) >= 2 else "")

    # Domare
    ref_nodes = page.locator("div.Vsp4o table tbody tr td a")
    refs = await ref_nodes.all_text_contents()
    domare1 = clean_text(refs[0] if len(refs) > 0 else "")
    domare2 = clean_text(refs[1] if len(refs) > 1 else "")

    return [
        date,
        federationId,
        base_link,
        season,
        serie,
        arena,
        matchnr,
        home,
        away,
        domare1,
        domare2
    ]



async def main():
    rows_out = []

    # Read CSV input
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for row in rows:
            date = row["date"]
            federation = row["federationId"]
            link = row["match_link"]

            print(f"[SCRAPE] {link}")
            data = await scrape_match(page, date, federation, link)
            if data:
                rows_out.append(data)

        await browser.close()

    # Save output
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date",
            "federationId",
            "match_link",
            "season",
            "serie",
            "arena",
            "home_team",
            "away_team",
            "domare1",
            "domare2"
        ])
        writer.writerows(rows_out)

    print(f"\nSaved {len(rows_out)} rows → {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
