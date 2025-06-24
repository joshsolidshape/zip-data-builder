#!/usr/bin/env python3
"""
Fetch USPS ZIP_Locale_Detail.xlsx, keep lower-48 states,
aggregate → us-zips.json.gz   (≈ 110 KB, <0.2 s lookup in browser)

Dependencies: pandas, openpyxl   (installed in the workflow)
"""

import gzip, io, json, pathlib, tempfile, urllib.request, pandas as pd

# Direct URL behind the “Download” button on https://postalpro.usps.com/ZIP_Locale_Detail
SRC_URL = (
    "https://postalpro.usps.com/sites/default/files/ZIP_Locale_Detail.xlsx"
)

SHEET   = "ZIP_DETAIL"
OUTFILE = pathlib.Path("us-zips.json.gz")
SKIP    = {"AK","HI","PR","GU","VI","AS","MP","UM","FM","MH","PW"}

def title(s: str) -> str:
    """LA VERNE → La Verne ; HOBOKEN → Hoboken"""
    return s.title()

def main() -> None:
    print("Downloading XLS …")
    with urllib.request.urlopen(SRC_URL) as r:
        raw = r.read()

    print("Parsing sheet …")
    df = pd.read_excel(
        io.BytesIO(raw),
        sheet_name=SHEET,
        usecols=["DELIVERY ZIPCODE", "PHYSICAL CITY", "PHYSICAL STATE"],
        dtype=str,
        engine="openpyxl",
    )
    df.columns = ["zip", "city", "state"]
    df = df[~df["state"].isin(SKIP)]

    df["zip"]   = df["zip"].str.zfill(5)
    df["city"]  = df["city"].map(title)
    df["state"] = df["state"].map(title)

    # aggregate → {zip: {state: "CA", cities:[...]}}
    data = {}
    for z, rows in df.groupby("zip"):
        data[z] = {
            "state": rows["state"].iat[0],
            "cities": sorted(rows["city"].unique()),
        }

    OUTFILE.parent.mkdir(exist_ok=True, parents=True)
    with gzip.open(OUTFILE, "wt", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))

    print(f"Wrote {len(data):,} ZIPs → {OUTFILE}")

if __name__ == "__main__":
    main()
