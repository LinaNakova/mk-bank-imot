# Банкарски имот · продажба

A single place that lists **all real estate the banks in North Macedonia have for sale**
(foreclosed / bank-owned property). It aggregates listings from ~11 banks into one
searchable, installable web app that **refreshes automatically every Monday**.

- **Frontend:** a static Progressive Web App (`site/`) — plain HTML/CSS/JS, no build step.
- **Backend:** a Python scraper (`scraper/`) that visits each bank, parses its page/PDFs,
  and writes `site/data/listings.json`.
- **Automation:** a GitHub Actions workflow runs the scraper every Monday, commits the
  refreshed data, and redeploys the site — all free.

Sources are the banks linked from the National Bank list:
<https://www.nbrm.mk/imot-na-bankite-i-stedilnicite-namenet-za-prodazba.nspx>

---

## 1. Deploy (one-time, ~5 minutes)

1. **Create a GitHub repo** and push this folder to it (branch `main`):
   ```bash
   git init
   git add .
   git commit -m "Банкарски имот: initial"
   git branch -M main
   git remote add origin https://github.com/<you>/<repo>.git
   git push -u origin main
   ```

2. **Enable GitHub Pages via Actions:**
   Repo → **Settings → Pages → Build and deployment → Source = "GitHub Actions"**.

3. **Enable Actions** (if prompted): Repo → **Actions** tab → enable workflows.
   The included workflow already asks for the permissions it needs
   (`contents: write`, `pages: write`, `id-token: write`).

4. **Run it once now:** Actions → **"Weekly update & deploy"** → **Run workflow**.
   When it finishes, your app is live at:
   ```
   https://<you>.github.io/<repo>/
   ```

That first run also installs a headless browser in CI, which fills in the few banks
that block plain scraping (see notes below).

---

## 2. Put it on your iPhone

1. Open the live URL above in **Safari** (must be Safari, not Chrome, for install).
2. Tap the **Share** button (the square with the up-arrow).
3. Tap **Add to Home Screen** → **Add**.

It now behaves like an app: full-screen, its own icon, and it opens the last data
even offline. Each time you open it while online it pulls the latest Monday refresh.

---

## 3. How the weekly update works

`.github/workflows/update.yml` runs on `cron: "0 6 * * 1"` — every **Monday 06:00 UTC**
(around 07:00–08:00 in Skopje). It:

1. installs dependencies + Playwright Chromium,
2. runs `python -m scraper.main`,
3. commits `site/data/listings.json` only if it changed,
4. redeploys the site.

You can also trigger it any time from **Actions → Run workflow**. Listings that a bank
removes simply drop off; new ones get a **НОВО** stamp for 7 days.

---

## 4. The banks & scraping strategy

Each bank publishes differently, so each has its own adapter in `scraper/banks/`:

| Bank | How it's read |
|---|---|
| Halkbank | HTML table |
| Unibank | HTML labelled blocks |
| Sparkasse | HTML → one PDF per property |
| SRB (Silk Road) | HTML → per-property PDFs |
| TTK | HTML → PDFs (filtered) |
| ccbank | one combined PDF report |
| ProCredit (PCB) | combined PDF |
| STB (Stopanska) | JavaScript page → headless browser |
| KB (Komercijalna) | anti-bot → headless browser |
| Alta | anti-bot → headless browser + combined PDF |

**Link-only fallback:** if a bank can't be parsed on a given run, its entry still
appears as a single card linking to the bank's official page, so nothing is ever
silently lost. The headless-browser banks (STB, KB, Alta) and ProCredit only fully
populate in **GitHub Actions**, where Chromium is installed — a plain local machine
without Playwright will show them as link-only.

---

## 5. Maintenance

- **ccbank & Alta post dated PDFs.** When a bank replaces its report with a newer dated
  file, update the URL constant:
  - `scraper/banks/ccbank.py` → `CCBANK_PDF`
  - `scraper/banks/altabanka.py` will try to auto-discover the PDF in the page; if it
    changes structure, check `PAGE` there.
  Find the new link on the National Bank page above or the bank's "Продажба на имот" page.

- **Add another bank:** create `scraper/banks/<name>.py` exposing `NAME` and
  `fetch(session) -> list`, using the helpers in `scraper/common.py`
  (`get`, `pdf_text`, `parse_combined_pdf`, `listing`, `guess_type`, `guess_city`, …),
  then register it in `scraper/banks/__init__.py`'s `ADAPTERS` list.

- **Switch UI to English:** the interface text lives in `site/index.html` and
  `site/app.js`. The data itself is Cyrillic (as published by the banks).

---

## 6. Run the scraper locally (optional)

```bash
pip install -r requirements.txt
python -m playwright install chromium   # for STB/KB/Alta
python -m scraper.main                   # writes site/data/listings.json

# preview the site
cd site && python -m http.server 8000    # then open http://localhost:8000
```

---

*Note on prices:* many bank foreclosure listings are sold by auction/offer and have no
fixed price, so cards may correctly show **„по договор"** (by agreement).
