import uuid

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from shared_utils.database.postgres_database import Base


class TableMixin(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    created_datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_datetime = Column(DateTime(timezone=True), onupdate=func.now())


user_usergroups = Table(
    "user_usergroups",
    Base.metadata,
    Column("group_id", ForeignKey("usergroup.id"), primary_key=True),
    Column("user_id", ForeignKey("user.id"), primary_key=True),
)



class Item(TableMixin, Base):
    name = Column(String, nullable=False)
    custom_attribute = Column(Integer, nullable=True, default=None)

    user_id = Column(UUID, ForeignKey("user.id"))
    user = relationship("User", back_populates="items")


class User(TableMixin, Base):
    email = Column(String)
    
    groups = relationship("UserGroup", secondary="user_usergroups", back_populates="users")
    
    items = relationship("Item", back_populates="user")


class UserGroup(TableMixin, Base):
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    users = relationship("User", secondary="user_usergroups", back_populates="groups")
