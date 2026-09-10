"""
Step 3: SQL + Python analysis layer.

Some questions can't be answered by a single SQL query -- e.g. "which
category grew fastest?" needs: pull raw numbers with SQL -> compute
growth rates with Python/pandas -> have the LLM interpret the result.

This is the same three-stage pattern as sql_agent_ollama.py, but with a
pandas computation step inserted between SQL and the final explanation.
"""

import os
import sqlite3
import pandas as pd
import ollama

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sales.db")
MODEL = "qwen3.5:9b"


def load_quarterly_category_sales():
    """Pull raw sales and aggregate into category x quarter totals."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT sale_date, category, total_amount FROM sales", conn)
    conn.close()

    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["quarter"] = df["sale_date"].dt.to_period("Q").astype(str)

    pivot = (
        df.groupby(["category", "quarter"])["total_amount"]
        .sum()
        .round(2)
        .unstack("quarter")
        .fillna(0)
    )
    return pivot


def compute_growth(pivot):
    """Compute % growth from the first to the last quarter, per category."""
    quarters = sorted(pivot.columns)
    first_q, last_q = quarters[0], quarters[-1]

    growth = pd.DataFrame({
        "first_quarter": pivot[first_q],
        "last_quarter": pivot[last_q],
    })
    growth["growth_pct"] = (
        (growth["last_quarter"] - growth["first_quarter"]) / growth["first_quarter"] * 100
    ).round(1)
    growth = growth.sort_values("growth_pct", ascending=False)
    return growth, first_q, last_q


def explain_growth(question, growth_table, first_q, last_q):
    table_text = growth_table.reset_index().to_string(index=False)
    prompt = f"""A user asked: "{question}"

Here is a table comparing each category's sales in {first_q} (first quarter
of data) versus {last_q} (last quarter of data), with the percentage growth
between them:

{table_text}

Answer the user's question in plain, concise English. Mention the specific
category and its growth percentage. If a category shrank, mention that too
if relevant.
"""
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]


def ask(question="Which product category grew fastest?"):
    pivot = load_quarterly_category_sales()
    growth, first_q, last_q = compute_growth(pivot)

    print(f"Quarterly sales by category ({first_q} -> {last_q}):")
    print(pivot.to_string())
    print(f"\nGrowth {first_q} -> {last_q}:")
    print(growth.to_string())

    answer = explain_growth(question, growth, first_q, last_q)
    print(f"\nANSWER:\n{answer}")
    return answer


if __name__ == "__main__":
    ask()
