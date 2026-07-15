"""ProCredit Bank (PCB) — page links to a combined 'Објава имот' PDF plus regulatory
forms. Pick the property announcement PDF and parse its table."""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .. import common as c

NAME = "ProCredit"
PAGE = "https://www.pcb.mk/prodazba-na-imot.nspx"
PICK = re.compile(r"(објава|objava|недвиж|nedviz|имот наменет)", re.I)
SKIP = re.compile(r"(движен имот|образец|obrazec)", re.I)  # prefer real estate list


def scrape(s):
    r = c.get(PAGE, s=s)
    if r is None:
        return [c.listing(NAME, "Продажба на имот — ProCredit", PAGE)]

    soup = BeautifulSoup(r.text, "html.parser")
    candidates = []
    for a in soup.find_all("a", href=re.compile(r"\.pdf", re.I)):
        label = c.norm_ws(a.get_text(" ", strip=True))
        hay = label + " " + a["href"]
        if PICK.search(hay) and not SKIP.search(hay):
            candidates.append(urljoin(PAGE, a["href"]))

    out = []
    for pdf in candidates[:3]:
        data = c.fetch_pdf(pdf, s=s)
        if not data:
            out.append(c.listing(NAME, c.slug_to_text(pdf), PAGE, pdf_url=pdf))
            continue
        items = c.parse_combined_pdf(data, NAME, PAGE)
        for it in items:
            it["pdf_url"] = pdf
        out.extend(items or [c.listing(NAME, c.slug_to_text(pdf), PAGE, pdf_url=pdf)])
    return out or [c.listing(NAME, "Продажба на имот — ProCredit", PAGE)]
