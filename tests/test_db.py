import os
import importlib
import sys
import pathlib

# ensure project root is on sys.path so test runner can import local modules
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

import db as db_mod
from db import Database


def setup_db(tmp_path):
    # isolate DATA_DIR for tests
    path = tmp_path / "data"
    path.mkdir()
    db_mod.DATA_DIR = str(path)
    return Database()


def test_insert_and_constraints(tmp_path):
    db = setup_db(tmp_path)
    db.create_table("users", ["id", "name", "email"], pk="id", uniques=["email"])
    t = db.tables["users"]

    # basic insert
    t.insert({"id": "1", "name": "Alice", "email": "a@example.com"})
    assert len(t.rows) == 1

    # duplicate pk
    with pytest.raises(ValueError):
        t.insert({"id": "1", "name": "Bob", "email": "b@example.com"})

    # duplicate unique
    with pytest.raises(ValueError):
        t.insert({"id": "2", "name": "Eve", "email": "a@example.com"})

    # missing column
    with pytest.raises(ValueError):
        t.insert({"id": "3", "name": "NoEmail"})

    # extra column
    with pytest.raises(ValueError):
        t.insert({"id": "4", "name": "X", "email": "x@e.com", "age": 30})


def test_update_constraints(tmp_path):
    db = setup_db(tmp_path)
    db.create_table("users", ["id", "name", "email"], pk="id", uniques=["email"])
    t = db.tables["users"]

    t.insert({"id": "1", "name": "A", "email": "a@example.com"})
    t.insert({"id": "2", "name": "B", "email": "b@example.com"})

    # updating to duplicate unique value
    with pytest.raises(ValueError):
        t.update(("id", "2"), {"email": "a@example.com"})

    # updating primary key to duplicate
    with pytest.raises(ValueError):
        t.update(("id", "2"), {"id": "1"})

    # unknown column in update
    with pytest.raises(ValueError):
        t.update(("id", "1"), {"age": 30})


def test_delete_and_select(tmp_path):
    db = setup_db(tmp_path)
    db.create_table("items", ["id", "value"], pk="id")
    t = db.tables["items"]

    t.insert({"id": "1", "value": "v1"})
    t.insert({"id": "2", "value": "v2"})

    assert len(t.select()) == 2
    assert t.select(("id", "1")) == [{"id": "1", "value": "v1"}]

    t.delete(("id", "1"))
    assert t.select() == [{"id": "2", "value": "v2"}]


def test_save_and_load(tmp_path):
    db = setup_db(tmp_path)
    db.create_table("users", ["id", "name", "email"], pk="id", uniques=["email"])
    t = db.tables["users"]
    t.insert({"id": "1", "name": "A", "email": "a@example.com"})

    db.save("users")

    db2 = Database()
    db2.load("users")
    assert "users" in db2.tables
    assert db2.tables["users"].rows == t.rows


def test_create_table_if_not_exists(tmp_path):
    db = setup_db(tmp_path)
    db.create_table("u", ["id"], pk="id")
    # creating again without flag should raise
    with pytest.raises(ValueError):
        db.create_table("u", ["id"], pk="id")
    # with flag should be OK
    db.create_table("u", ["id"], pk="id", if_not_exists=True)
