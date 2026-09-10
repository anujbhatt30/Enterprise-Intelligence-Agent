"""
Step 2b: SQL agent (Ollama version).

Given a natural language question, this:
1. Asks the local LLM to write a SQL query against the known schema
2. Runs ONLY if the query is a safe SELECT (basic guardrail -- no writes/deletes)
3. Executes it against data/sales.db
4. Asks the LLM to explain the result in plain English

Setup: same as the RAG Ollama version -- requires Ollama running locally
with your chosen model pulled (this project uses qwen3.5:9b).
"""

import os
import re
import sqlite3
import ollama

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sales.db")
MODEL = "qwen3.5:9b"

SCHEMA = """
Table: sales
Columns:
  sale_id      INTEGER  -- unique id per sale
  sale_date    TEXT     -- format YYYY-MM-DD
  product      TEXT     -- e.g. 'Laptop Pro', 'Office Chair'
  category     TEXT     -- 'Electronics', 'Furniture', or 'Stationery'
  region       TEXT     -- 'North', 'South', 'East', or 'West'
  quantity     INTEGER  -- units sold in this sale
  unit_price   REAL     -- price per unit
  total_amount REAL     -- quantity * unit_price (already calculated)
"""

# Basic safety guardrail: only allow read-only queries.
FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|PRAGMA)\b", re.IGNORECASE)


def generate_sql(question):
    prompt = f"""You are a SQL expert. Given this table schema:

{SCHEMA}

Write a single SQLite SELECT query that answers this question:
"{question}"

Rules:
- Output ONLY the SQL query, nothing else -- no explanation, no markdown formatting, no ```sql fences.
- Use only the sales table and columns listed above.
- The query must be read-only (SELECT only).
"""
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    sql = response["message"]["content"].strip()
    # strip markdown fences if the model adds them anyway
    sql = re.sub(r"^```sql\s*|\s*```$", "", sql, flags=re.IGNORECASE).strip()
    return sql


def run_sql(sql):
    if FORBIDDEN.search(sql):
        raise ValueError(f"Blocked potentially unsafe SQL: {sql}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql)
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return columns, rows


def explain_result(question, sql, columns, rows):
    result_preview = "\n".join(str(dict(zip(columns, r))) for r in rows[:20])
    prompt = f"""A user asked: "{question}"

This SQL query was run:
{sql}

Result (up to 20 rows shown):
{result_preview}

Answer the user's question in plain, concise English based on this result.
Mention specific numbers from the result.
"""
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]


def ask(question):
    sql = generate_sql(question)
    print(f"Generated SQL:\n{sql}\n")

    columns, rows = run_sql(sql)
    print(f"Result ({len(rows)} row(s)):")
    for r in rows[:10]:
        print(dict(zip(columns, r)))

    answer = explain_result(question, sql, columns, rows)
    print(f"\nANSWER:\n{answer}")
    return answer


if __name__ == "__main__":
    ask("What were total sales in Q4 2025?")
