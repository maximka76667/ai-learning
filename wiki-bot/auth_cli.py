import json
import time
from playwright.sync_api import sync_playwright

WIKI_URL = "https://wiki.hyperloopupv.com"
COOKIE_FILE = "cookies.json"


def login_and_save_cookies(headless=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Always visible
        context = browser.new_context()
        page = context.new_page()

        print(f"Opening {WIKI_URL}...")
        page.goto(WIKI_URL)

        print("\n" + "=" * 50)
        print("ACTION REQUIRED:")
        print("1. Log in with Slack in the browser window.")
        print("2. Click 'Accept' or 'Allow' if asked.")
        print("3. WAIT until you see the Wiki Home Page.")
        print("4. Come back here and PRESS ENTER.")
        print("=" * 50 + "\n")

        input("Press Enter when you are fully logged in...")

        # Save cookies
        cookies = context.cookies()

        # Verify we got something useful
        wiki_cookies = [c for c in cookies if "wiki.hyperloopupv.com" in c["domain"]]
        print(f"Found {len(wiki_cookies)} cookies for the Wiki domain.")

        with open(COOKIE_FILE, "w") as f:
            json.dump(cookies, f, indent=2)

        print(f"Saved cookies to {COOKIE_FILE}")
        browser.close()


if __name__ == "__main__":
    login_and_save_cookies()
