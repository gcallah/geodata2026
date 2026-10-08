from unittest.mock import MagicMock, patch

import data.db_connect as dbc


def test_drop():
    client = MagicMock()
    with patch.object(dbc, 'client', client):
        dbc.drop('some_collection', db='some_db')
    client['some_db']['some_collection'].drop.assert_called_once_with()
