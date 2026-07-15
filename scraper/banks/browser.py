"""Headless-browser helper for sites that block plain HTTP or render with JS.

Playwright is optional. If it (or its Chromium) isn't installed, run_in_page()
returns None and adapters fall back to a link-only listing. CI installs it, so
those sources get fully scraped there.

Design: the adapter passes a handler(html, fetch_pdf) that runs *while the
browser context is still open*, so fetch_pdf() inherits the page's anti-bot
cookies. Whatever the handler returns is returned to the adapter.
"""
from __future__ import annotations


def available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except Exception:
        return False


def run_in_page(url, handler, wait_selector=None, timeout_ms=45000):
    """Open `url` in headless Chromium and call handler(html, fetch_pdf).

    Returns handler(...) result, or None if a browser isn't available / fails.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                ),
                locale="mk-MK",
            )
            page = ctx.new_page()
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=8000)
                except Exception:
                    pass
            html = page.content()

            def fetch_pdf(pdf_url):
                try:
                    resp = ctx.request.get(pdf_url, timeout=timeout_ms)
                    if resp.ok and resp.body()[:4] == b"%PDF":
                        return resp.body()
                except Exception:
                    pass
                return None

            try:
                return handler(html, fetch_pdf)
            finally:
                ctx.close()
                browser.close()
    except Exception:
        return None
