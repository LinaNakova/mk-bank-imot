"""Sparkasse — HTML page links to one PDF per property; anchor text is descriptive,
e.g. 'Продажба на деловен простор во Гази Баба Скопје (PDF, 261 KB)'."""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .. import common as c

NAME = "Sparkasse"
PAGE = "https://www.sparkasse.mk/mk/za-nas/prodazba-na-imot"
# property PDFs live under this CDN path; skip other site PDFs
PROP_HINT = re.compile(r"prodazba-na-imot", re.I)


def scrape(s, enrich=True, max_enrich=60):
    r = c.get(PAGE, s=s)
    if r is None:
        return [c.listing(NAME, "Продажба на имот — Sparkasse", PAGE)]

    soup = BeautifulSoup(r.text, "html.parser")
    seen, out = set(), []
    for a in soup.find_all("a", href=re.compile(r"\.pdf", re.I)):
        href = a["href"]
        if not PROP_HINT.search(href):
            continue
        pdf = urljoin(PAGE, href)
        if pdf in seen:
            continue
        seen.add(pdf)
        text = c.norm_ws(a.get_text(" ", strip=True))
        title = re.sub(r"\s*\(PDF.*$", "", text, flags=re.I) or c.slug_to_text(pdf)
        out.append(
            c.listing(
                NAME,
                title,
                PAGE,
                prop_type=c.guess_type(title),
                location=c.guess_city(title),
                pdf_url=pdf,
            )
        )

    if enrich:
        for item in out[:max_enrich]:
            data = c.fetch_pdf(item["pdf_url"], s=s)
            if not data:
                continue
            txt = c.pdf_text(data)
            item["area_m2"] = item["area_m2"] or c.find_area(txt)
            if not item["price"]:
                item["price"], item["currency"] = c.find_price(txt)
            item["deed"] = item["deed"] or c.find_deed(txt)
            item["location"] = item["location"] or c.guess_city(txt)
            if not item["description"]:
                m = re.search(r"Опис[:\s]+(.{20,400})", txt)
                if m:
                    item["description"] = c.norm_ws(m.group(1))[:600]
    return out or [c.listing(NAME, "Продажба на имот — Sparkasse", PAGE)]
