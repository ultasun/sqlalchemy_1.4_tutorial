# https://docs.sqlalchemy.org/en/14/tutorial/engine.html
from sqlalchemy import create_engine
engine = create_engine("sqlite+pysqlite:///:memory:", echo=True, future=True)

# SQLAlchemy will lazily initialize the engine

# -----------------------------------------------------------------------------
# https://docs.sqlalchemy.org/en/14/tutorial/dbapi_transactions.html

from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text("select 'hello world everybody'"))
    print(result.all())

# commit as you go
with engine.connect() as conn:
    conn.execute(text("CREATE TABLE some_table (x int, y int)"))
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 1, "y": 1}, {"x": 2, "y": 4}],
        )
    conn.commit()

# begin once
with engine.begin() as conn:
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 6, "y": 8}, {"x": 9, "y": 10}],
        )

# basics of statement execution
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table"))
    for row in result:
        print(f"x: {row.x} y: {row.y}")

# tuple assignment
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table"))
    for x, y in result:
        pass

# integer index
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table"))

    for row in result:
        x = row[0]

# attribute name
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table"))

    for row in result:
        y = row.y

        # illustrate use with Python f-strings
        print(f"Row: {row.x} {y}")

# mapping access
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table"))

    for dict_row in result.mappings():
        x = dict_row["x"]
        y = dict_row["y"]

# sending parameters
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table WHERE y > :y"),
                          {"y": 2})
    for row in result:
        print(f"x: {row.x} y: {row.y}")

# sending multiple parameters
with engine.connect() as conn:
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 11, "y": 12}, {"x": 13, "y": 14}],
        )
    conn.commit()

# executing with an ORM session
from sqlalchemy.orm import Session

stmt = text("SELECT x, y FROM some_table WHERE y > :y ORDER BY x, y")
with Session(engine) as session:
    result = session.execute(stmt, {"y": 6})
    for row in result:
        print(f"x: {row.x} y: {row.y}")

with Session(engine) as session:
    result = session.execute(
        text("UPDATE some_table SET y=:y WHERE x=:x"),
        [{"x": 9, "y": 11}, {"x": 13, "y": 15}],
        )
    session.commit()

