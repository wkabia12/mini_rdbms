from flask import Flask, request, redirect, url_for, render_template_string
from db import Database, DATA_DIR
import os

app = Flask(__name__)
# Simple secret key for flash-like behavior (not used for production)
app.secret_key = "dev-secret"

db = Database()

# load users table if it exists on disk, otherwise create it
if os.path.exists(f"{DATA_DIR}/users.json"):
    try:
        db.load("users")
    except Exception:
        db.create_table("users", ["id", "name", "email"], pk="id", uniques=["email"], if_not_exists=True)
else:
    db.create_table("users", ["id", "name", "email"], pk="id", uniques=["email"], if_not_exists=True)

BASE_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Users</title>
    <style>
      body { font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; padding: 2rem; }
      table { border-collapse: collapse; width: 100%; max-width: 900px; }
      th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
      th { background: #f8f8f8; }
      tr:nth-child(even) { background: #f9f9f9; }
      .actions form { display: inline; margin: 0; }
      .error { color: #b00020; }
      .success { color: #0a7a0a; }
      .controls { margin-top: 1rem; }
      .btn { padding: 6px 10px; border-radius: 4px; border: 1px solid #ccc; background: white; cursor: pointer; }
      .btn.danger { border-color: #d00; color: #d00; }
      .btn.primary { border-color: #06c; color: #06c; }
      /* aligned form rows */
      .form-row { display: flex; align-items: center; gap: 8px; margin-bottom: .5rem; width: 100%; }
      .form-row label { width: 80px; font-weight: 600; }
      .form-row input { padding: 6px; width: 320px; max-width: 100%; border: 1px solid #ccc; border-radius: 4px; }
      .controls form { display: flex; flex-direction: column; align-items: flex-start; }
      .container { max-width: 980px; }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>Users</h1>
      {% if message %}
        <p class="{{ 'error' if error else 'success' }}">{{ message }}</p>
      {% endif %}

      <table>
        <thead>
          <tr><th>ID</th><th>Name</th><th>Email</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {% for u in users %}
            <tr>
              <td>{{ u['id'] }}</td>
              <td>{{ u['name'] }}</td>
              <td>{{ u['email'] }}</td>
              <td class="actions">
                <a class="btn" href="{{ url_for('edit', id=u['id']) }}">Edit</a>
                <form method="post" action="{{ url_for('delete', id=u['id']) }}" style="display:inline">
                  <button class="btn danger" type="submit">Delete</button>
                </form>
              </td>
            </tr>
          {% endfor %}
        </tbody>
      </table>

      <div class="controls">
        <h2>Add User</h2>
        <form method="post" action="{{ url_for('create') }}">
          <div class="form-row"><label for="id">ID:</label><input id="id" name="id"></div>
          <div class="form-row"><label for="name">Name:</label><input id="name" name="name"></div>
          <div class="form-row"><label for="email">Email:</label><input id="email" name="email"></div>
          <button class="btn primary" type="submit">Add</button>
        </form>
      </div>
    </div>
  </body>
</html>
"""

EDIT_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Edit User</title>
    <style>
      body { font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; padding: 2rem; }
      .btn { padding: 6px 10px; border-radius: 4px; border: 1px solid #ccc; background: white; cursor: pointer; }
    </style>
  </head>
  <body>
    <h1>Edit User</h1>
    {% if message %}
      <p class="{{ 'error' if error else 'success' }}">{{ message }}</p>
    {% endif %}
    <form method="post" action="{{ url_for('update', id=orig_id) }}">
      <div class="form-row"><label for="id">ID:</label><input id="id" name="id" value="{{ user['id'] }}"></div>
      <div class="form-row"><label for="name">Name:</label><input id="name" name="name" value="{{ user['name'] }}"></div>
      <div class="form-row"><label for="email">Email:</label><input id="email" name="email" value="{{ user['email'] }}"></div>
      <div style="margin-top:8px;">
        <button class="btn" type="submit">Save</button>
        <a class="btn" href="{{ url_for('index') }}">Cancel</a>
      </div>
    </form>
  </body>
</html>
"""


@app.route('/', methods=['GET'])
def index():
    table = db.tables.get('users')
    users = table.rows if table else []
    # show optional messages via query args
    message = request.args.get('message')
    error = request.args.get('error') == '1'
    return render_template_string(BASE_TEMPLATE, users=users, message=message, error=error)


@app.route('/', methods=['POST'])
def create():
    table = db.tables.get('users')
    if not table:
        return "Users table not found", 500
    try:
        record = {
            'id': request.form.get('id'),
            'name': request.form.get('name'),
            'email': request.form.get('email')
        }
        table.insert(record)
        db.save('users')
        return redirect(url_for('index', message='User added'))
    except ValueError as e:
        return str(e), 400


@app.route('/edit/<id>', methods=['GET'])
def edit(id):
    table = db.tables.get('users')
    if not table:
        return "Users table not found", 500
    user = next((r for r in table.rows if r.get('id') == id), None)
    if not user:
        return "User not found", 404
    message = request.args.get('message')
    error = request.args.get('error') == '1'
    return render_template_string(EDIT_TEMPLATE, user=user, orig_id=id, message=message, error=error)


@app.route('/update/<id>', methods=['POST'])
def update(id):
    table = db.tables.get('users')
    if not table:
        return "Users table not found", 500
    try:
        updates = {
            'id': request.form.get('id'),
            'name': request.form.get('name'),
            'email': request.form.get('email')
        }
        table.update(('id', id), updates)
        db.save('users')
        return redirect(url_for('index', message='User updated'))
    except ValueError as e:
        # return to edit page with error message
        return redirect(url_for('edit', id=id, message=str(e), error=1))


@app.route('/delete/<id>', methods=['POST'])
def delete(id):
    table = db.tables.get('users')
    if not table:
        return "Users table not found", 500
    table.delete(('id', id))
    db.save('users')
    return redirect(url_for('index', message='User deleted'))


if __name__ == '__main__':
    app.run(debug=True)
