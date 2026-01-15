#Core DB Engine

import json, os

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

class Table:
    def __init__(self, name, columns, primary_key=None, unique_keys=None):
        self.name = name
        self.columns = columns
        self.primary_key = primary_key
        self.unique_keys = unique_keys or []
        self.rows = []
        self.indexes = {}

    def insert(self, record):
        # basic validation
        if not isinstance(record, dict):
            raise ValueError("Record must be a dict")

        missing = [c for c in self.columns if c not in record]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        extra = [k for k in record.keys() if k not in self.columns]
        if extra:
            raise ValueError(f"Unknown columns: {extra}")

        # primary key check
        if self.primary_key:
            if self.primary_key not in record:
                raise ValueError(f"Missing primary key: {self.primary_key}")
            for r in self.rows:
                if r.get(self.primary_key) == record.get(self.primary_key):
                    raise ValueError("Duplicate primary key")

        # unique key check
        for uk in self.unique_keys:
            if uk not in record:
                raise ValueError(f"Missing unique key: {uk}")
            for r in self.rows:
                if r.get(uk) == record.get(uk):
                    raise ValueError(f"Duplicate unique key: {uk}")

        # store a copy to avoid external mutation
        self.rows.append(record.copy())

    def select(self, where=None):
        if not where:
            return self.rows
        return [r for r in self.rows if r.get(where[0]) == where[1]]

    def update(self, where, updates):
        # where should be a (column, value) tuple
        if not (isinstance(where, (list, tuple)) and len(where) == 2):
            raise ValueError("where must be a (column, value) tuple")
        col, val = where[0], where[1]

        # validate update keys
        for k in updates:
            if k not in self.columns:
                raise ValueError(f"Unknown column in update: {k}")

        count = 0
        for r in self.rows:
            if r.get(col) == val:
                new_record = r.copy()
                new_record.update(updates)

                # primary key check
                if self.primary_key and self.primary_key in updates:
                    new_pk = new_record[self.primary_key]
                    for other in self.rows:
                        if other is not r and other.get(self.primary_key) == new_pk:
                            raise ValueError("Duplicate primary key on update")

                # unique keys
                for uk in self.unique_keys:
                    if uk in updates:
                        new_uk = new_record.get(uk)
                        for other in self.rows:
                            if other is not r and other.get(uk) == new_uk:
                                raise ValueError(f"Duplicate unique key on update: {uk}")

                r.update(updates)
                count += 1
        return count

    def delete(self, where):
        if not (isinstance(where, (list, tuple)) and len(where) == 2):
            raise ValueError("where must be a (column, value) tuple")
        self.rows = [r for r in self.rows if r.get(where[0]) != where[1]]

class Database:
    def __init__(self):
        self.tables = {}

    def create_table(self, name, columns, pk=None, uniques=None, if_not_exists=False):
        if name in self.tables:
            if if_not_exists:
                return
            raise ValueError("Table already exists")
        self.tables[name] = Table(name, columns, pk, uniques)

    def save(self, name, base_dir=None):
        if name not in self.tables:
            raise ValueError("Table does not exist")
        t = self.tables[name]
        data = {
            "name": t.name,
            "columns": t.columns,
            "primary_key": t.primary_key,
            "unique_keys": t.unique_keys,
            "rows": t.rows,
        }
        base = base_dir or DATA_DIR
        os.makedirs(base, exist_ok=True)
        path = f"{base}/{name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def save_all(self, base_dir=None):
        for name in list(self.tables.keys()):
            self.save(name, base_dir=base_dir)

    def load(self, name, base_dir=None):
        base = base_dir or DATA_DIR
        path = f"{base}/{name}.json"
        if not os.path.exists(path):
            raise ValueError("Table file does not exist")
        with open(path) as f:
            data = json.load(f)
        # basic validation
        if "name" not in data or "columns" not in data or "rows" not in data:
            raise ValueError("Invalid table file")
        t = Table(data["name"], data["columns"], data.get("primary_key"), data.get("unique_keys", []))
        t.rows = data["rows"]
        self.tables[name] = t

    def drop_table(self, name, base_dir=None):
        if name not in self.tables:
            raise ValueError("Table does not exist")

        base = base_dir or DATA_DIR
        # Remove JSON file if it exists
        path = f"{base}/{name}.json"
        if os.path.exists(path):
            os.remove(path)

        del self.tables[name]
