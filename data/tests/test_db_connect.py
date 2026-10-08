import importlib
import os
from unittest.mock import MagicMock, patch

import data.db_connect as dbc


def test_drop():
    client = MagicMock()
    with patch.object(dbc, 'client', client):
        dbc.drop('some_collection', db='some_db')
    client['some_db']['some_collection'].drop.assert_called_once_with()


def test_delete_many():
    client = MagicMock()
    coll = client['some_db']['some_collection']
    coll.delete_many.return_value.deleted_count = 3
    with patch.object(dbc, 'client', client):
        assert dbc.delete_many('some_collection', {'a': 1}, db='some_db') == 3
    coll.delete_many.assert_called_once_with({'a': 1})


def reload_with_env(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(dbc.DB_ENV, raising=False)
    else:
        monkeypatch.setenv(dbc.DB_ENV, value)
    importlib.reload(dbc)
    return dbc.SE_DB


def test_db_name_from_env(monkeypatch):
    orig = os.environ.get(dbc.DB_ENV)
    try:
        assert reload_with_env(monkeypatch, 'test_other') == 'test_other'
        assert dbc.create.__defaults__ == ('test_other',)
    finally:
        reload_with_env(monkeypatch, orig)


def test_db_name_default(monkeypatch):
    orig = os.environ.get(dbc.DB_ENV)
    try:
        assert reload_with_env(monkeypatch, None) == dbc.DEFAULT_DB
    finally:
        reload_with_env(monkeypatch, orig)
