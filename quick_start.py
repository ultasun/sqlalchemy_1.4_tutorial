# "Declare Models"

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "user_account"

    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    fullname = Column(String)

    addresses = relationship(
        "Address", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"

class Address(Base):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("user_account.id"), nullable=False)

    user = relationship("User", back_populates="addresses")

    def __repr__(self):
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"

# "Create an Engine"
from sqlalchemy import create_engine
engine = create_engine("sqlite://", echo=True, future=True)

# Emit CREATE TABLE DDL
Base.metadata.create_all(engine)

# Create Objects and Persist
from sqlalchemy.orm import Session

with Session(engine) as session: # with is important to close out session 
    spongebob = User(
        name="spongebob",
        fullname="Spongebob Squarepants",
        addresses=[Address(email_address="spongebob@bikinibottom.net")],
    )
    sandy = User(
        name="sandy",
        fullname="Sandy Cheeks",
        addresses=[
            Address(email_address="sandy@bikinibottom.net"),
            Address(email_address="sandy@squirrelpower.org"),
        ],
    )
    patrick = User(name="patrick", fullname="Patrick Star")

    session.add_all([spongebob, sandy, patrick])

    session.commit()

# Simple SELECT
from sqlalchemy import select
session = Session(engine)
stmt = select(User).where(User.name.in_(["spongebob", "sandy"]))
for user in session.scalars(stmt):
    print(user)

# SELECT with JOIN
stmt = (
    select(Address)
    .join(Address.user)
    .where(User.name == "sandy")
    .where(Address.email_address == "sandy@bikinibottom.net")
)
sandy_address = session.scalars(stmt).one()
sandy_address

# Make Changes
stmt = select(User).where(User.name == "patrick")
patrick = session.scalars(stmt).one()
# ...SQL output...
patrick.addresses.append(Address(email_address="patrickstar@bikinibottom.net"))
# ...SQL output...
sandy_address.email_address = "sandy_cheeks@bikinibottom.net"
session.commit()
# ...SQL output...

# Some Deletes
sandy = session.get(User, 2)
sandy.addresses.remove(sandy_address)
session.flush()
session.delete(patrick)
session.commit()

