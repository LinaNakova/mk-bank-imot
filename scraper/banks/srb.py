"""SRB (Silk Road Bank) — 'Повеќе' links to per-property PDFs; the readable info is
in the filename, e.g. Stan_vo_Strumica_1.pdf, Semejna_kukja_vo_Kavadarci.pdf."""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .. import common as c

NAME = "SRB"
PAGE = "https://www.srb.mk/ProdazbaImot?Cat=ProdazbaImot"
_NOISE = re.compile(r"^(ip\d+|obrazec|informacija|opsti|uslovi)", re.I)


def scrape(s, enrich=True, max_enrich=30):
    r = c.get(PAGE, s=s)
    if r is None:
        return [c.listing(NAME, "Продажба на имот — SRB", PAGE)]

    soup = BeautifulSoup(r.text, "html.parser")
    seen, out = set(), []
    for a in soup.find_all("a", href=re.compile(r"prodazba/.+\.pdf", re.I)):
        pdf = urljoin(PAGE, a["href"])
        fname = pdf.split("/")[-1]
        if pdf in seen or _NOISE.search(fname):
            continue
        seen.add(pdf)
        title = c.slug_to_text(pdf)
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
            item["type"] = item["type"] or c.guess_type(txt)
    return out or [c.listing(NAME, "Продажба на имот — SRB", PAGE)]
