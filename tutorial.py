# https://docs.sqlalchemy.org/en/14/tutorial/engine.html
from sqlalchemy import create_engine
engine = create_engine("sqlite+pysqlite:///:memory:", echo=True, future=True)

# SQLAlchemy will lazily initialize the engine

# -----------------------------------------------------------------------------

