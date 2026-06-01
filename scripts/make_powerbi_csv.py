"""
Build a small, Power-BI-ready CSV from the large LendingClub loan.csv file.

- Reads the data dictionary to know which columns are valid.
- Reads only the header of loan.csv to see the real columns.
- Keeps the target columns that actually exist (warns + suggests for missing).
- Streams loan.csv in 200k-row chunks so the full 1.19 GB never loads at once.
- Drops null loan_status, samples 150k rows (random_state=42).
- Leaves messy text fields untouched (cleaning happens in Power Query).
"""

import difflib
import pandas as pd

# --- Paths (forward slashes to avoid Windows escape issues) ---------------
FOLDER = "C:/Users/harsh/OneDrive/Desktop/lending club loan powerbi"
DICT_PATH = f"{FOLDER}/LCDataDictionary.xlsx"
LOAN_PATH = f"{FOLDER}/loan.csv"
OUT_PATH = f"{FOLDER}/loans_clean.csv"

CHUNKSIZE = 200_000
SAMPLE_N = 150_000
RANDOM_STATE = 42

TARGET_COLS = [
    "loan_amnt", "funded_amnt", "term", "int_rate", "installment", "grade",
    "sub_grade", "emp_length", "home_ownership", "annual_inc",
    "verification_status", "issue_d", "loan_status", "purpose", "addr_state",
    "dti", "total_pymnt", "recoveries",
]


def main():
    # --- Step 1: valid column names from the data dictionary --------------
    dict_df = pd.read_excel(DICT_PATH)
    # The dictionary's first column holds the field/column names.
    name_col = dict_df.columns[0]
    dict_names = (
        dict_df[name_col]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )
    print("=" * 70)
    print(f"STEP 1: Data dictionary columns ({len(dict_names)} names)")
    print("=" * 70)
    for n in dict_names:
        print(f"  - {n}")

    # --- Step 2: real header of loan.csv ----------------------------------
    header_df = pd.read_csv(LOAN_PATH, nrows=0)
    file_cols = list(header_df.columns)
    print("\n" + "=" * 70)
    print(f"STEP 2: Actual loan.csv columns ({len(file_cols)} columns)")
    print("=" * 70)
    for c in file_cols:
        print(f"  - {c}")

    # --- Step 3: keep only target columns that exist in the file ----------
    file_cols_set = set(file_cols)
    dict_pool = dict_names + file_cols  # pool for closest-match suggestions

    kept, missing = [], []
    print("\n" + "=" * 70)
    print("STEP 3: Resolving target columns against the file")
    print("=" * 70)
    for col in TARGET_COLS:
        if col in file_cols_set:
            kept.append(col)
            print(f"  [keep]    {col}")
        else:
            missing.append(col)
            suggestion = difflib.get_close_matches(col, dict_pool, n=1, cutoff=0.0)
            sug = suggestion[0] if suggestion else "(no suggestion)"
            print(f"  [MISSING] {col}  -> closest match: {sug}")

    if missing:
        print(f"\n  WARNING: {len(missing)} target column(s) not found in loan.csv: {missing}")
    print(f"\n  Keeping {len(kept)} column(s): {kept}")

    # --- Step 4: stream the file in chunks, keeping only kept columns -----
    print("\n" + "=" * 70)
    print(f"STEP 4: Reading loan.csv in chunks of {CHUNKSIZE:,} rows")
    print("=" * 70)
    chunks = []
    total_rows = 0
    reader = pd.read_csv(
        LOAN_PATH,
        usecols=kept,
        chunksize=CHUNKSIZE,
        low_memory=False,
    )
    for i, chunk in enumerate(reader, start=1):
        chunks.append(chunk)
        total_rows += len(chunk)
        print(f"  chunk {i:>3}: {len(chunk):>7,} rows (running total {total_rows:,})")

    df = pd.concat(chunks, ignore_index=True)
    print(f"\n  Concatenated shape: {df.shape}")

    # --- Step 5: drop null loan_status, then random sample ----------------
    print("\n" + "=" * 70)
    print("STEP 5: Drop null loan_status + sample 150k rows")
    print("=" * 70)
    if "loan_status" in df.columns:
        before = len(df)
        df = df[df["loan_status"].notna()]
        print(f"  Dropped {before - len(df):,} rows with null loan_status "
              f"({len(df):,} remain)")
    else:
        print("  loan_status not in kept columns -> skipping null drop")

    n = min(SAMPLE_N, len(df))
    if n < SAMPLE_N:
        print(f"  Only {len(df):,} rows available; sampling {n:,} instead of {SAMPLE_N:,}")
    df = df.sample(n=n, random_state=RANDOM_STATE).reset_index(drop=True)
    print(f"  Sampled shape: {df.shape}")

    # --- Step 6: NO cleaning of messy text fields (left as-is) ------------
    # term, int_rate, emp_length etc. are intentionally untouched.

    # --- Step 7: save -----------------------------------------------------
    df.to_csv(OUT_PATH, index=False)
    print("\n" + "=" * 70)
    print(f"STEP 7: Saved -> {OUT_PATH}")
    print("=" * 70)

    # --- Step 8: sanity check ---------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 8: Final sanity check")
    print("=" * 70)
    print(f"  Final shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print("\n  df.head():")
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(df.head())


if __name__ == "__main__":
    main()
