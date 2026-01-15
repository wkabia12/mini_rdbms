# mini_rdbms 

A tiny, educational in-memory relational DB with a minimal SQL-like parser, a REPL, and a simple Flask web UI. Data is persisted as JSON files under the `data/` directory.

---

## Key Features

- Tables with defined `columns`, optional `primary_key` and `unique_keys`
- CRUD operations via `Table` methods and a small SQL-like language (REPL)
- Multi-database support: each database is stored under `data/<dbname>/` and tables are saved as `data/<dbname>/<table>.json`
- Web UI with a database dashboard and per-table CRUD pages
  - Landing page: `/` redirects to `/databases`
  - Users page: `/users` (backwards-compatible)
- Persistence APIs: `Database.save(name, base_dir=...)` and `Database.load(name, base_dir=...)`
- Tests using `pytest` in `tests/` and CI configured with GitHub Actions

---

##  Setup

```bash
# create & activate a virtualenv (Linux/macOS)
python3 -m venv venv
source venv/bin/activate

# install deps
pip install -r requirements.txt
```

Files added to repo:
- `requirements.txt` (Flask, pytest)
- `.github/workflows/ci.yml` (runs tests on push/PR)
- `.gitignore` (ignores `__pycache__/`, `.pytest_cache/`, `venv/`, `data/`, etc.)

---

## Running

- Start the REPL:

```bash
python repl.py
```

REPL example commands:
```
CREATE TABLE products (id, name, price)
INSERT INTO products VALUES (p1, 'Phone', 199)
SELECT * FROM products
```

- Start the web app (development server):

```bash
python webapp.py
```

Behavior:
- The root `/` redirects to `/databases` (DB dashboard).
- Create a database from the dashboard (creates `data/<dbname>/`).
- Inside a database page you can create tables by specifying columns, a primary key, and unique keys. Tables are saved to `data/<dbname>/<table>.json`.
- Table pages offer Add/Edit/Delete row operations via a consistent UI and will validate constraints (primary / unique keys).

---

## Tests

Run tests with:

```bash
venv/bin/pytest -q
```

Current test modules:
- `tests/test_db.py` — unit tests for DB / Table behavior
- `tests/test_sql.py` — SQL parser tests
- `tests/test_webapp.py` — web UI basic tests
- `tests/test_databases.py` — multi-database + table CRUD flows

Tests isolate `DATA_DIR` to avoid polluting local data.

---

## Notes & Limitations

- Security: there is no CSRF protection and forms are not authenticated — **do not** expose this to the public internet.
- SQL: the parser is intentionally simple and supports only a small subset shown above.
- Persistence: data is simple JSON files; not transactional or concurrent-safe.

---