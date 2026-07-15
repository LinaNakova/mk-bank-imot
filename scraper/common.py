"""Shared helpers for all bank adapters.

Every adapter returns a list of dict listings using `listing(...)`. The goal is
resilience: an adapter should never raise out; where structured parsing fails it
still returns at least a link back to the bank so no source silently disappears.
"""
from __future__ import annotations

import io
import re
import time
import hashlib
from urllib.parse import urljoin, unquote

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "mk-MK,mk;q=0.9,en;q=0.8",
}


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def get(url: str, s: requests.Session | None = None, timeout: int = 45, tries: int = 2):
    """GET with retries. Returns response or None (never raises)."""
    s = s or session()
    for attempt in range(tries):
        try:
            r = s.get(url, timeout=timeout)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(1.2)
    return None


# ---------------------------------------------------------------- parsing utils

_AREA_RE = re.compile(r"(\d[\d.\s]*(?:[.,]\d+)?)\s*(?:m2|м2|m²|м²|кв\.?\s*м)", re.I)
_PRICE_RE = re.compile(
    r"(\d[\d.\s]*(?:[.,]\d+)?)\s*(?:€|eur|евра|евро|мкд|денари|den)\b", re.I
)
_DEED_RE = re.compile(r"имотен\s+лист\s*(?:бр\.?|број)?\s*([\d/\-]+)", re.I)

# property type keywords -> normalized label (Macedonian)
_TYPES = [
    (r"деловно[\-\s]?станбен|станбено[\-\s]?делов", "Деловно-станбен"),
    (r"стан\b", "Стан"),
    (r"куќа|кукја|кук[јj]а|семејна", "Куќа"),
    (r"ресторан|угостит", "Угостителски објект"),
    (r"деловен|локал|канцелар|објект", "Деловен простор"),
    (r"магацин|склад", "Магацин"),
    (r"земј|нива|парцела|плац", "Земјиште"),
    (r"хотел|мотел", "Хотел"),
    (r"гараж", "Гаража"),
    (r"викенд", "Викендица"),
]

# NBRM-mandated report templates ("Образец ИП") are posted alongside real
# listings but are not properties themselves — drop them.
NOISE_TITLE = re.compile(r"(образец\s*ип|obrazec|општи услови|opsti uslovi|информација согласно)", re.I)


def is_noise(title: str) -> bool:
    return bool(NOISE_TITLE.search(title or ""))


def norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def guess_type(text: str) -> str | None:
    t = (text or "").lower()
    for pat, label in _TYPES:
        if re.search(pat, t):
            return label
    return None


def find_area(text: str) -> float | None:
    m = _AREA_RE.search(text or "")
    if not m:
        return None
    raw = m.group(1).replace(" ", "").replace(".", "").replace(",", ".")
    try:
        val = round(float(raw), 1)
        return val if 0 < val <= 500000 else None  # reject mis-parsed giant numbers
    except ValueError:
        return None


def find_price(text: str):
    m = _PRICE_RE.search(text or "")
    if not m:
        return None, None
    raw = m.group(1).replace(" ", "").replace(".", "").replace(",", ".")
    unit = m.group(0)[len(m.group(1)):].strip().lower()
    cur = "EUR" if any(x in unit for x in ("€", "eur", "евр")) else "MKD"
    try:
        return round(float(raw)), cur
    except ValueError:
        return None, None


def find_deed(text: str) -> str | None:
    m = _DEED_RE.search(text or "")
    return m.group(1) if m else None


# Macedonian city list for coarse location extraction from free text / filenames
CITIES = [
    "Скопје", "Битола", "Куманово", "Прилеп", "Тетово", "Велес", "Штип", "Охрид",
    "Гостивар", "Струмица", "Кавадарци", "Кочани", "Кичево", "Струга", "Радовиш",
    "Гевгелија", "Дебар", "Крива Паланка", "Свети Николе", "Неготино", "Виница",
    "Делчево", "Демир Хисар", "Валандово", "Богданци", "Берово", "Пробиштип",
    "Ресен", "Крушево", "Македонски Брод", "Кратово", "Дојран", "Пехчево",
    "Македонска Каменица", "Демир Капија", "Гази Баба", "Аеродром", "Карпош",
    "Центар", "Чаир", "Кисела Вода", "Ѓорче Петров", "Бутел", "Сарај", "Илинден",
    "Петровец", "Негорци", "Star Dojran", "Struga", "Skopje",
]


# Latin transliteration -> Cyrillic display, for filenames like Stan_vo_Strumica.pdf
LATIN_CITIES = {
    "skopje": "Скопје", "bitola": "Битола", "kumanovo": "Куманово",
    "prilep": "Прилеп", "tetovo": "Тетово", "veles": "Велес", "stip": "Штип",
    "ohrid": "Охрид", "gostivar": "Гостивар", "strumica": "Струмица",
    "kavadarci": "Кавадарци", "kocani": "Кочани", "kicevo": "Кичево",
    "struga": "Струга", "radovis": "Радовиш", "gevgelija": "Гевгелија",
    "debar": "Дебар", "negotino": "Неготино", "vinica": "Виница",
    "delcevo": "Делчево", "valandovo": "Валандово", "bogdanci": "Богданци",
    "berovo": "Берово", "probistip": "Пробиштип", "resen": "Ресен",
    "krusevo": "Крушево", "kratovo": "Кратово", "dojran": "Дојран",
    "pehcevo": "Пехчево", "negorci": "Негорци", "oktisi": "Октиси",
}


def guess_city(text: str) -> str | None:
    t = (text or "").lower()
    for c in sorted(CITIES, key=len, reverse=True):
        if c.lower() in t:
            return c
    for latin, cyr in sorted(LATIN_CITIES.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"\b{latin}\b", t):
            return cyr
    return None


def slug_to_text(url: str) -> str:
    """Turn a pdf filename/slug into readable words for fallback titles."""
    name = unquote(url.rstrip("/").split("/")[-1])
    name = re.sub(r"\.(pdf|aspx|nspx|html?)$", "", name, flags=re.I)
    name = re.sub(r"[_\-]+", " ", name)
    return norm_ws(name)


def make_id(bank: str, ref: str) -> str:
    return hashlib.sha1(f"{bank}||{ref}".encode("utf-8")).hexdigest()[:16]


def listing(
    bank: str,
    title: str,
    source_url: str,
    *,
    prop_type: str | None = None,
    location: str | None = None,
    area_m2: float | None = None,
    price: int | None = None,
    currency: str | None = None,
    deed: str | None = None,
    description: str | None = None,
    pdf_url: str | None = None,
) -> dict:
    ref = pdf_url or f"{source_url}::{title}"
    return {
        "id": make_id(bank, ref),
        "bank": bank,
        "title": norm_ws(title) or "Недвижен имот",
        "type": prop_type,
        "location": location,
        "area_m2": area_m2,
        "price": price,
        "currency": currency,
        "deed": deed,
        "description": norm_ws(description)[:600] if description else None,
        "source_url": source_url,
        "pdf_url": pdf_url,
    }


# ---------------------------------------------------------------- PDF helpers

def pdf_text(data: bytes) -> str:
    """Extract text from PDF bytes tolerantly (pdfplumber, fall back to pypdf)."""
    text = ""
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception:
        pass
    if len(text.strip()) < 20:
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data), strict=False)
            text = "\n".join((pg.extract_text() or "") for pg in reader.pages)
        except Exception:
            pass
    return text


def pdf_tables(data: bytes):
    try:
        import pdfplumber

        rows = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for p in pdf.pages:
                for tbl in p.extract_tables() or []:
                    rows.extend(tbl)
        return rows
    except Exception:
        return []


def parse_combined_pdf(data: bytes, bank: str, source_url: str) -> list[dict]:
    """Best-effort: turn a one-big-table PDF into individual listings.

    Column layout differs per bank, so we work row-by-row on the joined text and
    pull fields by pattern. A row counts as a property if it names an area, a
    type keyword, or a known city and isn't a header/total line.
    """
    out = []
    tables = pdf_tables(data)
    rows = ["  ".join((cell or "") for cell in r) for r in tables]
    if not rows:  # no table grid detected — fall back to text lines
        rows = [ln for ln in pdf_text(data).splitlines() if len(ln.strip()) > 8]

    for row in rows:
        row = norm_ws(row)
        low = row.lower()
        if not row or any(h in low for h in ("реден", "р.бр", "опис", "вкупно", "total", "локација локација")):
            continue
        area = find_area(row)
        ptype = guess_type(row)
        city = guess_city(row)
        if not (area or ptype or city):
            continue
        price, cur = find_price(row)
        title = row[:120]
        out.append(
            listing(
                bank, title, source_url,
                prop_type=ptype, location=city, area_m2=area,
                price=price, currency=cur, deed=find_deed(row),
            )
        )
    return out


def fetch_pdf(url: str, s: requests.Session | None = None) -> bytes | None:
    r = get(url, s=s, timeout=60)
    if r is None:
        return None
    if b"%PDF" not in r.content[:1024]:
        return None
    return r.content
