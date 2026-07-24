import asyncio
import pandas as pd
import re
from playwright.async_api import async_playwright
import nest_asyncio
import os

# Configuration
BASE_URL = "https://www.imf.org/en/publications/search#cf-type=COUNTRYREPS,ARTICLE4&numberOfResults=50"
DOMAIN = "https://www.imf.org"
OUTPUT_FILE = "imf_reports_final.csv"

# --- CONFIGURATION ---
BATCH_SIZE_REPORTS = 100  # Total reports you want to grab in this run
RESULTS_PER_PAGE = 50     # Keep this at 50 as per your working URL

def extract_year(text):
    match = re.search(r'20\d{2}', text)
    return match.group(0) if match else "Unknown"

def get_last_counter():
    """Checks existing CSV to see where to resume."""
    if os.path.exists(OUTPUT_FILE):
        try:
            df = pd.read_csv(OUTPUT_FILE)
            return len(df)
        except: return 0
    return 0


async def main():
    data = []
    
    start_from = get_last_counter()
    print(f"==============currrent count {start_from}==================")
    reports_collected_this_run = 0
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        while reports_collected_this_run < BATCH_SIZE_REPORTS:
            current_offset = start_from + reports_collected_this_run

            # Construct the exact URL format you confirmed works
            if current_offset < 50:
                BASE_URL = "https://www.imf.org/en/publications/search#cf-type=COUNTRYREPS,ARTICLE4&numberOfResults=50"
                
            else:
                BASE_URL = f"https://www.imf.org/en/publications/search#cf-type=COUNTRYREPS,ARTICLE4&firstResult={current_offset}&numberOfResults={RESULTS_PER_PAGE}"
            print(f"Opening Search: {BASE_URL}")
            
            try:
                await page.goto(BASE_URL, wait_until="commit", timeout=60000)
                print("Page committed. Waiting for results to render...")
                await page.wait_for_selector('.coveo-results-column, .CoveoResultList', timeout=60000)
                
                # Click 50 to get more data at once
                try:
                    per_page_50 = page.get_by_text("50", exact=True)
                    await per_page_50.click()
                    print("Clicked 50 results. Waiting for refresh...")
                    await asyncio.sleep(10)
                except:
                    pass
                
            except Exception as e:
                print(f"Initialization Error: {e}")
                await browser.close()
                return

            links_locator = page.locator('a.CoveoResultLink')
            count = await links_locator.count()
            
            if count == 0:
                links_locator = page.locator('a[href*="/en/publications/cr/issues/"]')
                count = await links_locator.count()

            print(f"Found {count} reports to process.")

            links_to_visit = []
            for i in range(count):
                el = links_locator.nth(i)
                raw_url = await el.get_attribute('href')
                raw_title = await el.inner_text()
                if raw_url:
                    full_url = raw_url if raw_url.startswith('http') else DOMAIN + raw_url
                    links_to_visit.append({'url': full_url, 'title': raw_title})

            for i, report in enumerate(links_to_visit):
                print(f"[{i+1}/{len(links_to_visit)}] Visiting: {report['title'][:50]}...")
                
                detail_page = await context.new_page()
                try:
                    await detail_page.goto(report['url'], wait_until="domcontentloaded", timeout=30000)
                    
                    # --- SUMMARY EXTRACTION (FIXED) ---
                    summary = "N/A"
                    # .last avoids the citation and disclaimer divs that share the same class
                    summary_locator = detail_page.locator('div.publication-text').last
                    
                    if await summary_locator.count() > 0:
                        raw_text = await summary_locator.inner_text()
                        summary = re.sub(r'^Summary\s+', '', raw_text.strip(), flags=re.IGNORECASE)
                    
                    # --- PDF EXTRACTION ---
                    pdf_link = "N/A"
                    pdf_el = detail_page.locator('a:has-text("Download PDF"), a[href$=".pdf"]').first
                    if await pdf_el.count() > 0:
                        raw_pdf = await pdf_el.get_attribute('href')
                        pdf_link = raw_pdf if raw_pdf.startswith('http') else DOMAIN + raw_pdf

                    # --- COUNTRY & YEAR ---
                    country = report['title'].split(":")[0].strip() if ":" in report['title'] else "N/A"
                    year = extract_year(report['title'])

                    data.append({
                        'Counter': start_from + reports_collected_this_run + 1,
                        'Country': country,
                        'Year': year,
                        'Title': report['title'],
                        'Summary': summary.strip(),
                        'PDF': pdf_link,
                        'URL': report['url']
                    })
                    reports_collected_this_run += 1

                except Exception as detail_e:
                    print(f"   Error on detail page: {detail_e}")
                
                await detail_page.close()
                await asyncio.sleep(1)

            # Save after every page of 50 for safety
            if data: 
                df = pd.DataFrame(data)
                file_exists = os.path.isfile(OUTPUT_FILE)
                df.to_csv(OUTPUT_FILE, mode='a', index=False, header=not file_exists, encoding='utf-8-sig')
                print(f"Saved batch to {OUTPUT_FILE}")
                data = []
                print("=============================================")



        await browser.close()

    if data:
        df = pd.DataFrame(data)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"\nSUCCESS: Saved {len(data)} reports with full data to {OUTPUT_FILE}")

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())