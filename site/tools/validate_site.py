"""Browser checks for the parameter search page.

Usage: validate_site.py [--base-url http://127.0.0.1:1111] [--out site/validation]
"""
import argparse
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

failures = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


def names(page):
    return page.locator("#params tr.p td.n").all_inner_texts()


def run(page, vehicle, version, q):
    page.select_option("#vehicle", vehicle)
    if version == "latest":
        version = page.eval_on_selector("#version", "e => e.options[0].value")
    page.select_option("#version", version)
    page.wait_for_selector(f'#params[data-loaded="{vehicle}-{version}"]')
    page.fill("#q", q)
    return version


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:1111")
    ap.add_argument("--out", default=Path(__file__).resolve().parents[1] / "validation")
    a = ap.parse_args()
    base, out = a.base_url.rstrip("/"), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        page = p.chromium.launch(channel=os.environ.get("PW_CHANNEL")).new_page(viewport={"width": 1400, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("response", lambda r: errors.append(f"{r.status} {r.url}") if r.status >= 400 else None)
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(f"{base}/params/")

        run(page, "Copter", "latest", "ATC_RAT_RLL_P")
        check(names(page)[:1] == ["ATC_RAT_RLL_P"], "exact search ranks ATC_RAT_RLL_P first")
        for q in ("ATC_RTA_RLL", "atc rat rll"):
            page.fill("#q", q)
            check("ATC_RAT_RLL_P" in names(page)[:5], f"fuzzy search {q!r} ranks ATC_RAT_RLL_P in top 5")
        page.fill("#q", "roll rate")
        check(len(names(page)) > 0, "description search 'roll rate' returns rows")

        run(page, "Copter", "4.5", "ATC_RAT_RLL_P")
        count45 = page.inner_text("#count")
        latest = run(page, "Copter", "latest", "ATC_RAT_RLL_P")
        check(names(page)[:1] == ["ATC_RAT_RLL_P"], "version switch 4.5 -> latest keeps the row")
        data = page.request.get(f"{base}/data/Copter-{latest}.json").json()
        row = next(r for r in data if r["n"] == "ATC_RAT_RLL_P")
        shown = page.locator("#params tr.p").first.locator("td").all_inner_texts()
        check(shown[2] == " to ".join(row["r"]) and shown[3] == row.get("u", ""), "range and units match the loaded JSON")
        check(page.inner_text("#count").endswith("parameters") and page.inner_text("#count") != count45, "result count re-renders")

        run(page, "Plane", "latest", "ATC_")
        check("ATC_RAT_RLL_P" not in names(page), "Plane excludes Copter-only ATC_RAT_RLL_P")
        page.fill("#q", "TRIM")
        check("TRIM_THROTTLE" in names(page), "Plane includes TRIM_THROTTLE")
        run(page, "Rover", "latest", "CRUISE_SPEED")
        check(names(page)[:1] == ["CRUISE_SPEED"], "Rover finds CRUISE_SPEED")
        run(page, "Sub", "latest", "JS_GAIN_DEFAULT")
        check(names(page)[:1] == ["JS_GAIN_DEFAULT"], "Sub finds JS_GAIN_DEFAULT")

        run(page, "Copter", "latest", "")
        page.click('#chips button[data-g="EK3"]')
        n = names(page)
        check(n and all(x.startswith("EK3_") for x in n), "EK3 chip filters to EK3_ names")

        page.goto(f"{base}/params/#v=Plane&r=latest&q=TRIM")
        page.reload()  # a hash-only goto does not reload the page
        page.wait_for_selector('#params[data-loaded^="Plane-"]')
        check(page.input_value("#vehicle") == "Plane" and page.eval_on_selector("#version", "e => e.selectedIndex") == 0
              and page.input_value("#q") == "TRIM" and "TRIM_THROTTLE" in names(page), "hash restores vehicle, version and query")

        page.screenshot(path=out / "default.png", full_page=True)
        page.click("#mode")
        page.screenshot(path=out / "toggled.png", full_page=True)
        check(not errors, f"no console errors: {errors}")
    print(f"{len(failures)} failures")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
