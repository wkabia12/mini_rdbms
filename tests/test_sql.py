import sys
import pathlib

# ensure project root is on sys.path so test runner can import local modules
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from sql import parse

def test_parse_valid_queries():
    cases = [
        ("CREATE TABLE users (id, name, email)", ("CREATE", "users", ["id", "name", "email"])),
        ("INSERT INTO users VALUES (1, 'Alice', 'a@example.com')", ("INSERT", "users", ["1", "Alice", "a@example.com"])),
        ("SELECT * FROM users", ("SELECT", "users")),
        ("SELECT * FROM users WHERE id = 1", ("SELECT", "users", ("id", "1"))),
        ("DELETE FROM users WHERE id = 1", ("DELETE", "users", ("id", "1"))),
        ("DROP TABLE users", ("DROP", "users")),
    ]

    for q, expected in cases:
        assert parse(q) == expected


def test_parse_invalid_queries():
    bad = ["", "CREATE users", "INSERT users 1,2,3", "SELECT users"]
    for q in bad:
        with pytest.raises(ValueError):
            parse(q)
