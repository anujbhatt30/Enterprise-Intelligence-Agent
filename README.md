# Enterprise Intelligence Agent — Step 1: RAG

## What's here
A working, tested RAG (retrieval-augmented generation) pipeline:

```
enterprise_agent/
├── data/company_docs/     # drop your .txt policy/handbook docs here
├── rag/
│   ├── ingest.py           # chunks docs + builds a TF-IDF index
│   ├── retrieve.py         # finds the top-k relevant chunks for a query
│   └── generate.py         # retrieval + Claude -> final cited answer
└── requirements.txt
```

## How to run it

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Add your own company documents (.txt files) to `data/company_docs/`.
   A sample `leave_policy.txt` is already included so you can test immediately.

3. Build the index:
   ```
   python rag/ingest.py
   ```

4. Test retrieval only (no API key needed):
   ```
   python rag/retrieve.py
   ```

5. Get a full cited answer — two options:

   **Option A: Claude API (cloud, needs an API key, small cost per call)**
   - Get a key from https://console.anthropic.com/
   - Create a `.env` file in this folder: `ANTHROPIC_API_KEY=sk-ant-...`
   - Run:
     ```
     python rag/generate.py
     ```

   **Option B: Ollama (fully local, free, no API key)**
   - Install Ollama from https://ollama.com
   - Pull a model: `ollama pull llama3.1`
   - Install the Python client: `pip install ollama`
   - Run:
     ```
     python rag/generate_ollama.py
     ```

## Verified working
Retrieval was tested end-to-end against the sample leave policy doc:
query "How many days of annual leave do employees get?" correctly
returned the Annual Leave section as the top match (similarity 0.61).

## What's next
Combine this into a simple demo UI (Streamlit) if you want a polished
front-end to show off the whole thing.

---

# Step 5: Streamlit UI

## What's here
```
app/
└── app.py   # chat interface wrapping the router from Step 4
```

A single chat box: type a question, see which tool handled it, and get
the answer — no terminal commands needed once it's running. Includes a
sidebar with the 4 example questions from the original project spec as
one-click buttons.

## How to run it

1. Install Streamlit (one-time):
   ```
   pip install streamlit
   ```

2. Make sure the database and RAG index exist (skip if you already ran
   Steps 2 and 1):
   ```
   python sql_agent/create_db.py
   python rag/ingest.py
   ```

3. Launch the app:
   ```
   streamlit run app/app.py
   ```
   This opens a browser tab automatically (usually at
   http://localhost:8501). If it doesn't open automatically, copy the
   URL shown in the terminal into your browser.

4. Click one of the example questions in the sidebar, or type your own
   question in the chat box at the bottom.

## Verified working (tested in this environment)
- The app compiles with no syntax errors.
- The exact import chain the app uses (router, RAG, SQL agent, analysis
  layer) was tested and resolves cleanly with no path errors.

The actual browser UI and Ollama-driven responses need to be tested on
your machine — Streamlit needs a local server + browser, which can't run
in this environment.

## Notes for scaling this up
- Add a toggle to show the generated SQL / retrieved chunks for
  transparency (great for demos — shows *how* it got the answer, not
  just the answer).
- Add a "was this helpful?" thumbs up/down per answer, and log it — a
  simple feedback loop is an easy thing to mention in interviews.
- Deploy it (Streamlit Community Cloud is free) if you want a shareable
  link — though note that would require switching from local Ollama to
  a cloud LLM API for anyone besides you to actually use it.

---

# Step 4: Router

## What's here
```
router/
└── router_ollama.py   # classifies a question -> dispatches to the right tool
```

This is the piece that makes it a genuine "agent" rather than four
separate scripts: it looks at the question, decides RAG / SQL / ANALYSIS
/ REASONING, and calls the right function from Steps 1-3.

## How to run it
```
python router/router_ollama.py
```
This runs all 4 example questions from your original project spec, one
per category, and prints which category each was classified into plus
the final answer.

To ask your own question, add at the bottom of the file:
```python
print(route("How many sick days do employees get?"))
```

## Verified working (tested in this environment, without an LLM)
- All imports across rag/, sql_agent/, and router/ resolve correctly
  with no path errors.
- The REASONING handler's data-gathering step (pulling the growth table)
  was tested directly and returns the correct numbers.

The LLM classification step (deciding RAG vs SQL vs ANALYSIS vs
REASONING) needs to be tested on your machine — this is the part most
likely to need prompt tweaks if the model misclassifies a question.

## How it works
1. `classify()` — asks the LLM to label the question as one of 4
   categories, with a short description + example of each.
2. `route()` — based on the label, calls the matching function from
   Steps 1-3 and returns its answer.
3. `handle_reasoning()` — for "why"/"what should we do" questions, first
   pulls the growth data (reusing Step 3's functions), then asks the LLM
   to explain and recommend based on those real numbers — not just
   free-associate an answer.

## If classification gets it wrong
This is the most likely rough edge, and totally normal for a first pass.
If you ask something and it picks the wrong category:
- Print `category` before routing to see what it chose.
- Add the misclassified question as an extra example in the `classify()`
  prompt — a few good examples usually fixes it fast.
- For borderline cases (e.g. "what were Q4 sales and why did they drop?"),
  you could route to REASONING by default when a question contains both
  a factual and a "why" component — REASONING can still pull SQL data itself.

## Notes for scaling this up
- Add the citation-forcing instruction ("give me the answer with
  sources") as a modifier on top of RAG answers — `generate_ollama.py`
  already does this by default.
- For a real company deployment, log every question + chosen category +
  answer, so you can review and improve the router's accuracy over time.
- Consider a confidence threshold: if the LLM isn't confident about the
  category, ask the user a clarifying question instead of guessing.

---

# Step 3: SQL + Python Analysis Layer

## What's here
```
sql_agent/
└── analysis_ollama.py   # question -> SQL -> pandas computation -> LLM interpretation
```

This handles questions a single SQL query can't answer directly — like
"which category grew fastest?" — by adding a pandas computation step
between the raw SQL pull and the final LLM explanation.

## How to run it
```
python sql_agent/analysis_ollama.py
```
Prints the raw quarterly pivot table, the computed growth percentages,
then the LLM's plain-English answer.

## Verified working (tested in this environment, without an LLM)
The SQL pull + pandas growth computation was tested directly against the
sample database and produced a genuinely interesting result:

| Category    | Q1 2025   | Q4 2025   | Growth   |
|-------------|-----------|-----------|----------|
| Stationery  | 2,542.98  | 3,214.18  | +26.4%   |
| Furniture   | 51,020.33 | 64,162.20 | +25.8%   |
| Electronics | 132,906.26| 122,353.48| -7.9%    |

Electronics has the highest total sales (from Step 2) but is actually
*shrinking*, while Stationery and Furniture are both growing — a good
real example of why "highest total" and "fastest growing" need different
tools/queries to answer correctly.

The LLM interpretation step needs to be tested on your machine with Ollama.

## How it works
1. `load_quarterly_category_sales()` — pulls raw sales via SQL, then uses
   pandas to group by category and quarter into a pivot table.
2. `compute_growth()` — computes % change from the first to the last
   quarter of data, per category.
3. `explain_growth()` — sends the computed table (not raw rows) to the
   LLM, which writes the plain-English answer citing real numbers.

## Notes for scaling this up
- This uses first-quarter-vs-last-quarter growth as a simple example.
  For real use, you might want month-over-month, trailing 3-month
  average, or year-over-year growth depending on what "grew fastest"
  should mean for your business.
- The same pattern (SQL -> pandas -> LLM) extends to other analysis
  questions: correlation between price and volume, seasonality, top
  N products per region, etc. Add a new function per analysis type.

---

# Step 2: SQL Agent

## What's here
```
sql_agent/
├── create_db.py           # builds a sample sales.db (SQLite) with 600 rows
└── sql_agent_ollama.py     # question -> SQL -> execute -> plain-English answer
```

## How to run it

1. Make sure Ollama is running and your model is pulled (same as Step 1).

2. Create the sample database (from inside the `enterprise_agent` folder):
   ```
   python sql_agent/create_db.py
   ```
   This creates `data/sales.db` with a year of sample sales data across
   3 categories, 4 regions, and 6 products.

3. Ask a question:
   ```
   python sql_agent/sql_agent_ollama.py
   ```
   This runs the built-in example question ("What were total sales in
   Q4 2025?"). To ask your own question, edit the last line of the file:
   ```python
   ask("Which product category grew fastest?")
   ```

## Verified working (tested in this environment, without an LLM)
- Database creation: confirmed 600 rows created correctly.
- Query execution: a Q4 2025 total-sales query correctly returned $189,729.86.
- Safety guardrail: a `DROP TABLE` query was correctly blocked before execution.

The LLM-driven SQL generation step needs to be tested on your machine with
Ollama, since it can't run in this environment — try it and paste me the
output.

## How it works
1. `generate_sql()` sends your question + the table schema to the LLM and
   asks for ONLY a SQL query back (no prose).
2. `run_sql()` checks the query against a blocklist (no INSERT/UPDATE/
   DELETE/DROP/etc.) before running it — this is a basic guardrail, not
   a full security solution. For a real company database, also use a
   read-only database user/connection as a second layer of protection.
3. `explain_result()` sends the SQL + result back to the LLM to turn the
   raw rows into a plain-English answer with the actual numbers.

## Notes for scaling this up
- Swap `DB_PATH` to point at your real database (Postgres/MySQL will need
  a different connection library, e.g. `psycopg2` or `pymysql`, instead
  of `sqlite3`).
- For production, use a dedicated **read-only** database user/connection
  string — don't rely on the regex blocklist alone.
- Log every generated SQL query somewhere, so you can audit what the
  agent actually ran if a result looks wrong.

## Notes for scaling this up
- TF-IDF is a fast, fully-offline baseline. For better semantic matching
  (e.g. matching "time off" to "annual leave"), swap in embeddings —
  see the comment at the bottom of `rag/ingest.py`.
- Add PDF/DOCX loaders (e.g. `pypdf`, `python-docx`) once you're working
  with real company documents instead of .txt files.
