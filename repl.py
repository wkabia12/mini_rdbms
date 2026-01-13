from db import Database, DATA_DIR
from sql import parse
import os

db = Database()
# load any existing tables from disk
if os.path.isdir(DATA_DIR):
    for fname in os.listdir(DATA_DIR):
        if fname.endswith('.json'):
            name = fname[:-5]
            try:
                db.load(name)
                print(f"Loaded table {name}")
            except Exception as e:
                print(f"Failed to load {name}: {e}")

while True:
    q = input("rdbms> ").strip()
    if not q:
        continue
    if q.lower() == "exit":
        try:
            db.save_all()
        except Exception as e:
            print("Error saving data:", e)
        break

    try:
        cmd = parse(q)
    except ValueError as e:
        print("Parse error:", e)
        continue

    try:
        if cmd[0] == "CREATE":
            db.create_table(cmd[1], cmd[2], if_not_exists=True)
            db.save(cmd[1])
            print("Table created")
        elif cmd[0] == "INSERT":
            if cmd[1] not in db.tables:
                print("Table does not exist")
                continue
            table = db.tables[cmd[1]]
            record = dict(zip(table.columns, cmd[2]))
            table.insert(record)
            db.save(cmd[1])
            print("Row inserted")
        elif cmd[0] == "SELECT":
            if cmd[1] not in db.tables:
                print("Table does not exist")
                continue
            where = None
            if len(cmd) > 2:
                where = cmd[2]
            if where:
                rows = db.tables[cmd[1]].select(where)
            else:
                rows = db.tables[cmd[1]].rows
            print(rows)
        elif cmd[0] == "DELETE":
            if cmd[1] not in db.tables:
                print("Table does not exist")
                continue
            db.tables[cmd[1]].delete(cmd[2])
            db.save(cmd[1])
            print("Row deleted")
        elif cmd[0] == "DROP":
            db.drop_table(cmd[1])
            print("Table dropped")
        else:
            print("Unknown command")
    except Exception as e:
        print("Error:", e)
