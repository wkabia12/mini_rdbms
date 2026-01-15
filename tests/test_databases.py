import sys
import os
import pathlib
import importlib
import pytest

# ensure project root on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import db as db_mod


def test_database_and_table_crud(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(db_mod, 'DATA_DIR', str(data_dir))

    # reload webapp so it picks up changed DATA_DIR
    sys.modules.pop('webapp', None)
    import webapp

    client = webapp.app.test_client()

    # create a new database
    rv = client.post('/databases', data={'dbname': 'shop'})
    assert rv.status_code in (302, 303)

    # view database page
    rv = client.get('/db/shop')
    assert rv.status_code == 200

    # create a table
    rv = client.post('/db/shop/tables/create', data={'tname': 'products', 'cols': 'id, name, price', 'pk': 'id', 'uniques': ''})
    assert rv.status_code in (302, 303)

    # add a row
    rv = client.post('/db/shop/tables/products/create_row', data={'id': 'p1', 'name': 'Phone', 'price': '199'})
    assert rv.status_code in (302, 303)

    # view table and ensure the row appears
    rv = client.get('/db/shop/tables/products')
    txt = rv.get_data(as_text=True)
    assert 'Phone' in txt

    # edit row
    rv = client.post('/db/shop/tables/products/update/p1', data={'id':'p1', 'name':'Phone X', 'price':'249'})
    assert rv.status_code in (302, 303)
    rv = client.get('/db/shop/tables/products')
    assert 'Phone X' in rv.get_data(as_text=True)

    # delete row
    rv = client.post('/db/shop/tables/products/delete', data={'pk':'p1'})
    assert rv.status_code in (302, 303)
    rv = client.get('/db/shop/tables/products')
    assert 'Phone X' not in rv.get_data(as_text=True)

    # drop table
    rv = client.post('/db/shop/tables/products/drop')
    assert rv.status_code in (302, 303)
    rv = client.get('/db/shop')
    assert 'products' not in rv.get_data(as_text=True)

    # drop database
    rv = client.post('/databases/shop/drop')
    assert rv.status_code in (302, 303)
    rv = client.get('/databases')
    assert 'shop' not in rv.get_data(as_text=True)
