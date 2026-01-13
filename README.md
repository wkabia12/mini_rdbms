# mini_rdbms ✅

A tiny, educational in-memory relational DB with a minimal SQL-like parser, a REPL, and a simple Flask web UI. Data is persisted as JSON files under the `data/` directory.

---

## 🔧 Features

- Tables with defined `columns`, optional `primary_key` and `unique_keys`
- CRUD operations via Table methods and a small SQL-like language
- Persistence: tables are saved to `data/<table>.json` (use `Database.save_all()` to persist)
- Interactive REPL (`repl.py`) and a minimal web UI (`webapp.py`) for quick demos
- Tests using `pytest` in `tests/`

---

## ⚙️ Setup

```bash
# create & activate a virtualenv (Linux/macOS)
python3 -m venv venv
source venv/bin/activate

# install deps
pip install Flask pytest
```

> Tip: you can also install all deps with `pip install -r requirements.txt` if you add one.

---

## ▶️ Running

- Start the REPL:

```bash
python repl.py
```

Commands example (type and press Enter):
```
CREATE TABLE users (id, name, email)
INSERT INTO users VALUES (1, 'Alice', 'a@example.com')
SELECT * FROM users
SELECT * FROM users WHERE id = 1
DELETE FROM users WHERE id = 1
DROP TABLE users
exit  # saves all tables and quits
```

- Start the web app (opens on http://127.0.0.1:5000/):

```bash
python webapp.py
```

The web UI persists to `data/users.json` and returns 400 errors if inserts violate constraints (duplicate email / missing fields).

---

## 🧪 Tests

Run the test suite with:

```bash
venv/bin/pytest -q
```

Tests isolate the `DATA_DIR` so they won't affect your local `data/` files.

---

## ⚠️ Notes & Limitations

- SQL parser is intentionally minimal (supports a small subset shown above). Invalid SQL raises `ValueError` with a helpful message.
- `Table.insert` and `Table.update` now validate columns and enforce `primary_key` and `unique_keys`.
- This project is educational/demo code, not intended for production use.

---

## Contributing

Small improvements or bug fixes are welcome—add tests and open a PR.

---

If you'd like, I can also add a `requirements.txt` and a GitHub Actions workflow to run tests on push. 🔁
