"""TTK Bank — page links to PDFs; keep only property-related ones and drop
generic site documents (recommendations, payment-account leaflets, etc.)."""
import re
from urllib.parse import urljoin, unquote

from bs4 import BeautifulSoup

from .. import common as c

NAME = "TTK"
PAGE = (
    "https://ttk.com.mk/Web/%D0%97%D0%90_%D0%91%D0%90%D0%9D%D0%9A%D0%90%D0%A2"
    "%D0%90/%D0%98%D0%BD%D0%B2%D0%B5%D1%81%D1%82%D0%B8%D1%82%D0%BE%D1%80%D0%B8"
    "/%D0%9F%D1%80%D0%BE%D0%B4%D0%B0%D0%B6%D0%B1%D0%B0_%D0%BD%D0%B0_%D0%BD%D0%B5"
    "%D0%B4%D0%B2%D0%B8%D0%B6%D0%B5%D0%BD_%D0%B8%D0%BC%D0%BE%D1%82_%D0%B8_%D0%BE"
    "%D0%BF%D1%80%D0%B5%D0%BC%D0%B0.aspx"
)
PROP = re.compile(r"(имот|недвиж|стан|куќа|кук[јj]а|деловен|земј|магацин|prodazba|nedviz)", re.I)
NOISE = re.compile(r"(препораки|preporaki|безбед|платежна сметка|тарифа|услови|opsti)", re.I)


def scrape(s, enrich=True, max_enrich=30):
    r = c.get(PAGE, s=s)
    if r is None:
        return [c.listing(NAME, "Продажба на недвижен имот — TTK", PAGE)]

    soup = BeautifulSoup(r.text, "html.parser")
    seen, out = set(), []
    for a in soup.find_all("a", href=re.compile(r"\.pdf", re.I)):
        href = a["href"]
        label = c.norm_ws(a.get_text(" ", strip=True))
        hay = unquote(href) + " " + label
        if NOISE.search(hay) or not PROP.search(hay):
            continue
        pdf = urljoin(PAGE, href)
        if pdf in seen:
            continue
        seen.add(pdf)
        title = label if len(label) > 4 else c.slug_to_text(pdf)
        out.append(
            c.listing(
                NAME, title, PAGE,
                prop_type=c.guess_type(hay),
                location=c.guess_city(hay),
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
            item["location"] = item["location"] or c.guess_city(txt)
            item["type"] = item["type"] or c.guess_type(txt)
    if not out:
        return [c.listing(NAME, "Продажба на недвижен имот — TTK", PAGE)]
    return out
