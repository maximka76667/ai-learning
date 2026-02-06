import asyncio
import json
import sys
from config import WIKI_URL, COOKIES_FILE
from crawler import get_all_wiki_paths, crawl_wiki_pages_async
from vector_store import populate_vector_store
from graph import build_workflow
from logger import update_line


async def main():
    should_reset = "--reset" in sys.argv

    if should_reset:

        # 1. Load cookies
        try:
            with open(COOKIES_FILE) as f:
                cookie_list = json.load(f)
        except FileNotFoundError:
            print("Please run auth_cli.py first to generate cookies.")
            return

        # 2. Scrape (Optional: Add a flag to skip this if DB exists)
        urls = get_all_wiki_paths(WIKI_URL, cookie_list)
        documents = await crawl_wiki_pages_async(urls, cookie_list)

        # 3. Index
        populate_vector_store(documents, reset=should_reset)
    else:
        print("Using existing vector store (pass --reset to refresh).")

    # 4. Run Graph
    app = build_workflow()

    initial_state = {
        "query": "Explain me PCU. What microcontroller is used in it?",
        "intent_node_output_ok": False,
        "intent_node_output": None,
        "search_node_output": None,
        "context_chunks": [],
        "summarize_node_output": None,
    }

    final_state = await app.ainvoke(initial_state)
    update_line(f"Final answer: {final_state['summarize_node_output']}")


if __name__ == "__main__":
    asyncio.run(main())
