# scripts/aggregate_country_basic.py
# -------------------------------------------------------------------
# Simple brand & shop aggregation after matching.
#
# Usage (PowerShell):
#   python scripts\aggregate_country_basic.py `
#       data\processed\malaysia_matched.csv `
#       data\processed\my_brand_summary.csv `
#       data\processed\my_shop_brand.csv `
#       data\processed\my_unmatched.csv `
#       --brand-col "Brand (Matched)" `
#       --shop-col "Shop" `
#       --price-col "Price (USD)" `
#       --units-col "Units Sold (Numeric)"
# -------------------------------------------------------------------

import argparse
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("matched_csv")
    ap.add_argument("brand_summary_csv")
    ap.add_argument("shop_brand_csv")
    ap.add_argument("unmatched_csv")
    ap.add_argument("--brand-col", default="Brand (Matched)")
    ap.add_argument("--shop-col", default="Shop")
    ap.add_argument("--price-col", default="Price (USD)")
    ap.add_argument("--units-col", default="Units Sold (Numeric)")
    args = ap.parse_args()

    df = pd.read_csv(args.matched_csv)

    # coerce numerics if present
    for c in [args.price_col, args.units_col, "Revenue (USD)"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Brand summary
    if "Revenue (USD)" not in df.columns and all(c in df.columns for c in [args.price_col, args.units_col]):
        df["Revenue (USD)"] = df[args.price_col].fillna(0) * df[args.units_col].fillna(0)

    brand_grp = (
        df.groupby(args.brand_col, dropna=False)
          .agg(
              listings=("Listing", "count") if "Listing" in df.columns else ("Brand (Matched)", "count"),
              units=(args.units_col, "sum"),
              revenue=("Revenue (USD)", "sum"),
              avg_price=(args.price_col, "mean")
          )
          .reset_index()
    )

    # Sort by revenue desc
    brand_grp = brand_grp.sort_values("revenue", ascending=False)
    brand_grp.to_csv(args.brand_summary_csv, index=False)
    print(f"✓ Wrote {args.brand_summary_csv}")

    # Shop x Brand view
    if args.shop_col in df.columns:
        shop_brand = (
            df.groupby([args.shop_col, args.brand_col], dropna=False)
              .agg(
                  listings=("Listing", "count") if "Listing" in df.columns else (args.brand_col, "count"),
                  units=(args.units_col, "sum"),
                  revenue=("Revenue (USD)", "sum")
              )
              .reset_index()
              .sort_values(["revenue"], ascending=False)
        )
        shop_brand.to_csv(args.shop_brand_csv, index=False)
        print(f"✓ Wrote {args.shop_brand_csv}")

    # Unmatched for review
    um = df[df[args.brand_col].eq("no brand")].copy()
    # keep only the most useful columns, if they exist
    keep_cols = [c for c in ["Shop", "Listing", "Listing (Cleaned)", args.units_col, args.price_col, "Match Score"] if c in um.columns]
    if keep_cols:
        um = um[keep_cols]
    um = um.sort_values("Match Score", ascending=False, na_position="last") if "Match Score" in um.columns else um
    um.to_csv(args.unmatched_csv, index=False)
    print(f"✓ Wrote {args.unmatched_csv}")

if __name__ == "__main__":
    main()
