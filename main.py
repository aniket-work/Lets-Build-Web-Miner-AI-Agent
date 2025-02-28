import asyncio
import random

from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

from config import BASE_URL, CSS_SELECTOR, REQUIRED_KEYS
from utils.data_loader_utils import (
    save_cars_to_csv,
)
from utils.data_loader_utils import (
    fetch_and_process_page,
    get_browser_config,
    get_llm_strategy,
)

load_dotenv()


async def crawl_cars():
    """
    Main function to crawl car data from the website using infinite scrolling.
    """
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    session_id = "car_crawl_session"

    all_cars = []
    seen_identifiers = set()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Fetch and process data using infinite scrolling
        cars = await fetch_and_process_page(
            crawler,
            BASE_URL,
            CSS_SELECTOR,
            llm_strategy,
            session_id,
            REQUIRED_KEYS,
            seen_identifiers,
        )

        if not cars:
            print("No cars extracted.")
        else:
            all_cars.extend(cars)

    if all_cars:
        save_cars_to_csv(all_cars, "complete_cars.csv")
        print(f"Saved {len(all_cars)} cars to 'complete_cars.csv'.")
    else:
        print("No cars were found during the crawl.")

    llm_strategy.show_usage()


async def main():
    """
    Entry point of the script.
    """
    await crawl_cars()


if __name__ == "__main__":
    asyncio.run(main())