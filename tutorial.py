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
            {"name": "patrick", "fullname": "Patrick Star"},
            {"name": "squidward", "fullname": "Squidward T"}
        ]
    )
    conn.commit()

# slightly deeper alchemy
from sqlalchemy import select, bindparam
scalar_subq = (
    select(user_table.c.id)
    .where(user_table.c.name == bindparam("username"))
    .scalar_subquery()
)

with engine.connect() as conn:
    result = conn.execute(
        insert(address_table).values(user_id=scalar_subq),
        [
            {"username": "spongebob",
             "email_address": "spongebob@bikinibottom.net"},
            {"username": "sandy",
             "email_address": "sandy@bikinibottom.net"},
            {"username": "sandy",
             "email_address": "sandy@squirrelpower.org"}
        ],
    )
    conn.commit()

# insert ... from select
select_stmt = select(user_table.c.id, user_table.c.name + "@aol.com")
insert_stmt = insert(address_table).from_select(
    ["user_id", "email_address"], select_stmt)
print(insert_stmt)

# insert ... returning
insert_stmt = insert(address_table).returning(
    address_table.c.id, address_table.c.email_address)
print(insert_stmt)

select_stmt = select(user_table.c.id, user_table.c.name + "@aol.com")
insert_stmt = insert(address_table).from_select(
    ["user_id", "email_address"], select_stmt)

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
from sqlalchemy import func, cast
stmt = select(
    ("username: " + user_table.c.name).label("username"),
    ).order_by(user_table.c.name)
with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(f"{row.username}")

# selecting with textual column expressions
from sqlalchemy import text
stmt = select(text("'some phrase'"), user_table.c.name).order_by(user_table.c.name)
with engine.connect() as conn:
    print(conn.execute(stmt).all())

from sqlalchemy import literal_column
stmt = select(literal_column("'some phrase'").label("p"),
              user_table.c.name).order_by(user_table.c.name)
with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(f"{row.p}, {row.name}")

# the where clause
print(user_table.c.name == "squidward")

print(address_table.c.user_id > 10)

print(select(user_table).where(user_table.c.name == "squidward"))

print(
    select(address_table.c.email_address)
    .where(user_table.c.name == "squidward")
    .where(address_table.c.user_id == user_table.c.id)
)

print(
    select(address_table.c.email_address).where(
        user_table.c.name == "squidward",
        address_table.c.user_id == user_table.c.id
    )
)

# "and" and "or" conjunctions are both available directly using and_() and or_()
# functions, illustrated below in terms of ORM entities:
from sqlalchemy import and_, or_
print(
    select(Address.email_address).where(
        and_(
            or_(User.name == "squidward", User.name == "sandy"),
            Address.user_id == User.id,
        )
    )
)

# filter_by()
print(
    select(User).filter_by(name="spongebob", fullname="Spongebob Squarepants")
)

# explicit FROM clauses and JOINs
print(select(user_table.c.name))
print(select(user_table.c.name, address_table.c.email_address))

# two ways are available to join the previous two tables:

# Select.join_from() allows to indicate the left and right side of the JOIN
print(
    select(user_table.c.name, address_table.c.email_address).join_from(
        user_table, address_table
    )
)

# Select.join() indicates only the right side of the JOIN
print(
    select(user_table.c.name, address_table.c.email_address)
    .join(address_table)
)

# Select.select_from()
print(
    select(address_table.c.email_address)
    .select_from(user_table).join(address_table)
)

# to SELECT from the common SQL expression COUNT(), use a SQLAlchemy element
# known as `sqlalchemy.sql.expression.func` to produce the SQL COUNT() function
from sqlalchemy import func
print(select(func.count("*")).select_from(user_table))

# setting the ON clause
print(
    select(address_table.c.email_address)
    .select_from(user_table)
    .join(address_table, user_table.c.id == address_table.c.user_id)
)

# OUTER and FULL join
print(
    select(user_table).join(address_table, isouter=True)
)

print(
    select(user_table).join(address_table, full=True)
)

# SQL also has a 'RIGHT OUTER JOIN' but SQLAlchemy doesn't render this directly,
# instead, reverse the order of the tables and use 'LEFT OUTER JOIN'

# ORDER BY, GROUP BY, HAVING

# ORDER BY
print(select(user_table).order_by(user_table.c.name))

# ascending / descending is available from ColumnElement.asc() and
# ColumnElement.desc()
print(select(User).order_by(User.fullname.desc()))

# Aggregate functions with GROUP BY / HAVING
from sqlalchemy import func
count_fn = func.count(user_table.c.id)
print(count_fn)

with engine.connect() as conn:
    result = conn.execute(
        select(User.name, func.count(Address.id).label("count"))
        .join(Address)
        .group_by(User.name)
        .having(func.count(Address.id) > 1)
    )
    print(result.all())

# ordering or grouping by a label
from sqlalchemy import func, desc
stmt = (
    select(Address.user_id, func.count(Address.id).label("num_addresses"))
    .group_by("user_id")
    .order_by("user_id", desc("num_addresses"))
)
print(stmt)

# using aliases
user_alias_1 = user_table.alias()
user_alias_2 = user_table.alias()
print(
    select(user_alias_1.c.name, user_alias_2.c.name).join_from(
        user_alias_1, user_alias_2, user_alias_1.c.id > user_alias_2.c.id
    )
)

# ORM entity aliases
from sqlalchemy.orm import aliased
address_alias_1 = aliased(Address)
address_alias_2 = aliased(Address)
print(
    select(User)
    .join_from(User, address_alias_1)
    .where(address_alias_1.email_address == "patrick@aol.com")
    .join_from(User, address_alias_2)
    .where(address_alias_2.email_address == "patrick@gmail.com")
)

# subqueries and CTEs
subq = (
    select(func.count(address_table.c.id).label("count"), address_table.c.user_id)
    .group_by(address_table.c.user_id)
    .subquery()
)
print(subq)
print(select(subq.c.user_id, subq.c.count))
stmt = select(user_table.c.name, user_table.c.fullname, subq.c.count).join_from(user_table, subq)
print(stmt)

# Common Table Expressions (CTEs)
subq = (
    select(func.count(address_table.c.id).label("count"), address_table.c.user_id)
    .group_by(address_table.c.user_id)
    .cte()
)
stmt = select(user_table.c.name, user_table.c.fullname, subq.c.count).join_from(
    user_table, subq
)

print(stmt)

# ORM entity subqueries/CTEs
subq = select(Address).where(~Address.email_address.like("%.net")).subquery()
address_subq = aliased(Address, subq)
stmt = (
    select(User, address_subq)
    .join_from(User, address_subq)
    .order_by(User.id, address_subq.id)
)
with Session(engine) as session:
    for user, address in session.execute(stmt):
        print(f"{user} {address}")

# same goal as above, using CTE to achieve
cte_obj = select(Address).where(~Address.email_address.like("%.net")).cte()
address_cte = aliased(Address, cte_obj)
stmt = (
    select(User, address_cte)
    .join_from(User, address_cte)
    .order_by(User.id, address_cte.id)
)
with Session(engine) as session:
    for user, address in session.execute(stmt):
        print(f"{user} {address}")

# scalar and correlated subqueries
subq = (
    select(func.count(address_table.c.id))
    .where(user_table.c.id == address_table.c.user_id)
    .scalar_subquery()
)
print(subq)
print(subq == 5)
stmt = select(user_table.c.name, subq.label("address_count"))
print(stmt)

stmt = (
    select(
        user_table.c.name, address_table.c.email_address, subq.label("address_count")
    )
    .join_from(user_table, address_table)
    .order_by(user_table.c.id, address_table.c.id)
)
try: # this next statement will fail because the statement is too ambiguous
    print(stmt)
except:
    pass

# a more specific query
subq = (
    select(func.count(address_table.c.id))
    .where(user_table.c.id == address_table.c.user_id)
    .scalar_subquery()
    .correlate(user_table)
)

# no more ambiguity,
# the statement then can return the data for this column like any other:
with engine.connect() as conn:
    result = conn.execute(
        select(
            user_table.c.name,
            address_table.c.email_address,
            subq.label("address_count"),
        )
        .join_from(user_table, address_table)
        .order_by(user_table.c.id, address_table.c.id)
    )
    print(result.all())

# LATERAL correlation
print("LATERAL correlation")
subq = (
    select(
        func.count(address_table.c.id).label("address_count"),
        address_table.c.email_address,
        address_table.c.user_id,
    )
    .where(user_table.c.id == address_table.c.user_id)
    .lateral()
)
stmt = (
    select(user_table.c.name, subq.c.address_count, subq.c.email_address)
    .join_from(user_table, subq)
    .order_by(user_table.c.id, subq.c.email_address)
)
print(stmt)

# UNION, UNION ALL and other set operations
from sqlalchemy import union_all
stmt1 = select(user_table).where(user_table.c.name == "sandy")
stmt2 = select(user_table).where(user_table.c.name == "spongebob")
u = union_all(stmt1, stmt2)
with engine.connect() as conn:
    result = conn.execute(u)
    print(result.all())

u_subq = u.subquery()
stmt = (
    select(u_subq.c.name, address_table.c.email_address)
    .join_from(address_table, u_subq)
    .order_by(u_subq.c.name, address_table.c.email_address)
)
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())

# selecting ORM entities from Unions
stmt1 = select(User).where(User.name == "sandy")
stmt2 = select(User).where(User.name == "spongebob")
u = union_all(stmt1, stmt2)

orm_stmt = select(User).from_statement(u)
with Session(engine) as session:
    for obj in session.execute(orm_stmt).scalars():
        print(obj)

user_alias = aliased(User, u.subquery())
orm_stmt = select(user_alias).order_by(user_alias.id)
with Session(engine) as session:
    for obj in session.execute(orm_stmt).scalars():
        print(obj)

# EXISTS subqueries
subq = (
    select(func.count(address_table.c.id))
    .where(user_table.c.id == address_table.c.user_id)
    .group_by(address_table.c.user_id)
    .having(func.count(address_table.c.id) > 1)
).exists()
with engine.connect() as conn:
    result = conn.execute(select(user_table.c.name).where(subq))
    print(result.all())
# NOT EXISTS
subq = (
    select(address_table.c.id).where(
        user_table.c.id == address_table.c.user_id)
).exists()

with engine.connect() as conn:
    result = conn.execute(select(user_table.c.name).where(~subq))
    print(result.all())

# working with SQL functions

# the count() function, an aggregate function which counts how many rows 
print(select(func.count()).select_from(user_table))

# the lower() function, a string function that converts a string to lower case
print(select(func.lower("A String WITH Much UPPERCASE")))

# the now() function, provides current date and time
stmt = select(func.now())
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())

# func tries to be as liberal as possible in what it accepts.

print(select(func.some_crazy_function(user_table.c.name, 17)))

from sqlalchemy.dialects import postgresql
print(select(func.now()).compile(dialect=postgresql.dialect()))

from sqlalchemy.dialects import oracle
print(select(func.now()).compile(dialect=oracle.dialect()))

# functions have return types
func.now().type
from sqlalchemy import JSON
function_expr = func.json_object('{a, 1, b, "def", c, 3.5}', type_=JSON)

stmt = select(function_expr["def"])
print(stmt)

# built-in functions have pre-configured return types
m1 = func.max(Column("some_int", Integer))
m1.type
m2 = func.max(Column("some_str", String))
m2.type
func.now().type
func.current_date().type
func.concat("x", "y").type
func.upper("lowercase").type
print(select(func.upper("lowercase") + " suffix"))
func.count().type
func.json_object('{"a", "b"}').type

# advanced sql function techniques

# using window functions
stmt = (
    select(
        func.row_number().over(partition_by=user_table.c.name),
        user_table.c.name,
        address_table.c.email_address,
    )
    .select_from(user_table)
    .join(address_table)
)
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())

# above, the partition_by parameter is used so that the 'PARTITION BY' clause
# is rendered within the 'OVER' clause; we also may make use of the 'ORDER BY'
# clause using order_by:
stmt = (
    select(
        func.count().over(order_by=user_table.c.name),
        user_table.c.name,
        address_table.c.email_address,
    )
    .select_from(user_table)
    .join(address_table)
)
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())

# FunctionElement.over() only applies to SQL aggregate functions. SQLAlchemy
# will emit it, but the database could reject the expression if used incorrectly

# special modifiers WITHIN GROUP, FILTER

print(
    func.unnest(
        func.percentile_disc([0.25, 0.5, 0.75, 1]).within_group(user_table.c.name)
    )
)

stmt = (
    select(
        func.count(address_table.c.email_address).filter(user_table.c.name == "sandy"),
        func.count(address_table.c.email_address).filter(
            user_table.c.name == "spongebob"
        ),
    )
    .select_from(user_table)
    .join(address_table)
)

with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())

onetwothree = func.json_each('["one", "two", "three"]').table_valued("value")
stmt = select(onetwothree).where(onetwothree.c.value.in_(["two", "three"]))
with engine.connect() as conn:
    result = conn.execute(stmt)
    result.all()

# column valued functions - table valued function as a scalar column
from sqlalchemy import select, func
stmt = select(func.json_array_elements('["one", "two"').column_valued("x"))
print(stmt)

from sqlalchemy.dialects import oracle
stmt = select(func.scalar_strings(5).column_valued("s"))
print(stmt.compile(dialect=oracle.dialect()))

# data casts and type coercion
from sqlalchemy import cast
stmt = select(cast(user_table.c.id, String))
with engine.connect() as conn:
    result = conn.execute(stmt)
    result.all()

from sqlalchemy import JSON
print(cast("{'a': 'b'}", JSON)["a"])

# type_coerce() - a Python-only "cast"

import json
from sqlalchemy import JSON
from sqlalchemy import type_coerce
from sqlalchemy.dialects import mysql
s = select(type_coerce({"some_key": {"foo": "bar"}}, JSON)["some_key"])
print(s.compile(dialect=mysql.dialect()))

# updating and deleting rows with core

# the update() SQL expression construct
from sqlalchemy import update
stmt = (
    update(user_table)
    .where(user_table.c.name == "patrick")
    .values(fullname="Patrick Star")
)
print(stmt)

stmt = update(user_table).values(fullname="Username: " + user_table.c.name)
print(stmt)

# supporting updates in an 'executemany' context
from sqlalchemy import bindparam
stmt = (
    update(user_table)
    .where(user_table.c.name == bindparam("oldname"))
    .values(name=bindparam("newname"))
)
with engine.begin() as conn:
    conn.execute(
        stmt,
        [
            {"oldname": "jack", "newname": "ed"},
            {"oldname": "wendy", "newname": "mary"},
            {"oldname": "jim", "newname": "james"},
        ],
    )

# correlated updates
scalar_subq = (
    select(address_table.c.email_address)
    .where(address_table.c.user_id == user_table.c.id)
    .order_by(address_table.c.id)
    .limit(1)
    .scalar_subquery()
)
update_stmt = update(user_table).values(fullname=scalar_subq)
print(update_stmt)

# UPDATE..FROM
# sqlalchemy automatically determines FROM clauses for postgres/mysql
update_stmt = (
    update(user_table)
    .where(user_table.c.id == address_table.c.user_id)
    .where(address_table.c.email_address == "patrick@aol.com")
    .values(fullname="Pat")
)
print(update_stmt)

# there is a mysql specific syntax to update multiple tables
# (what happens if not using mysql?)
update_stmt = (
    update(user_table)
    .where(user_table.c.id == address_table.c.user_id)
    .where(address_table.c.email_address == "patrick@aol.com")
    .values(
        {
            user_table.c.fullname: "Patrix",
            address_table.c.email_address: "patrick@bikinibottom.net"
        }
    )
)
from sqlalchemy.dialects import mysql
print(update_stmt.compile(dialect=mysql.dialect()))
      
# parameter ordered updates
update_stmt = update(some_table).ordered_values(
    (some_table.c.y, 20), (some_table.c.x, some_table.c.y + 10)
)
print(update_stmt)

# the delete() SQL expression construct
from sqlalchemy import delete
stmt = delete(user_table).where(user_table.c.name == "patrick")
print(stmt)

# multiple table deletes
delete_stmt = (
    delete(user_table)
    .where(user_table.c.id == address_table.c.user_id)
    .where(address_table.c.email_address == "patrick@aol.com")
)
from sqlalchemy.dialects import mysql
print(delete_stmt.compile(dialect=mysql.dialect()))

# getting affected row count from UPDATE, DELETE
with engine.begin() as conn:
    result = conn.execute(
        update(user_table)
        .values(fullname="Patrick McStar")
        .where(user_table.c.name == "patrick")
    )
    print(result.rowcount)

# using RETURNING with UPDATE, DELETE
update_stmt = (
    update(user_table)
    .where(user_table.c.name == "patrick")
    .values(fullname="Patrick MuhStar")
    .returning(user_table.c.id, user_table.c.name)
)
print(update_stmt)

delete_stmt = (
    delete(user_table)
    .where(user_table.c.name == "patrick")
    .returning(user_table.c.id, user_table.c.name)
)
print(delete_stmt)

# -----------------------------------------------------------------------------
# data manipulation with the ORM

# this section will build out the lifecycle of the Session and how it interacts
# with these constructs

# inserting rows with the ORM

# instruct the Session object to emit INSERT statements by adding objects to it

# instances of classes represent rows
squidward = User(name="squidward", fullname="Squidward Tentacles")
krabs = User(name="ehkrabs", fullname="Eugene H. Krabs")

# adding objects to a session, remember to close this session later
session = Session(engine)
session.add(squidward)
session.add(krabs)
session.new # shows pending objects

# flushing
# the session makes use of a pattern known as unit of work -- accumulating
# changes one at a time, but does not actually communicate them to the database
# until it is needed.
session.flush()

# autogenerated primary key attributes

squidward.id
krabs.id

# when a DBMS is using an autogenerated sequence (AUTOINCREMENT, SERIAL, etc.),
# the autogenerated primary key will not be available from SQLAlchemy until
# flush() or commit() is called.
#
# Some database backends such as psycopg2 can also INSERT many rows at once
# while still being able to retrieve the primary key values.

# getting objects by primary key from the identity map
some_squidward = session.get(User, 4)

# the identity map is a critical feature that allows complex sets of objects to
# be manipulated within a transaction without things getting out of sync.

some_squidward is squidward

# committing
session.commit()
