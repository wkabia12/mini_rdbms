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
        # primary key check
        if self.primary_key:
            for r in self.rows:
                if r[self.primary_key] == record[self.primary_key]:
                    raise ValueError("Duplicate primary key")

        # unique key check
        for uk in self.unique_keys:
            for r in self.rows:
                if r[uk] == record[uk]:
                    raise ValueError(f"Duplicate unique key: {uk}")

        self.rows.append(record)

    def select(self, where=None):
        if not where:
            return self.rows
        return [r for r in self.rows if r.get(where[0]) == where[1]]

    def update(self, where, updates):
        for r in self.rows:
            if r.get(where[0]) == where[1]:
                r.update(updates)

    def delete(self, where):
        self.rows = [r for r in self.rows if r.get(where[0]) != where[1]]

class Database:
    def __init__(self):
        self.tables = {}

    def create_table(self, name, columns, pk=None, uniques=None):
        self.tables[name] = Table(name, columns, pk, uniques)

    def save(self, name):
        path = f"{DATA_DIR}/{name}.json"
        with open(path, "w") as f:
            json.dump(self.tables[name].__dict__, f, indent=2)

    def load(self, name):
        path = f"{DATA_DIR}/{name}.json"
        with open(path) as f:
            data = json.load(f)
        t = Table(data["name"], data["columns"], data["primary_key"], data["unique_keys"])
        t.rows = data["rows"]
        self.tables[name] = t