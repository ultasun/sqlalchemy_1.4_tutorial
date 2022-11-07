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
    
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# working with database metadata

# setting up metadata with table objects
from sqlalchemy import MetaData
metadata_obj = MetaData()

from sqlalchemy import Table, Column, Integer, String
user_table = Table(
    "user_account",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("name", String(30)),
    Column("fullname", String),
)

# declaring simple constraints
from sqlalchemy import ForeignKey
address_table = Table(
    "address",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("user_id", ForeignKey("user_account.id"), nullable=False),
    Column("email_address", String, nullable=False),
)

# emitting DDL to the database
metadata_obj.create_all(engine)

# defining table metadata with the orm

# setting up the Registry
from sqlalchemy.orm import registry
mapper_registry = registry()
Base = mapper_registry.generate_base()

# another alternative
#from sqlalchemy.orm import declarative_base
#Base = declarative_base()

# declaring mapped classes
from sqlalchemy.orm import relationship
class User(Base):
    __tablename__ = "user_account"

    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    fullname = Column(String)

    addresses = relationship("Address", back_populates="user")

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"

class Address(Base):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("user_account.id"))

    user = relationship("User", back_populates="addresses")

    def __repr__(self):
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"

# other mapped class details
sandy = User(name="sandy", fullname="Sandy Cheeks")

# emitting ddl to the database
mapper_registry.metadata.create_all(engine)
Base.metadata.create_all(engine)

# ...

# table reflection
some_table = Table("some_table", metadata_obj, autoload_with=engine)

# -----------------------------------------------------------------------------
# working with data
# https://web.archive.org/web/20220815143402/https://docs.sqlalchemy.org/en/14/tutorial/data.html

# inserting rows with core

# the insert() sql expression construct
from sqlalchemy import insert, select
stmt = insert(user_table).values(name='spongebob', fullname="Spongebob Squarepants")
print(stmt)
compiled = stmt.compile()

with engine.connect() as conn:
    result = conn.execute(stmt)
    conn.commit()

# insert usually generates the "values" clause automatically
with engine.connect() as conn:
    result = conn.execute(
        insert(user_table),
        [
            {"name": "sandy", "fullname": "Sandy Cheeks"},
            {"name": "patrick", "fullname": "Patrick Star"}
        ]
    )
    conn.commit()

# ... skipping the 'Deep Alchemy' section

# insert ... from select
select_stmt = select(user_table.c.id, user_table.c.name + "@aol.com")
insert_stmt = insert(address_table).from_select(
    ["user_id", "email_address"], select_stmt)
print(insert_stmt)

# insert ... returning
insert_stmt = insert(address_table).returning(address_table.c.id, address_table.c.email_address)
print(insert_stmt)

select_stmt = select(user_table.c.id, user_table.c.name + "@aol.com")
insert_stmt = insert(address_table).from_select(
    ["user_id", "email_address"], select_stmt
    )
print(insert_stmt.returning(address_table.c.id, address_table.c.email_address))

# -----------------------------------------------------------------------------
from sqlalchemy import select # this was imported previously
stmt = select(user_table).where(user_table.c.name == "spongebob")
print(stmt)

with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(row)

stmt = select(User).where(User.name == "spongebob")
with Session(engine) as session:
    for row in session.execute(stmt):
        print(row)

# setting the COLUMNS and FROM clause
print(select(user_table))

print(select(user_table.c.name, user_table.c.fullname))

# selecting orm entities and columns

print(select(User))

row = session.execute(select(User)).first()

#row
#row[0]

user = session.scalars(select(User)).first()
print(select(User.name, User.fullname))

row = session.execute(select(User.name, User.fullname)).first()

session.execute(
    select(User.name, Address).where(User.id == Address.user_id).order_by(
        Address.id)
).all()

# selecting from labeled SQL expressions
