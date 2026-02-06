import asyncio
import json
import os
import sys
from typing import List
import html2text
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import requests
from langchain_community.document_loaders import RecursiveUrlLoader
from bs4 import BeautifulSoup as Soup
from langchain_core.documents import Document
from config import COOKIES_FILE, WIKI_URL
from auth_cli import login_and_save_cookies
from logger import log_node


def get_all_wiki_paths(base_url, cookies_list):
    # Convert cookie list to dict for requests
    cookies = {c["name"]: c["value"] for c in cookies_list}

    # Wiki.js GraphQL Query
    query = """
    {
      pages {
        list (orderBy: TITLE) {
          path
          title
        }
      }
    }
    """

    response = requests.post(
        f"{base_url}/graphql",
        json={"query": query},
        cookies=cookies,
        headers={
            "Authorization": f"Bearer {cookies.get('token') or cookies.get('jwt')}"  # Try to find token if needed
        },
    )

    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        print(response.text)
        return []

    try:
        data = response.json()
        pages = data["data"]["pages"]["list"]
        # Return full URLs
        return [f"{base_url}/{p['path']}" for p in pages]
    except Exception as e:
        print(f"Failed to parse API response: {e}")
        return []


with open(COOKIES_FILE) as f:
    cookie_list = json.load(f)


urls = get_all_wiki_paths(WIKI_URL, cookie_list)


async def scrape_single_page(context, url, sem):
    """
    Scrapes a single page asynchronously with semaphore limiting.
    """
    async with sem:  # Controls how many tabs open at once (max 10)
        page = None
        try:
            page = await context.new_page()

            await page.goto(url, timeout=30000)
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except:
                print(f"Timeout waiting for content on {url}")
                await asyncio.sleep(2)

            title = await page.title()

            if "Page Not Found" in title or "404" in title:
                print(f"Skipping 404/Not Found: {url}")
                await page.close()
                return None

            full_html = await page.content()

            await page.close()

            # 2. Filter with BeautifulSoup (Reliable)
            soup = Soup(full_html, "html.parser")

            for element in soup(["script", "style", "svg", "noscript"]):
                element.extract()

            # Find Content
            content_div = soup.select_one(".contents") or soup.body

            # Find Comments
            comments_div = soup.select_one(".comments-main")

            # Construct clean HTML
            clean_html = ""
            if content_div:
                clean_html += str(content_div)

            if comments_div:
                clean_html += "\n<hr><h2>Comments</h2>\n" + str(comments_div)

            # 3. Convert to Markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.body_width = 0
            markdown_content = h.handle(clean_html)

            if "hardware" in url.lower() and "pcu" not in url.lower():
                print(f"\n--- DEBUG MARKDOWN for {url} ---")
                print(markdown_content)
                print("--------------------------------\n")

            print(f"Scraped: {'/'.join(url.split('/')[3:])}")

            return Document(
                page_content=f"# {title}\nURL: {url}\n\n{markdown_content}",
                metadata={"source": url, "title": title},
            )

        except Exception as e:
            print(f"Failed {url}: {e}")
            if page:
                await page.close()
            return None


async def crawl_wiki_pages_async(target_urls, cookies_list):
    print(f"Starting async scrape of {len(target_urls)} pages...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(cookies_list)

        # Limit concurrency to avoid crashing the browser or getting banned
        sem = asyncio.Semaphore(10)

        tasks = [scrape_single_page(context, url, sem) for url in target_urls]
        results = await asyncio.gather(*tasks)

        await browser.close()

        valid_docs = [r for r in results if r]
        print(
            f"Finished! Successfully scraped {len(valid_docs)}/{len(target_urls)} pages."
        )
        return valid_docs


# Wrapper to run it synchronously
def fast_crawl(urls, cookies):
    return asyncio.run(crawl_wiki_pages_async(urls, cookies))


def get_cookies_dict():
    if not os.path.exists(COOKIES_FILE):
        print("No cookies found! Run 'python auth_cli.py' first.")
        return {}

    with open(COOKIES_FILE, "r") as f:
        cookie_list = json.load(f)

    # Convert Playwright list format to Dict format for Requests
    return {c["name"]: c["value"] for c in cookie_list}


def crawl_wiki_pages(target_urls: List[str], cookies_list: List[dict]):
    """
    Scrapes a specific list of URLs using Playwright + Markdown conversion.
    """
    documents = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(cookies_list)
        page = context.new_page()

        for i, url in enumerate(target_urls):
            print(f"[{i+1}/{len(target_urls)}] Scraping {url}...")

            try:
                page.goto(url)
                page.wait_for_load_state("networkidle")

                title = page.title()

                # 1. Extract Main Content
                main_html = ""
                for selector in [".contents", ".v-main__wrap", "article", "#app"]:
                    if page.locator(selector).count() > 0:
                        main_html = page.locator(selector).first.inner_html()
                        break

                # 2. Extract Comments (Optional)
                comments_html = ""
                for comment_sel in [".comments", ".page-comments"]:
                    if page.locator(comment_sel).count() > 0:
                        comments_html = page.locator(comment_sel).first.inner_html()
                        break

                # Combine
                full_html = main_html or page.inner_html("body")
                if comments_html:
                    full_html += f"\n<hr>\n<h2>Comments</h2>\n{comments_html}"

                # 3. Convert to Markdown
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.body_width = 0  # Don't wrap lines
                markdown_content = h.handle(full_html)

                # 4. Enrich Content
                enriched_content = f"# {title}\nURL: {url}\n\n{markdown_content}"

                documents.append(
                    Document(
                        page_content=enriched_content,
                        metadata={"source": url, "title": title},
                    )
                )

            except Exception as e:
                print(f"Failed to scrape {url}: {e}")

        browser.close()

    return documents


def load_data_with_retry():
    max_retries = 1

    if "-r" in sys.argv and os.path.exists("cookies.json"):
        print("Removing cookies.json...")
        os.remove("cookies.json")

    for attempt in range(max_retries + 1):
        try:
            cookies = get_cookies_dict()

            # Check if we even have cookies
            if not cookies and attempt == 0:
                print("No cookies found. Launching login...")
                login_and_save_cookies()
                cookies = get_cookies_dict()

            print(f"Loading pages... (Attempt {attempt+1})")
            loader = RecursiveUrlLoader(
                url=WIKI_URL,
                max_depth=10,
                extractor=lambda x: Soup(x, "html.parser").text,
                headers={
                    "Cookie": "; ".join([f"{k}={v}" for k, v in cookies.items()]),
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                },
            )
            data = loader.load()

            # Simple check: if data is empty or looks like a login page, raise error
            if not data or "Sign in to your account" in data[0].page_content:
                raise Exception("Auth failed (Login page detected)")

            return data

        except Exception as e:
            print(f"Error loading data: {e}")
            if attempt < max_retries:
                print("Cookie might be expired. Refreshing auth...")
                login_and_save_cookies()  # This opens the browser window
            else:
                print("Failed after refreshing cookies.")
                raise e
