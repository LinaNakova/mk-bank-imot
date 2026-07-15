"""Central Cooperative Bank (ccbank) — publishes a single combined PDF report of
all real estate for sale. The URL is dated; refresh CCBANK_PDF when the bank
issues a new report (see README)."""
from .. import common as c

NAME = "ccbank"
SITE = "https://ccbank.mk/"
# Latest known combined report (dated in filename). Update when a new one is posted.
CCBANK_PDF = (
    "https://ccbank.mk/Upload/Dokumenti/130311%D0%BF%D0%B5%D1%82%D0%BE%D0%BA,12"
    "%D1%98%D0%B0%D0%BD%D1%83%D0%B0%D1%80%D0%B82024Copy%20of%20%D0%98%D0%B7%D0%B2"
    "%D0%B5%D1%88%D1%82%D0%B0%D1%98%20%D0%B7%D0%B0%20%D0%BD%D0%B5%D0%B4%D0%B2%D0"
    "%B8%D0%B6%D0%B5%D0%BD%20%D0%B8%D0%BC%D0%BE%D1%82%20%D0%BD%D0%B0%D0%BC%D0%B5"
    "%D0%BD%D0%B5%D1%82%20%D0%B7%D0%B0%20%D0%BF%D1%80%D0%BE%D0%B4%D0%B0%D0%B6%D0"
    "%B1%D0%B0%2031.12.2023.pdf"
)


def scrape(s):
    data = c.fetch_pdf(CCBANK_PDF, s=s)
    if not data:
        return [c.listing(NAME, "Извештај за недвижен имот за продажба — ccbank", CCBANK_PDF, pdf_url=CCBANK_PDF)]
    items = c.parse_combined_pdf(data, NAME, CCBANK_PDF)
    for it in items:
        it["pdf_url"] = CCBANK_PDF
    return items or [c.listing(NAME, "Извештај за недвижен имот за продажба — ccbank", CCBANK_PDF, pdf_url=CCBANK_PDF)]
