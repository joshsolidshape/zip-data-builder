#!/usr/bin/env python3
"""
Fetch USPS ZIP_Locale_Detail.xls, keep lower-48 states,
aggregate → us-zips.json.gz   (≈110 KB, <0.2 s lookup in browser)

Dependencies installed in the workflow:
    pandas xlrd        ← xlrd handles legacy .xls files
"""

import gzip, io, json, pathlib, urllib.request

import pandas as pd


# Direct “Download” link on https://postalpro.usps.com/ZIP_Locale_Detail
SRC_URL = (
    "https://postalpro.usps.com/mnt/glusterfs/2025-06/ZIP_Locale_Detail.xls"
    # If USPS rolls the month folder, just update the path above.
)

SHEET   = "ZIP_DETAIL"
OUTFILE = pathlib.Path("us-zips.json.gz")

# States / territories *not* served (outside lower-48)
SKIP = {"AK", "HI", "PR", "GU", "VI", "AS", "MP", "UM", "FM", "MH", "PW"}


def title(s: str) -> str:
    """LA VERNE → La Verne ; HOBOKEN → Hoboken"""
    return s.title()


def main() -> None:
    print("⇣  Downloading XLS …")
    with urllib.request.urlopen(SRC_URL) as r:
        raw = r.read()

    print("⇡  Parsing sheet …")
    df = pd.read_excel(
        io.BytesIO(raw),
        sheet_name=SHEET,
        usecols=["DELIVERY ZIPCODE", "PHYSICAL CITY", "PHYSICAL STATE"],
        dtype=str,
        engine="xlrd",          # ← change for .xls
    )

    # normalise / filter
    df.columns = ["zip", "city", "state"]
    df = df[~df["state"].isin(SKIP)]

    df["zip"]   = df["zip"].str.zfill(5)
    df["city"]  = df["city"].map(title)
    df["state"] = df["state"].map(title)

    # aggregate → {zip: {state:"CA", cities:[...]}}
    data: dict[str, dict[str, object]] = {}
    for z, rows in df.groupby("zip"):
        data[z] = {
            "state":  rows["state"].iat[0],
            "cities": sorted(rows["city"].unique()),
        }

    OUTFILE.parent.mkdir(exist_ok=True, parents=True)
    with gzip.open(OUTFILE, "wt", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))

    print(f"✓ Wrote {len(data):,} ZIPs → {OUTFILE}")


if __name__ == "__main__":
    main()
