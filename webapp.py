from flask import Flask, request, redirect, url_for, render_template_string
from db import Database, DATA_DIR
import os
import shutil

app = Flask(__name__)
# Simple secret key for flash-like behavior (not used for production)
app.secret_key = "dev-secret"

# default single database instance (for backward compatibility / quick demos)
db = Database()

# load users table if it exists on disk, otherwise create it
if os.path.exists(f"{DATA_DIR}/users.json"):
    try:
        db.load("users")
    except Exception:
        db.create_table("users", ["id", "name", "email"], pk="id", uniques=["email"], if_not_exists=True)
else:
    db.create_table("users", ["id", "name", "email"], pk="id", uniques=["email"], if_not_exists=True)

# manager for multiple named databases (stored under DATA_DIR/<dbname>/)
db_instances = {}

def get_db_instance(dbname):
    """Return a Database object for the given dbname, loading tables from disk if necessary."""
    if dbname in db_instances:
        return db_instances[dbname]
    d = Database()
    base = os.path.join(DATA_DIR, dbname)
    if os.path.isdir(base):
        # load all tables from this database directory
        for fname in os.listdir(base):
            if fname.endswith('.json'):
                tname = fname[:-5]
                try:
                    d.load(tname, base_dir=base)
                except Exception:
                    # skip invalid tables
                    pass
    db_instances[dbname] = d
    return d

# This template renders the default users table (backwards compatible view)
# Fragment for the users table content
USERS_TEMPLATE = """
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
<p style="margin-top:1rem"><a class="btn" href="{{ url_for('databases_page') }}">Manage Databases</a></p>
"""

# Shared layout that wraps page fragments in a consistent design
LAYOUT_TEMPLATE = """
<!doctype html>
<html lang=en>
  <head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <style>
      body { font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; padding: 2rem; background: #fafafa; }
      .container { max-width: 980px; margin: 0 auto; background: white; border: 1px solid #eee; border-radius: 8px; padding: 1.2rem; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
      header { display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; }
      nav a { margin-right: 8px; }
      table { border-collapse: collapse; width: 100%; max-width: 100%; }
      th, td { border: 1px solid #eee; padding: 10px; text-align: left; }
      th { background: #f8f8f8; }
      tr:nth-child(even) { background: #fafafa; }
      .actions form { display: inline; margin: 0; }
      .error { color: #b00020; }
      .success { color: #0a7a0a; }
      .controls { margin-top: 1rem; }
      .btn { padding: 6px 10px; border-radius: 4px; border: 1px solid #ccc; background: white; cursor: pointer; }
      .btn.danger { border-color: #d00; color: #d00; }
      .btn.primary { border-color: #06c; color: #06c; }
      .form-row { display: flex; align-items: center; gap: 8px; margin-bottom: .5rem; width: 100%; }
      .form-row label { width: 140px; font-weight: 600; }
      .form-row input { padding: 8px; width: 320px; max-width: 100%; border: 1px solid #ccc; border-radius: 4px; }
      footer { margin-top: 1rem; font-size: 0.9rem; color: #666; }
    </style>
  </head>
  <body>
    <div class="container">
      <header>
        <div>
          <strong>mini_rdbms</strong>
        </div>
        <nav>
          <a class="btn" href="{{ url_for('users_page') }}">Users</a>
          <a class="btn" href="{{ url_for('databases_page') }}">Databases</a>
        </nav>
      </header>
      <main>
        {{ content|safe }}
      </main>
      <footer>
        Small demo DB - data stored under <code>{{ data_dir }}</code>
      </footer>
    </div>
  </body>
</html>
"""

# Template to render the list of databases and creation form
# content fragment for the databases page
DATABASES_TEMPLATE = """
<h1>Databases</h1>
{% if message %}
  <p class="{{ 'error' if error else 'success' }}">{{ message }}</p>
{% endif %}

<h2>Existing Databases</h2>
<ul>
  {% for d in databases %}
    <li>
      <a href="{{ url_for('view_db', dbname=d) }}">{{ d }}</a>
      <form method="post" action="{{ url_for('drop_database', dbname=d) }}" style="display:inline">
        <button class="btn danger" type="submit">Drop DB</button>
      </form>
    </li>
  {% endfor %}
</ul>

<h3>Create Database</h3>
<form method="post" action="{{ url_for('create_database') }}">
  <div class="form-row"><label for="dbname">Name:</label><input id="dbname" name="dbname"></div>
  <button class="btn primary" type="submit">Create</button>
</form>

<p style="margin-top:1rem"><a class="btn" href="{{ url_for('users_page') }}">Back to users</a></p>
"""


# fragment for edit page
EDIT_TEMPLATE = """
<h1>Edit Row</h1>
{% if message %}
  <p class="{{ 'error' if error else 'success' }}">{{ message }}</p>
{% endif %}
<form method="post" action="{{ action_url }}">
  {% for col in columns %}
    <div class="form-row"><label for="{{ col }}">{{ col|capitalize }}:</label><input id="{{ col }}" name="{{ col }}" value="{{ row.get(col, '') }}"></div>
  {% endfor %}
  <div style="margin-top:8px;">
    <button class="btn" type="submit">Save</button>
    <a class="btn" href="{{ back_url }}">Cancel</a>
  </div>
</form>
"""

@app.route('/users', methods=['GET'])
def users_page():
    # Show the users table (backwards compatible)
    table = db.tables.get('users')
    users = table.rows if table else []
    message = request.args.get('message')
    error = request.args.get('error') == '1'
    content = render_template_string(USERS_TEMPLATE, users=users, message=message, error=error)
    return render_template_string(LAYOUT_TEMPLATE, title='Users', content=content, data_dir=DATA_DIR)


# Landing page redirects to the databases dashboard
@app.route('/', methods=['GET'])
def root():
    return redirect(url_for('databases_page'))


def get_databases_list():
    # databases are subdirectories under DATA_DIR
    try:
        names = [name for name in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, name))]
    except Exception:
        names = []
    return names


@app.route('/databases', methods=['GET'])
def databases_page():
    names = get_databases_list()
    message = request.args.get('message')
    error = request.args.get('error') == '1'
    content = render_template_string(DATABASES_TEMPLATE, databases=names, message=message, error=error)
    return render_template_string(LAYOUT_TEMPLATE, title='Databases', content=content, data_dir=DATA_DIR)


@app.route('/databases', methods=['POST'])
def create_database():
    name = request.form.get('dbname')
    if not name or '/' in name or '..' in name:
        return redirect(url_for('databases_page', message='Invalid database name', error=1))
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        return redirect(url_for('databases_page', message='Database already exists', error=1))
    os.makedirs(path, exist_ok=True)
    return redirect(url_for('databases_page', message='Database created'))


@app.route('/databases/<dbname>/drop', methods=['POST'])
def drop_database(dbname):
    path = os.path.join(DATA_DIR, dbname)
    if not os.path.isdir(path):
        return redirect(url_for('databases_page', message='Database not found', error=1))
    shutil.rmtree(path)
    # remove instance if loaded
    db_instances.pop(dbname, None)
    return redirect(url_for('databases_page', message='Database dropped'))


DB_VIEW_TEMPLATE = """
<h1>Database: {{ dbname }}</h1>
{% if message %}<p class="{{ 'error' if error else 'success' }}">{{ message }}</p>{% endif %}

<h3>Tables</h3>
<ul>
  {% for t in tables %}
    <li>
      <a href="{{ url_for('view_table', dbname=dbname, table=t) }}">{{ t }}</a>
      <form method="post" action="{{ url_for('drop_table', dbname=dbname, table=t) }}" style="display:inline">
        <button class="btn danger" type="submit">Drop</button>
      </form>
    </li>
  {% endfor %}
</ul>

<h3>Create Table</h3>
<form method="post" action="{{ url_for('create_table', dbname=dbname) }}">
  <div class="form-row"><label for="tname">Name:</label><input id="tname" name="tname"></div>
  <div class="form-row"><label for="cols">Columns (comma separated):</label><input id="cols" name="cols"></div>
  <div class="form-row"><label for="pk">Primary key (optional):</label><input id="pk" name="pk"></div>
  <div class="form-row"><label for="uniques">Unique keys (comma sep):</label><input id="uniques" name="uniques"></div>
  <button class="btn primary" type="submit">Create Table</button>
</form>
<p style="margin-top:1rem"><a class="btn" href="{{ url_for('databases_page') }}">Back to databases</a></p>
"""

@app.route('/db/<dbname>', methods=['GET'])
def view_db(dbname):
    path = os.path.join(DATA_DIR, dbname)
    if not os.path.isdir(path):
        return f"Database {dbname} not found", 404
    tables = [f[:-5] for f in os.listdir(path) if f.endswith('.json')]
    message = request.args.get('message')
    error = request.args.get('error') == '1'
    content = render_template_string(DB_VIEW_TEMPLATE, dbname=dbname, tables=tables, message=message, error=error)
    return render_template_string(LAYOUT_TEMPLATE, title=f"DB: {dbname}", content=content, data_dir=os.path.join(DATA_DIR, dbname))


@app.route('/db/<dbname>/tables/create', methods=['POST'])
def create_table(dbname):
    d = get_db_instance(dbname)
    tname = request.form.get('tname')
    cols = [c.strip() for c in request.form.get('cols', '').split(',') if c.strip()]
    pk = request.form.get('pk') or None
    uniques = [u.strip() for u in request.form.get('uniques', '').split(',') if u.strip()]
    try:
        d.create_table(tname, cols, pk, uniques)
        # save immediately
        d.save(tname, base_dir=os.path.join(DATA_DIR, dbname))
        return redirect(url_for('view_db', dbname=dbname, message='Table created'))
    except Exception as e:
        return redirect(url_for('view_db', dbname=dbname, message=str(e), error=1))


@app.route('/db/<dbname>/tables/<table>/drop', methods=['POST'])
def drop_table(dbname, table):
    d = get_db_instance(dbname)
    try:
        d.drop_table(table, base_dir=os.path.join(DATA_DIR, dbname))
        return redirect(url_for('view_db', dbname=dbname, message='Table dropped'))
    except Exception as e:
        return redirect(url_for('view_db', dbname=dbname, message=str(e), error=1))


TABLE_TEMPLATE = """
<h1>DB: {{ dbname }} / Table: {{ table }}</h1>
{% if message %}<p class="{{ 'error' if error else 'success' }}">{{ message }}</p>{% endif %}
<table>
  <thead>
    <tr>
      {% for c in columns %}<th>{{ c }}</th>{% endfor %}
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {% for r in rows %}
      <tr>
        {% for c in columns %}<td>{{ r.get(c) }}</td>{% endfor %}
        <td>
          <a class="btn" href="{{ url_for('edit_row', dbname=dbname, table=table, pk=r.get(primary_key) if primary_key else '') }}">Edit</a>
          <form method="post" action="{{ url_for('delete_row', dbname=dbname, table=table) }}" style="display:inline">
            <input type="hidden" name="pk" value="{{ r.get(primary_key) if primary_key else '' }}">
            <button class="btn danger" type="submit">Delete</button>
          </form>
        </td>
      </tr>
    {% endfor %}
  </tbody>
</table>

<h3>Add Row</h3>
<form method="post" action="{{ url_for('create_row', dbname=dbname, table=table) }}">
  {% for c in columns %}
    <div class="form-row"><label for="{{ c }}">{{ c }}:</label><input id="{{ c }}" name="{{ c }}"></div>
  {% endfor %}
  <button class="btn primary" type="submit">Add Row</button>
</form>
<p style="margin-top:1rem"><a class="btn" href="{{ url_for('view_db', dbname=dbname) }}">Back to DB</a></p>
"""


@app.route('/db/<dbname>/tables/<table>', methods=['GET'])
def view_table(dbname, table):
    d = get_db_instance(dbname)
    try:
        d.load(table, base_dir=os.path.join(DATA_DIR, dbname))
    except Exception:
        # if it's already loaded, ignore
        pass
    if table not in d.tables:
        return "Table not found", 404
    t = d.tables[table]
    rows = t.rows
    message = request.args.get('message')
    error = request.args.get('error') == '1'

    content = render_template_string(TABLE_TEMPLATE, dbname=dbname, table=table, columns=t.columns, rows=rows, primary_key=t.primary_key, message=message, error=error)
    return render_template_string(LAYOUT_TEMPLATE, title=f"Table: {table}", content=content, data_dir=os.path.join(DATA_DIR, dbname))


@app.route('/users', methods=['POST'])
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
        return redirect(url_for('users_page', message='User added'))
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
    # render edit template expecting a generic 'row' variable
    content = render_template_string(EDIT_TEMPLATE, row=user, columns=table.columns, action_url=url_for('update', id=id), back_url=url_for('users_page'), message=message, error=error)
    return render_template_string(LAYOUT_TEMPLATE, title='Edit User', content=content, data_dir=DATA_DIR)


# generic row edit for a table in a named database
@app.route('/db/<dbname>/tables/<table>/edit/<pk>', methods=['GET'])
def edit_row(dbname, table, pk):
    d = get_db_instance(dbname)
    try:
        d.load(table, base_dir=os.path.join(DATA_DIR, dbname))
    except Exception:
        pass
    if table not in d.tables:
        return "Table not found", 404
    t = d.tables[table]
    row = next((r for r in t.rows if (t.primary_key and r.get(t.primary_key) == pk)), None)
    if not row:
        return "Row not found", 404
    content = render_template_string(EDIT_TEMPLATE, row=row, columns=t.columns, action_url=url_for('update_row', dbname=dbname, table=table, pk=pk), back_url=url_for('view_table', dbname=dbname, table=table))
    return render_template_string(LAYOUT_TEMPLATE, title=f'Edit {table}', content=content, data_dir=os.path.join(DATA_DIR, dbname))

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
        return redirect(url_for('users_page', message='User updated'))
    except ValueError as e:
        # return to edit page with error message
        return redirect(url_for('edit', id=id, message=str(e), error=1))


@app.route('/db/<dbname>/tables/<table>/update/<pk>', methods=['POST'])
def update_row(dbname, table, pk):
    d = get_db_instance(dbname)
    if table not in d.tables:
        try:
            d.load(table, base_dir=os.path.join(DATA_DIR, dbname))
        except Exception:
            return "Table not found", 404
    t = d.tables[table]
    updates = {c: request.form.get(c) for c in t.columns}
    try:
        t.update((t.primary_key or t.columns[0], pk), updates)
        d.save(t.name, base_dir=os.path.join(DATA_DIR, dbname))
        return redirect(url_for('view_table', dbname=dbname, table=table, message='Row updated'))
    except ValueError as e:
        return redirect(url_for('edit_row', dbname=dbname, table=table, pk=pk, message=str(e), error=1))

@app.route('/delete/<id>', methods=['POST'])
def delete(id):
    table = db.tables.get('users')
    if not table:
        return "Users table not found", 500
    table.delete(('id', id))
    db.save('users')
    return redirect(url_for('users_page', message='User deleted'))


@app.route('/db/<dbname>/tables/<table>/create_row', methods=['POST'])
def create_row(dbname, table):
    d = get_db_instance(dbname)
    if table not in d.tables:
        try:
            d.load(table, base_dir=os.path.join(DATA_DIR, dbname))
        except Exception:
            return "Table not found", 404
    t = d.tables[table]
    record = {c: request.form.get(c) for c in t.columns}
    try:
        t.insert(record)
        d.save(t.name, base_dir=os.path.join(DATA_DIR, dbname))
        return redirect(url_for('view_table', dbname=dbname, table=table, message='Row added'))
    except ValueError as e:
        return redirect(url_for('view_table', dbname=dbname, table=table, message=str(e), error=1))


@app.route('/db/<dbname>/tables/<table>/delete', methods=['POST'])
def delete_row(dbname, table):
    d = get_db_instance(dbname)
    if table not in d.tables:
        try:
            d.load(table, base_dir=os.path.join(DATA_DIR, dbname))
        except Exception:
            return "Table not found", 404
    t = d.tables[table]
    pk = request.form.get('pk')
    if not pk:
        return redirect(url_for('view_table', dbname=dbname, table=table, message='Missing PK', error=1))
    t.delete((t.primary_key, pk))
    d.save(t.name, base_dir=os.path.join(DATA_DIR, dbname))
    return redirect(url_for('view_table', dbname=dbname, table=table, message='Row deleted'))


if __name__ == '__main__':
    app.run(debug=True)
