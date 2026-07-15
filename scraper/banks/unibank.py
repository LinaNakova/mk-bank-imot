"""Unibank — properties are HTML blocks with labeled fields:
'Опис на недвижниот имот:', 'Адреса:', 'Број на Имотен лист:', 'Квадратура...'."""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .. import common as c

NAME = "Unibank"
PAGE = "https://www.unibank.mk/nedvizen-imot.nspx"

FIELD = lambda label, text: (
    m.group(1).strip()
    if (m := re.search(label + r"\s*[:：]?\s*(.+?)(?=(?:Опис|Адреса|Број|Квадратура|Заложно|Напомена|Цена|$))", text, re.I | re.S))
    else None
)


def scrape(s):
    r = c.get(PAGE, s=s)
    if r is None:
        return [c.listing(NAME, "Недвижен имот — Unibank", PAGE)]

    soup = BeautifulSoup(r.text, "html.parser")
    blocks, seen = [], set()
    for li in soup.find_all(["li", "p", "div"]):
        if "Опис на недвижниот имот" in li.get_text():
            blk = li.find_parent(["div", "article", "section"]) or li
            blocks.append(blk)

    out = []
    for blk in blocks:
        text = c.norm_ws(blk.get_text(" ", strip=True))
        if text in seen:
            continue
        seen.add(text)
        desc = FIELD("Опис на недвижниот имот", text)
        addr = FIELD("Адреса", text)
        deed = FIELD("Број на Имотен лист", text)
        area_field = FIELD("Квадратура на недвижниот имот", text) or text
        if not desc:
            continue
        a = blk.find("a", href=re.compile(r"\.pdf", re.I))
        pdf = urljoin(PAGE, a["href"]) if a else None
        out.append(
            c.listing(
                NAME,
                desc,
                PAGE,
                prop_type=c.guess_type(desc),
                location=addr or c.guess_city(desc),
                area_m2=c.find_area(area_field),
                deed=deed,
                pdf_url=pdf,
            )
        )
    return out or [c.listing(NAME, "Недвижен имот — Unibank", PAGE)]
