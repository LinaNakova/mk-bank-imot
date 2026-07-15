"""Halkbank — property data lives in an HTML table (num | description | location | PDF link)."""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .. import common as c

NAME = "Halkbank"
PAGE = "https://www.halkbank.mk/prodazba-na-imot-na-halkbank.nspx"


def scrape(s):
    r = c.get(PAGE, s=s)
    if r is None:
        return [c.listing(NAME, "Продажба на имот — Halkbank", PAGE)]

    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for tr in soup.select("table tr"):
        tds = tr.find_all(["td", "th"])
        if len(tds) < 3:
            continue
        desc = c.norm_ws(tds[1].get_text(" ", strip=True))
        loc = c.norm_ws(tds[2].get_text(" ", strip=True))
        if not desc or desc.lower().startswith("опис"):
            continue  # header row
        a = tr.find("a", href=re.compile(r"\.pdf", re.I))
        pdf = urljoin(PAGE, a["href"]) if a else None
        out.append(
            c.listing(
                NAME,
                desc,
                PAGE,
                prop_type=c.guess_type(desc),
                location=loc or c.guess_city(desc),
                pdf_url=pdf,
            )
        )
    return out or [c.listing(NAME, "Продажба на имот — Halkbank", PAGE)]
