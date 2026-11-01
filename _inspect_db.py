import sqlite3

c = sqlite3.connect(r"H:\Desktop\CRUD\dimensao_logus_interno.db")
c.row_factory = sqlite3.Row
cur = c.cursor()
print("tables:", [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")])
for r in cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'"):
    print("---", r[0])
    print(r[1])
try:
    n = cur.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0]
    print("count:", n)
    for row in cur.execute("SELECT * FROM matriculas"):
        print(dict(row))
except Exception as e:
    print("err", e)
c.close()
