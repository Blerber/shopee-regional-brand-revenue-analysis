import argparse
import re
import sys
from unidecode import unidecode
import pandas as pd
from rapidfuzz import fuzz

def norm(s: str) -> str:
    if pd.isna(s):
        return ""
    s = unidecode(str(s)).lower()
    # keep letters/numbers/spaces; drop everything else
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    # squash whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def compact(s: str) -> str:
    return s.replace(" ", "") if s else s

def build_brand_keyspace(brands_df: pd.DataFrame) -> pd.DataFrame:
    # Expect columns: brand, key
    out = brands_df.copy()
    out["key_norm"] = out["key"].fillna("").map(norm)
    out["key_compact"] = out["key_norm"].map(compact)
    # Drop empties/dupes
    out = out[(out["key_norm"] != "") & (out["brand"] != "")]
    out = out.drop_duplicates(subset=["brand", "key_norm"])
    return out

def score_listing_against_key(list_norm: str, list_compact: str, key_norm: str, key_compact: str) -> int:
    # Try multiple similarity views; take the best
    s1 = fuzz.partial_ratio(list_norm, key_norm)
    s2 = fuzz.token_set_ratio(list_norm, key_norm)
    # compact vs compact to forgive space differences completely
    s3 = fuzz.partial_ratio(list_compact, key_compact)
    return max(s1, s2, s3)

def best_brand(list_norm: str, list_compact: str, brand_keys: pd.DataFrame) -> tuple[str | None, int, str | None]:
    best = (None, 0, None)  # (brand, score, matched_key_norm)
    # Optional fast prefilter: shortlist keys that appear as substring in norm/compact
    sub = brand_keys[
        brand_keys["key_norm"].apply(lambda k: k in list_norm) |
        brand_keys["key_compact"].apply(lambda k: k in list_compact)
    ]
    candidates = sub if len(sub) else brand_keys

    for _, row in candidates.iterrows():
        sc = score_listing_against_key(list_norm, list_compact, row["key_norm"], row["key_compact"])
        if sc > best[1]:
            best = (row["brand"], sc, row["key_norm"])
    return best

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv", help="e.g., data\\raw\\malaysia\\combined_my.csv")
    ap.add_argument("brands_csv", help="e.g., data\\brands\\brands_master.csv")
    ap.add_argument("output_csv", help="e.g., data\\processed\\malaysia_matched.csv")
    ap.add_argument("--listing-col", default="Listing (Cleaned)")
    ap.add_argument("--price-col", default="Price (USD)")
    ap.add_argument("--units-col", default="Units Sold (Numeric)")
    ap.add_argument("--threshold", type=int, default=85, help="min match score to accept")
    args = ap.parse_args()

    # Load
    try:
        df = pd.read_csv(args.input_csv)
    except Exception as e:
        print(f"Failed to read input CSV: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        brands = pd.read_csv(args.brands_csv)
    except Exception as e:
        print(f"Failed to read brands CSV: {e}", file=sys.stderr)
        sys.exit(1)

    # Sanity columns
    for col in [args.listing_col]:
        if col not in df.columns:
            print(f"Missing column in input: {col}", file=sys.stderr)
            sys.exit(1)
    if "brand" not in brands.columns or "key" not in brands.columns:
        print("brands_master.csv must have columns: brand,key", file=sys.stderr)
        sys.exit(1)

    # Prep fields
    df["__list_norm"] = df[args.listing_col].fillna("").map(norm)
    df["__list_compact"] = df["__list_norm"].map(compact)

    brand_keys = build_brand_keyspace(brands)

    # Match
    matched_brand = []
    match_score = []
    matched_key = []

    for ln, lc in zip(df["__list_norm"], df["__list_compact"]):
        b, sc, keyn = best_brand(ln, lc, brand_keys)
        if b is not None and sc >= args.threshold:
            matched_brand.append(b)
            match_score.append(sc)
            matched_key.append(keyn)
        else:
            matched_brand.append("no brand")
            match_score.append(sc)
            matched_key.append(keyn)

    df["Brand (Matched)"] = matched_brand
    df["Match Score"] = match_score
    df["Matched Key"] = matched_key

    # Optional convenience: revenue if columns exist
    if args.price_col in df.columns and args.units_col in df.columns:
        try:
            df["__price"] = pd.to_numeric(df[args.price_col], errors="coerce")
            df["__units"] = pd.to_numeric(df[args.units_col], errors="coerce")
            df["Revenue (USD)"] = (df["__price"].fillna(0) * df["__units"].fillna(0)).round(2)
        except Exception:
            # don't fail the whole run if types are odd
            pass

    # Clean internals
    df = df.drop(columns=[c for c in df.columns if c.startswith("__")], errors="ignore")

    # Save
    df.to_csv(args.output_csv, index=False)
    print(f"✓ Wrote {args.output_csv}")

if __name__ == "__main__":
    main()
