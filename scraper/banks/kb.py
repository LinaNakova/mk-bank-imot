"""Komercijalna Banka (KB) — the forced-collection page blocks plain HTTP (503).
A real browser context passes; parse the rendered table/links, else link only."""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .. import common as c
from . import browser

NAME = "Komercijalna"
PAGE = "https://www2.kb.mk/ImotPrisilnaNaplata.aspx"


def _parse(html, fetch_pdf):
    soup = BeautifulSoup(html, "html.parser")
    out, seen = [], set()

    for tr in soup.select("table tr"):
        tds = tr.find_all(["td", "th"])
        if len(tds) < 2:
            continue
        text = c.norm_ws(" ".join(td.get_text(" ", strip=True) for td in tds))
        low = text.lower()
        if not text or low.startswith(("опис", "реден", "р.бр")):
            continue
        if not (c.guess_type(text) or c.find_area(text) or c.guess_city(text)):
            continue
        a = tr.find("a", href=True)
        pdf = urljoin(PAGE, a["href"]) if a and ".pdf" in a["href"].lower() else None
        key = pdf or text
        if key in seen:
            continue
        seen.add(key)
        out.append(c.listing(NAME, text[:120], PAGE, prop_type=c.guess_type(text),
                             location=c.guess_city(text), area_m2=c.find_area(text),
                             pdf_url=pdf))

    for a in soup.find_all("a", href=re.compile(r"\.pdf", re.I)):
        hay = c.norm_ws(a.get_text(" ", strip=True)) + " " + a["href"]
        if not re.search(r"(имот|стан|куќа|деловен|земј|imot)", hay, re.I):
            continue
        pdf = urljoin(PAGE, a["href"])
        if pdf in seen:
            continue
        seen.add(pdf)
        out.append(c.listing(NAME, c.norm_ws(a.get_text(" ", strip=True)) or c.slug_to_text(pdf),
                             PAGE, prop_type=c.guess_type(hay), location=c.guess_city(hay),
                             pdf_url=pdf))
    return out


def scrape(s):
    result = browser.run_in_page(PAGE, _parse, wait_selector="table")
    if result:
        return result
    return [c.listing(NAME, "Имот од присилна наплата — Комерцијална Банка", PAGE)]
