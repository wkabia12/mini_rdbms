#SQL Like Query Parser

def parse(sql):
    tokens = sql.strip().split()
    cmd = tokens[0].upper()

    if cmd == "CREATE":
        name = tokens[2]
        cols = tokens[3].strip("()").split(",")
        return ("CREATE", name, cols)

    if cmd == "INSERT":
        name = tokens[2]
        values = tokens[4].strip("()").split(",")
        return ("INSERT", name, values)

    if cmd == "SELECT":
        name = tokens[3]
        return ("SELECT", name)

    if cmd == "DELETE":
        name = tokens[2]
        col, val = tokens[4], tokens[6]
        return ("DELETE", name, (col, val))
