from flask import Flask, request, redirect
from db import Database, DATA_DIR
import os

app = Flask(__name__)
db = Database()

# load users table if it exists on disk, otherwise create it
if os.path.exists(f"{DATA_DIR}/users.json"):
    try:
        db.load("users")
    except Exception:
        db.create_table("users", ["id", "name", "email"], pk="id", uniques=["email"], if_not_exists=True)
else:
    db.create_table("users", ["id", "name", "email"], pk="id", uniques=["email"], if_not_exists=True)

@app.route("/", methods=["GET", "POST"])
def index():
    table = db.tables.get("users")
    if request.method == "POST":
        try:
            table.insert({
                "id": request.form.get("id"),
                "name": request.form.get("name"),
                "email": request.form.get("email")
            })
            db.save("users")
            return redirect("/")
        except ValueError as e:
            return f"Error: {e}", 400

    users = table.rows if table else []
    html = "<h1>Users</h1><ul>"
    for u in users:
        html += f"<li>{u}</li>"
    html += "</ul>"

    html += """
    <form method="post">
      ID:<input name="id"><br>
      Name:<input name="name"><br>
      Email:<input name="email"><br>
      <button>Add</button>
    </form>
    """
    return html

if __name__ == "__main__":
    app.run(debug=True)
