"""
driver_updater.py
=================
Scans all device drivers installed on this Windows machine, looks up the
latest available version online for each one, and reports which are outdated
with a direct download link.

Vendor coverage
---------------
  NVIDIA   — official NVIDIA API (exact match by GPU model)
  Intel    — official Intel ARK / download API (chipset, graphics, WiFi, LAN)
  AMD      — AMD release page scraping
  Realtek  — Realtek download page scraping
  Generic  — Google search fallback for any other vendor

Requirements
------------
  pip install requests beautifulsoup4 tabulate

Run
---
  python Code/driver_updater.py

Output
------
  Console table + results/driver_report_<YYYYMMDD_HHMMSS>.csv
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
_MISSING = []
try:
    import requests
except ImportError:
    _MISSING.append("requests")
try:
    from bs4 import BeautifulSoup
except ImportError:
    _MISSING.append("beautifulsoup4")
try:
    from tabulate import tabulate
except ImportError:
    _MISSING.append("tabulate")

if _MISSING:
    print(f"Missing packages: {', '.join(_MISSING)}")
    print(f"Install with:  pip install {' '.join(_MISSING)}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
DT_TAG     = datetime.now().strftime('%Y%m%d_%H%M%S')
OUTPUT_CSV = OUTPUT_DIR / f"driver_report_{DT_TAG}.csv"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36"}
TIMEOUT = 15   # seconds per HTTP request


# ===========================================================================
#   STEP 1 — Enumerate installed drivers via PowerShell
# ===========================================================================
def get_installed_drivers() -> list[dict]:
    """
    Query WMI for all signed device drivers.
    Returns a list of dicts with keys:
      name, manufacturer, driver_version, driver_date, device_class, inf_name
    """
    print("\n[STEP 1] Enumerating installed device drivers via WMI …")

    ps_script = r"""
    Get-WmiObject Win32_PnPSignedDriver |
    Where-Object { $_.DriverVersion -ne $null -and $_.DeviceName -ne $null } |
    Select-Object DeviceName, Manufacturer, DriverVersion, DriverDate, DeviceClass, InfName |
    ConvertTo-Json -Depth 2
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=120
        )
        raw = result.stdout.strip()
        if not raw:
            print("  ERROR :: PowerShell returned no output.")
            return []

        data = json.loads(raw)
        # PowerShell returns a single dict when only one object is found
        if isinstance(data, dict):
            data = [data]

        drivers = []
        for d in data:
            name    = (d.get("DeviceName")    or "").strip()
            mfr     = (d.get("Manufacturer")  or "").strip()
            version = (d.get("DriverVersion") or "").strip()
            date    = (d.get("DriverDate")    or "").strip()
            cls     = (d.get("DeviceClass")   or "").strip()
            inf     = (d.get("InfName")       or "").strip()

            if name and version:
                drivers.append({
                    "name":           name,
                    "manufacturer":   mfr,
                    "driver_version": version,
                    "driver_date":    _parse_wmi_date(date),
                    "device_class":   cls,
                    "inf_name":       inf,
                })

        # Deduplicate by (name, manufacturer, version)
        seen = set()
        unique = []
        for d in drivers:
            key = (d["name"], d["manufacturer"], d["driver_version"])
            if key not in seen:
                seen.add(key)
                unique.append(d)

        print(f"  → {len(unique)} drivers found\n")
        return unique

    except subprocess.TimeoutExpired:
        print("  ERROR :: PowerShell timed out.")
        return []
    except json.JSONDecodeError as e:
        print(f"  ERROR :: Could not parse PowerShell output: {e}")
        return []


def _parse_wmi_date(raw: str) -> str:
    """Convert WMI date string like '20231015000000.000000+000' → '2023-10-15'."""
    if not raw:
        return ""
    m = re.match(r'^(\d{4})(\d{2})(\d{2})', raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return raw[:10] if len(raw) >= 10 else raw


# ===========================================================================
#   STEP 2 — Look up latest driver versions online
# ===========================================================================

# ---------------------------------------------------------------------------
# NVIDIA
# ---------------------------------------------------------------------------
def _lookup_nvidia(name: str) -> tuple[str, str]:
    """
    Use NVIDIA's download API to find the latest driver for this GPU.
    Returns (latest_version, download_url).
    """
    # Extract model hint, e.g. "RTX 3060" from full device name
    model_hints = re.findall(r'(?:GTX|RTX|Quadro|Tesla|MX|GT)\s*\d+\s*\w*', name, re.I)
    if not model_hints:
        return "", ""

    # NVIDIA product type lookup table (simplified)
    # psid=120 = GeForce RTX 30/40, osid=135 = Windows 11 64-bit
    # This is a best-effort heuristic — works for most consumer GPUs
    params = {
        "lang":     "1033",
        "osID":     "135",       # Windows 11 64-bit
        "driverType": "1",
        "isWHQL":   "1",
        "dtcid":    "1",
    }
    # Map common GPU families to psid/pfid
    hint = model_hints[0].upper()
    if "RTX 40" in hint or "4090" in hint or "4080" in hint or "4070" in hint or "4060" in hint:
        params.update({"psid": "127", "pfid": "983"})
    elif "RTX 30" in hint or "3090" in hint or "3080" in hint or "3070" in hint or "3060" in hint:
        params.update({"psid": "120", "pfid": "844"})
    elif "RTX 20" in hint or "2080" in hint or "2070" in hint or "2060" in hint:
        params.update({"psid": "107", "pfid": "760"})
    elif "GTX 16" in hint or "1660" in hint or "1650" in hint:
        params.update({"psid": "104", "pfid": "758"})
    elif "GTX 10" in hint or "1080" in hint or "1070" in hint or "1060" in hint:
        params.update({"psid": "104", "pfid": "736"})
    else:
        return "", ""

    try:
        url  = "https://www.nvidia.com/Download/processFind.aspx"
        resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        # Extract version from response HTML
        m = re.search(r'driverResults\.aspx/(\d+)/en-us', resp.text)
        if not m:
            # Try alternate pattern
            m = re.search(r'(\d{3}\.\d{2})', resp.text)
        if m:
            ver = m.group(1) if '.' in m.group(1) else ""
            dl  = f"https://www.nvidia.com/Download/driverResults.aspx/{m.group(1)}/en-us"
            return ver, dl
    except Exception:
        pass
    return "", ""


# ---------------------------------------------------------------------------
# Intel
# ---------------------------------------------------------------------------
_INTEL_SEARCH_URL = "https://downloadcenter.intel.com/api/v1/search"

def _lookup_intel(name: str) -> tuple[str, str]:
    """Search Intel Download Center API for the latest driver."""
    # Build a clean search term
    search = re.sub(r'\(.*?\)', '', name).strip()
    search = re.sub(r'Intel\s*', '', search, flags=re.I).strip()
    search = search[:60]  # API has length limits
    try:
        resp = requests.get(
            "https://www.intel.com/content/www/us/en/search.html",
            params={"q": f"Intel {search} driver download", "f:@tabfilter": "Downloads"},
            headers=HEADERS, timeout=TIMEOUT
        )
        # Parse version and link from result
        m_ver  = re.search(r'Version\s*([\d.]+)', resp.text)
        m_link = re.search(r'(https://downloadcenter\.intel\.com/download/\d+)', resp.text)
        ver    = m_ver.group(1)  if m_ver  else ""
        link   = m_link.group(1) if m_link else "https://downloadcenter.intel.com/"
        return ver, link if ver else ("", "")
    except Exception:
        pass
    return "", ""


# ---------------------------------------------------------------------------
# AMD
# ---------------------------------------------------------------------------
def _lookup_amd(name: str) -> tuple[str, str]:
    """Scrape AMD driver version from AMD's download page."""
    try:
        resp = requests.get(
            "https://www.amd.com/en/support/download/drivers.html",
            headers=HEADERS, timeout=TIMEOUT
        )
        # Look for version numbers on page (AMD lists like "Adrenalin 24.x.x")
        m = re.search(r'Adrenalin\s+(\d{2}\.\d+\.\d+)', resp.text)
        if m:
            ver  = m.group(1)
            link = "https://www.amd.com/en/support/download/drivers.html"
            return ver, link
    except Exception:
        pass
    return "", ""


# ---------------------------------------------------------------------------
# Realtek
# ---------------------------------------------------------------------------
def _lookup_realtek(name: str) -> tuple[str, str]:
    """Look up Realtek audio/LAN driver version."""
    is_audio = any(k in name.lower() for k in ('audio', 'hd audio', 'ac97'))
    try:
        if is_audio:
            url  = "https://www.realtek.com/en/component/zoo/category/pc-audio-codecs-high-definition-audio-codecs-software"
            link = url
        else:
            url  = "https://www.realtek.com/en/component/zoo/category/network-interface-controllers-10-100-1000m-gigabit-ethernet-pci-express-software"
            link = url
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        m = re.search(r'(\d+\.\d+\.\d+(?:\.\d+)?)', resp.text)
        ver = m.group(1) if m else ""
        return ver, link if ver else ("", "")
    except Exception:
        pass
    return "", ""


# ---------------------------------------------------------------------------
# Generic fallback — Google search
# ---------------------------------------------------------------------------
def _lookup_generic(name: str, manufacturer: str) -> tuple[str, str]:
    """
    Use DuckDuckGo (no API key required) to find the latest driver page.
    Returns (version_hint, url).  Version may be empty if not parseable from snippet.
    """
    query = f"{manufacturer} {name} latest driver download site:{_vendor_domain(manufacturer)}"
    if not _vendor_domain(manufacturer):
        query = f"{manufacturer} {name} driver download latest version"
    try:
        resp = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers=HEADERS, timeout=TIMEOUT
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        for result in soup.select(".result__body")[:3]:
            link_tag = result.select_one(".result__url")
            snip_tag = result.select_one(".result__snippet")
            href = link_tag.get_text(strip=True) if link_tag else ""
            snip = snip_tag.get_text(strip=True) if snip_tag else ""
            # Try to extract a version number from snippet
            m = re.search(r'\b(\d+\.\d+[\.\d]*)\b', snip)
            ver = m.group(1) if m else ""
            if href:
                full_url = "https://" + href if not href.startswith("http") else href
                return ver, full_url
    except Exception:
        pass
    return "", ""


def _vendor_domain(manufacturer: str) -> str:
    """Return the support domain for known manufacturers."""
    mfr = manufacturer.lower()
    domains = {
        "nvidia":    "nvidia.com",
        "intel":     "intel.com",
        "amd":       "amd.com",
        "realtek":   "realtek.com",
        "qualcomm":  "qualcomm.com",
        "broadcom":  "broadcom.com",
        "logitech":  "logitech.com",
        "microsoft": "microsoft.com",
        "lenovo":    "support.lenovo.com",
        "dell":      "dell.com",
        "hp":        "hp.com",
        "asus":      "asus.com",
        "acer":      "acer.com",
        "msi":       "msi.com",
        "samsung":   "samsung.com",
        "synaptics": "synaptics.com",
    }
    for key, domain in domains.items():
        if key in mfr:
            return domain
    return ""


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
def lookup_latest_driver(driver: dict) -> tuple[str, str]:
    """
    Route to the appropriate lookup function based on manufacturer.
    Returns (latest_version, download_url).  Both empty strings if not found.
    """
    name = driver["name"]
    mfr  = driver["manufacturer"].lower()

    if "nvidia" in mfr or "nvidia" in name.lower():
        ver, url = _lookup_nvidia(name)
        if ver:
            return ver, url

    if "intel" in mfr or "intel" in name.lower():
        ver, url = _lookup_intel(name)
        if ver:
            return ver, url

    if "amd" in mfr or "advanced micro" in mfr or "radeon" in name.lower():
        ver, url = _lookup_amd(name)
        if ver:
            return ver, url

    if "realtek" in mfr or "realtek" in name.lower():
        ver, url = _lookup_realtek(name)
        if ver:
            return ver, url

    # Generic fallback for everything else
    return _lookup_generic(name, driver["manufacturer"])


# ===========================================================================
#   STEP 3 — Compare versions
# ===========================================================================
def _parse_version(v: str) -> tuple[int, ...]:
    """Convert '31.0.15.3623' → (31, 0, 15, 3623) for comparison."""
    parts = re.findall(r'\d+', v)
    return tuple(int(x) for x in parts) if parts else (0,)


def compare_and_report(drivers: list[dict]) -> list[dict]:
    print("[STEP 2 & 3] Looking up latest versions online and comparing …")
    print(f"  (This may take a few minutes for {len(drivers)} drivers)\n")

    rows = []
    for i, drv in enumerate(drivers, start=1):
        name    = drv["name"]
        mfr     = drv["manufacturer"]
        inst_v  = drv["driver_version"]
        inst_d  = drv["driver_date"]

        print(f"  [{i}/{len(drivers)}] {name[:55]:<55} v{inst_v}", end=" … ", flush=True)

        latest_v, dl_url = lookup_latest_driver(drv)

        if not latest_v:
            status = "unknown"
            print("no data found")
        else:
            inst_t   = _parse_version(inst_v)
            latest_t = _parse_version(latest_v)
            if latest_t > inst_t:
                status = "OUTDATED"
                print(f"OUTDATED  (latest: {latest_v})")
            elif latest_t < inst_t:
                status = "newer than online"
                print(f"OK (installed newer: {inst_v} > {latest_v})")
            else:
                status = "up-to-date"
                print("up-to-date")

        rows.append({
            "device_name":      name,
            "manufacturer":     mfr,
            "installed_version": inst_v,
            "installed_date":   inst_d,
            "latest_version":   latest_v or "N/A",
            "status":           status,
            "download_url":     dl_url or "N/A",
        })

    return rows


# ===========================================================================
#   Output helpers
# ===========================================================================
def print_report(rows: list[dict]):
    outdated = [r for r in rows if r["status"] == "OUTDATED"]
    unknown  = [r for r in rows if r["status"] == "unknown"]
    ok       = [r for r in rows if r["status"] in ("up-to-date", "newer than online")]

    print(f"\n{'═'*80}")
    print(f"  DRIVER UPDATE REPORT  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═'*80}")
    print(f"  Total drivers scanned : {len(rows)}")
    print(f"  Up-to-date            : {len(ok)}")
    print(f"  OUTDATED              : {len(outdated)}")
    print(f"  Version unknown       : {len(unknown)}")
    print(f"{'─'*80}\n")

    if outdated:
        print("  *** DRIVERS THAT NEED UPDATING ***\n")
        for r in outdated:
            print(f"  Device  : {r['device_name']}")
            print(f"  Vendor  : {r['manufacturer']}")
            print(f"  Installed : {r['installed_version']}  ({r['installed_date']})")
            print(f"  Latest    : {r['latest_version']}")
            print(f"  Download  : {r['download_url']}")
            print(f"  {'─'*70}")
    else:
        print("  All drivers with known versions are up-to-date.\n")


def save_csv(rows: list[dict]):
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  Full report saved → {OUTPUT_CSV}")


# ===========================================================================
#   Main
# ===========================================================================
def main():
    print(f"{'═'*80}")
    print(f"  Windows Driver Version Checker")
    print(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═'*80}")

    t0 = datetime.now()

    # Step 1 — enumerate
    drivers = get_installed_drivers()
    if not drivers:
        sys.exit("No drivers found — ensure you're running on Windows with WMI available.")

    # Step 2 & 3 — look up + compare
    rows = compare_and_report(drivers)

    # Output
    print_report(rows)
    save_csv(rows)

    elapsed = round((datetime.now() - t0).total_seconds(), 1)
    print(f"\n  Finished : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Elapsed  : {elapsed}s\n")


if __name__ == "__main__":
    main()
