import sys
import os
import importlib
import pathlib

# ensure project root is on sys.path so test runner can import local modules
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

import db as db_mod


def test_webapp_post_and_duplicate(tmp_path, monkeypatch):
    # isolate DATA_DIR and reload webapp so it picks up the new path
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(db_mod, 'DATA_DIR', str(data_dir))

    # Ensure fresh import of webapp
    sys.modules.pop('webapp', None)
    import webapp

    client = webapp.app.test_client()

    # successful insert
    rv = client.post('/users', data={'id': '1', 'name': 'Alice', 'email': 'a@example.com'})
    assert rv.status_code in (302, 303)

    # duplicate email should return 400
    rv = client.post('/users', data={'id': '2', 'name': 'Bob', 'email': 'a@example.com'})
    assert rv.status_code == 400

    # get should show the user
    rv = client.get('/users')
    assert 'Alice' in rv.get_data(as_text=True)
