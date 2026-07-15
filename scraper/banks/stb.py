"""Stopanska Banka (STB) — listings are rendered client-side, so plain HTTP sees
almost nothing. Render with a headless browser; fall back to the page link."""
import re

from bs4 import BeautifulSoup

from .. import common as c
from . import browser

NAME = "Stopanska"
PAGE = "https://www.stb.com.mk/ostanati-sodrzini/prodazba-na-imot/prodazba-na-imot-od-khipoteka/"


def _parse(html, fetch_pdf):
    soup = BeautifulSoup(html, "html.parser")
    out, seen = [], set()
    # property PDFs
    for a in soup.find_all("a", href=re.compile(r"\.pdf", re.I)):
        label = c.norm_ws(a.get_text(" ", strip=True))
        href = a["href"]
        if not re.search(r"(имот|стан|куќа|деловен|земј|prodazba|imot)", (label + href), re.I):
            continue
        url = href if href.startswith("http") else "https://www.stb.com.mk" + ("" if href.startswith("/") else "/") + href
        if url in seen:
            continue
        seen.add(url)
        title = label if len(label) > 4 else c.slug_to_text(url)
        out.append(c.listing(NAME, title, PAGE, prop_type=c.guess_type(title),
                             location=c.guess_city(title), pdf_url=url))
    # text blocks mentioning area (rendered cards without PDFs)
    if not out:
        for el in soup.find_all(["li", "div", "article"]):
            t = c.norm_ws(el.get_text(" ", strip=True))
            if 15 < len(t) < 300 and c.find_area(t) and c.guess_type(t):
                if t in seen:
                    continue
                seen.add(t)
                out.append(c.listing(NAME, t[:120], PAGE, prop_type=c.guess_type(t),
                                     location=c.guess_city(t), area_m2=c.find_area(t)))
    return out


def scrape(s):
    result = browser.run_in_page(PAGE, _parse, wait_selector="a[href$='.pdf'], table")
    if result:
        return result
    return [c.listing(NAME, "Продажба на имот од хипотека — Stopanska Банка", PAGE)]
