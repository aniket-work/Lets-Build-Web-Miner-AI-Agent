from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig, LLMExtractionStrategy
from models.car import Car
import os
import tempfile
import json
from typing import List, Set
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from playwright.async_api import async_playwright

def get_browser_config() -> BrowserConfig:
    return BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

def get_llm_strategy() -> LLMExtractionStrategy:
    return LLMExtractionStrategy(
        provider="openai/gpt-4o",
        api_token=os.getenv("OPENAI_API_KEY"),
        schema=Car.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "Extract a car object with 'year', 'name', 'kilometers', and 'price' from the following content. "
            "The content represents a single car listing in HTML format. Follow these rules strictly:\n"
            "- 'year' must be an integer (e.g., 2020). It is typically the first part of the car title.\n"
            "- 'name' must be the car model as a string (e.g., 'Mercedes-Benz C-Class C 300 4MATIC'). It follows the year in the car title.\n"
            "- 'kilometers' must be a string with the unit 'km' (e.g., '72,942 km'). It is usually below the car title.\n"
            "- 'price' must be a string with the currency symbol (e.g., '$32,990'). It is the main price, typically the largest price text. "
            "Exclude any additional text like 'or $321/biweekly', 'SALE', or other payment details.\n"
            "If any field cannot be extracted correctly, return an empty object {}."
        ),
        input_format="markdown",
        verbose=True,
    )


async def fetch_and_process_page(
    crawler: AsyncWebCrawler,
    base_url: str,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_names: Set[str],
) -> List[dict]:
    print(f"[INFO] Starting fetch_and_process_page for URL: {base_url} (initial load only)")
    all_cars = []
    seen_elements = set()

    # Step 1: Set up Playwright browser
    print("[INFO] Launching Playwright browser")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
            print("[INFO] Browser launched successfully")
        except Exception as e:
            print(f"[ERROR] Failed to launch browser: {e}")
            return []

        try:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            print("[INFO] Browser context created")
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")
            print("[INFO] Anti-detection script added to context")
        except Exception as e:
            print(f"[ERROR] Failed to create browser context: {e}")
            await browser.close()
            return []

        try:
            page = await context.new_page()
            print("[INFO] New page created")
        except Exception as e:
            print(f"[ERROR] Failed to create new page: {e}")
            await browser.close()
            return []

        # Step 2: Navigate to the page
        try:
            print(f"[INFO] Navigating to URL: {base_url}")
            await page.goto(base_url)
            print("[INFO] Page navigation successful")
        except Exception as e:
            print(f"[ERROR] Failed to navigate to URL {base_url}: {e}")
            await browser.close()
            return []

        # Step 3: Wait for car listings to load
        try:
            print(f"[INFO] Waiting for elements with selector: {css_selector}")
            await page.wait_for_selector(css_selector, timeout=10000)
            print("[INFO] Elements found within timeout")
        except Exception as e:
            print(f"[ERROR] Error waiting for selector '{css_selector}': {e}")
            await browser.close()
            return []

        # Step 4: Find all car listing elements
        try:
            elements = await page.query_selector_all(css_selector)
            print(f"[INFO] Found {len(elements)} elements with selector '{css_selector}'")
        except Exception as e:
            print(f"[ERROR] Failed to find elements with selector '{css_selector}': {e}")
            await browser.close()
            return []

        # Step 5: Process each element
        for idx, element in enumerate(elements):
            print(f"[INFO] Processing element {idx + 1}/{len(elements)}")

            # Step 5.1: Extract HTML for the element
            try:
                element_html = await element.inner_html()
                print(f"[INFO] Element {idx + 1}: HTML extracted successfully (length: {len(element_html)})")
            except Exception as e:
                print(f"[ERROR] Element {idx + 1}: Failed to extract HTML: {e}")
                continue

            # Step 5.2: Check for duplicate elements
            element_id = hash(element_html)
            if element_id in seen_elements:
                print(f"[INFO] Element {idx + 1}: Skipped (duplicate element)")
                continue
            seen_elements.add(element_id)
            print(f"[INFO] Element {idx + 1}: Added to seen_elements (ID: {element_id})")

            # Step 5.3: Write HTML to temporary file
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(f"<html><body>{element_html}</body></html>")
                    temp_file_path = temp_file.name
                print(f"[INFO] Element {idx + 1}: Temporary file created at {temp_file_path}")
            except Exception as e:
                print(f"[ERROR] Element {idx + 1}: Failed to create temporary file: {e}")
                continue

            # Step 5.4: Process the temporary file with crawl4ai
            temp_file_path_fixed = temp_file_path.replace('\\', '/')
            temp_file_url = f"file://{temp_file_path_fixed}"
            print(f"[INFO] Element {idx + 1}: Processing temporary file URL: {temp_file_url}")

            try:
                result = await crawler.arun(
                    url=temp_file_url,
                    config=CrawlerRunConfig(
                        cache_mode="BYPASS",
                        extraction_strategy=llm_strategy,
                        css_selector="",
                        session_id=session_id,
                    ),
                )
                print(f"[INFO] Element {idx + 1}: crawl4ai processing completed (success: {result.success})")
            except Exception as e:
                print(f"[ERROR] Element {idx + 1}: crawl4ai processing failed: {e}")
                os.unlink(temp_file_path)
                continue

            # Step 5.5: Clean up temporary file
            try:
                os.unlink(temp_file_path)
                print(f"[INFO] Element {idx + 1}: Temporary file deleted: {temp_file_path}")
            except Exception as e:
                print(f"[ERROR] Element {idx + 1}: Failed to delete temporary file {temp_file_path}: {e}")

            # Step 5.6: Check extraction result
            if not (result.success and result.extracted_content):
                print(f"[ERROR] Element {idx + 1}: Extraction failed: {result.error_message}")
                continue
            print(f"[INFO] Element {idx + 1}: Extraction successful, content available")

            # Step 5.7: Parse extracted content
            try:
                extracted_data = json.loads(result.extracted_content)
                print(f"[INFO] Element {idx + 1}: Extracted data: {extracted_data}")
            except Exception as e:
                print(f"[ERROR] Element {idx + 1}: Failed to parse extracted content: {e}")
                continue

            # Step 5.8: Determine car object
            car = extracted_data if isinstance(extracted_data, dict) else extracted_data[0] if extracted_data else None
            print(f"[INFO] Element {idx + 1}: Car object: {car}")

            if not car:
                print(f"[INFO] Element {idx + 1}: Skipping car: No valid data extracted")
                continue

            # Step 5.9: Post-process the extracted data
            try:
                if "year" in car:
                    car["year"] = int(car["year"])
                    print(f"[INFO] Element {idx + 1}: Post-processed 'year': {car['year']}")
                if "price" in car:
                    car["price"] = car["price"].split(" or ")[0].strip().replace("SALE", "").strip()
                    print(f"[INFO] Element {idx + 1}: Post-processed 'price': {car['price']}")
                if "kilometers" in car and "km" not in car["kilometers"]:
                    car["kilometers"] = f"{car['kilometers']} km"
                    print(f"[INFO] Element {idx + 1}: Post-processed 'kilometers': {car['kilometers']}")
            except Exception as e:
                print(f"[ERROR] Element {idx + 1}: Error post-processing car data: {e}")
                continue

            # Step 5.10: Check for extraction error
            if car.get("error") is True:
                print(f"[INFO] Element {idx + 1}: Skipping car due to extraction error (error: {car.get('error')})")
                continue
            print(f"[INFO] Element {idx + 1}: No extraction error (error: {car.get('error', 'not present')})")

            # Step 5.11: Check for required keys
            if not all(key in car for key in required_keys):
                print(f"[INFO] Element {idx + 1}: Skipping car: Missing required keys. Car: {car}")
                continue
            print(f"[INFO] Element {idx + 1}: All required keys present: {required_keys}")

            # Step 5.12: Check for duplicates
            car_identifier = f"{car['year']}_{car['name']}"
            if car_identifier in seen_names:
                print(f"[INFO] Element {idx + 1}: Duplicate car '{car_identifier}' skipped")
                continue
            seen_names.add(car_identifier)
            print(f"[INFO] Element {idx + 1}: Added car identifier to seen_names: {car_identifier}")

            # Step 5.13: Add car to list
            all_cars.append(car)
            print(f"[INFO] Element {idx + 1}: Car added to all_cars: {car}")

        # Step 6: Close browser
        try:
            await browser.close()
            print("[INFO] Browser closed successfully")
        except Exception as e:
            print(f"[ERROR] Failed to close browser: {e}")

    print(f"[INFO] Extracted {len(all_cars)} cars from the initial page load")
    return all_cars  

# Example usage
async def main():
    crawler = AsyncWebCrawler(get_browser_config())
    base_url = "https://www.clutch.ca/cars"  # Adjust as needed
    css_selector = ".vehicle-listing"  # Adjust based on actual HTML structure
    llm_strategy = get_llm_strategy()
    session_id = "session_123"
    required_keys = ["year", "name", "kilometers", "price"]
    seen_names = set()

    cars = await fetch_and_process_page(
        crawler, base_url, css_selector, llm_strategy, session_id, required_keys, seen_names
    )

    # Save to CSV or process as needed
    import csv
    with open("complete_cars.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=required_keys)
        writer.writeheader()
        writer.writerows(cars)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())