"""Alta Banka — page and its combined PDF both block plain HTTP (503). Load the
page in a browser, find the combined 'Оглас за продажба' PDF, and download it
through the browser context (inherits anti-bot cookies) to parse the table."""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .. import common as c
from . import browser

NAME = "Alta"
PAGE = "https://altabanka.com.mk/prodazba-na-imot.nspx"
PICK = re.compile(r"(оглас|недвиж|имот|prevzemenimot|prodazba)", re.I)


def _parse(html, fetch_pdf):
    soup = BeautifulSoup(html, "html.parser")
    pdfs, seen = [], set()
    for a in soup.find_all("a", href=re.compile(r"\.pdf", re.I)):
        hay = c.norm_ws(a.get_text(" ", strip=True)) + " " + a["href"]
        if PICK.search(hay):
            url = urljoin(PAGE, a["href"])
            if url not in seen:
                seen.add(url)
                pdfs.append(url)

    out = []
    for pdf in pdfs[:3]:
        data = fetch_pdf(pdf)
        if not data:
            out.append(c.listing(NAME, c.slug_to_text(pdf), PAGE, pdf_url=pdf))
            continue
        items = c.parse_combined_pdf(data, NAME, PAGE)
        for it in items:
            it["pdf_url"] = pdf
        out.extend(items or [c.listing(NAME, c.slug_to_text(pdf), PAGE, pdf_url=pdf)])
    return out


def scrape(s):
    result = browser.run_in_page(PAGE, _parse, wait_selector="a[href$='.pdf']")
    if result:
        return result
    return [c.listing(NAME, "Продажба на недвижен имот — Alta Банка", PAGE)]
