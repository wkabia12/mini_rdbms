#SQL Like Query Parser (minimal, safer)

def _strip_quotes(s):
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def parse(sql):
    s = sql.strip()
    if not s:
        raise ValueError("Empty query")
    up = s.upper()

    # CREATE TABLE name (col1, col2)
    if up.startswith("CREATE TABLE"):
        try:
            rest = s[len("CREATE TABLE"):].strip()
            name, cols_part = rest.split("(", 1)
            name = name.strip()
            cols = cols_part.rsplit(")", 1)[0]
            cols_list = [c.strip() for c in cols.split(",") if c.strip()]
            if not name or not cols_list:
                raise ValueError
            return ("CREATE", name, cols_list)
        except Exception:
            raise ValueError("Invalid CREATE syntax. Use: CREATE TABLE name (col1, col2)")

    # INSERT INTO name VALUES (v1, v2)
    if up.startswith("INSERT INTO"):
        try:
            rest = s[len("INSERT INTO"):].strip()
            name_part, vals_part = rest.split("VALUES", 1)
            name = name_part.strip()
            vals = vals_part.strip()
            if not vals.startswith("(") or not vals.endswith(")"):
                raise ValueError
            vals_content = vals[1:-1]
            vals_list = [ _strip_quotes(v.strip()) for v in vals_content.split(",") ]
            return ("INSERT", name, vals_list)
        except Exception:
            raise ValueError("Invalid INSERT syntax. Use: INSERT INTO name VALUES (v1, v2)")

    # SELECT * FROM name [WHERE col = val]
    if up.startswith("SELECT"):
        try:
            # support: SELECT * FROM name WHERE col = val
            parts = s.split()
            if len(parts) < 4 or parts[1] != '*':
                raise ValueError
            if parts[2].upper() != 'FROM':
                raise ValueError
            name = parts[3]
            if 'WHERE' in (p.upper() for p in parts):
                where_idx = next(i for i, p in enumerate(parts) if p.upper() == 'WHERE')
                # simple: WHERE col = val
                if len(parts) <= where_idx + 3 or parts[where_idx + 2] != '=':
                    raise ValueError
                col = parts[where_idx + 1]
                val = _strip_quotes(parts[where_idx + 3] if parts[where_idx + 3] != ';' else parts[where_idx + 4]) if len(parts) > where_idx + 3 else ''
                return ("SELECT", name, (col, _strip_quotes(val)))
            return ("SELECT", name)
        except Exception:
            raise ValueError("Invalid SELECT syntax. Use: SELECT * FROM name [WHERE col = value]")

    # DELETE FROM name WHERE col = val
    if up.startswith("DELETE FROM"):
        try:
            rest = s[len("DELETE FROM"):].strip()
            if 'WHERE' not in rest.upper():
                raise ValueError
            name_part, where_part = rest.split('WHERE', 1)
            name = name_part.strip()
            where_tokens = where_part.strip().split()
            if len(where_tokens) < 3 or where_tokens[1] != '=':
                raise ValueError
            col = where_tokens[0]
            val = _strip_quotes(where_tokens[2])
            return ("DELETE", name, (col, val))
        except Exception:
            raise ValueError("Invalid DELETE syntax. Use: DELETE FROM name WHERE col = value")

    # DROP TABLE name
    if up.startswith("DROP TABLE"):
        try:
            name = s[len("DROP TABLE"):].strip()
            if not name:
                raise ValueError
            return ("DROP", name)
        except Exception:
            raise ValueError("Invalid DROP syntax. Use: DROP TABLE name")

    raise ValueError("Unsupported or invalid SQL statement")

