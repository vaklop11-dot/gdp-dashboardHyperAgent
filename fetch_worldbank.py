import argparse
import json
from pathlib import Path

import pandas as pd
import requests


def fetch_indicator(iso3: str, code: str, out_dir: Path, date_range: str | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://api.worldbank.org/v2/country/{iso3}/indicator/{code}?format=json&per_page=2000"
    if date_range:
        url += f"&date={date_range}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    json_path = out_dir / f"{iso3}_{code}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Try to write a CSV when response contains the expected array in index 1
    csv_path = None
    if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
        df = pd.json_normalize(data[1])
        csv_path = out_dir / f"{iso3}_{code}.csv"
        df.to_csv(csv_path, index=False)

    return csv_path or json_path


def main():
    p = argparse.ArgumentParser(description="Fetch World Bank indicator JSON and optionally save CSV.")
    p.add_argument("iso3", help="Country ISO3 code, e.g. DEU")
    p.add_argument("code", help="Indicator code, e.g. NY.GDP.MKTP.CD")
    p.add_argument("--out", default="data", help="Output directory (default: data)")
    p.add_argument("--date", default=None, help="Date range e.g. 2015:2024")
    args = p.parse_args()

    out = fetch_indicator(args.iso3.upper(), args.code, Path(args.out), args.date)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
