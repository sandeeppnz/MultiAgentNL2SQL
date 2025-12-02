# core/db/db_results.py

import pandas as pd

def normalize_results(df: pd.DataFrame):
    """
    Converts DataFrame into JSON-safe python dict.
    """
    if df is None or df.empty:
        return {"rows": [], "row_count": 0, "columns": []}

    return {
        "columns": list(df.columns),
        "row_count": len(df),
        "rows": df.to_dict(orient="records"),
    }
