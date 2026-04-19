from datetime import datetime
from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Extra
from pydantic import Field

"""
Maintain all schemas in this one file, splitting out into multiple files
causes circular and reference dependency issues that pydantic masks
"""



global_model_config = ConfigDict(
    from_attributes=True,  # Use ORM to retrieve objects
    extra=Extra.ignore,  # Ignore any extra values that get passed in when serializing
    use_enum_values=True,  # Use enum values rather than raw enum
)


class ItemBase(BaseModel):
    model_config = global_model_config

    id: UUID
    custom_attribute: int
    name: str
    created_datetime: datetime
    updated_datetime: Optional[datetime]


class ItemCreate(BaseModel):
    user_id: Optional[UUID] = None
    custom_attribute: int
    name: str


class ItemUpdate(ItemCreate):
    id: UUID


class ItemFilter(BaseModel):
    custom_attribute: Optional[int] = None
    name: Optional[str] = None
    user_id: Optional[UUID] = None


class Item(ItemBase):
    user: Optional["UserBase"] = None


class UserGroupBase(BaseModel):
    # Allows pydantic/sqlalchemy to use ORM to pull out related objects instead of just references to them
    model_config = global_model_config

    id: UUID
    created_datetime: datetime
    updated_datetime: Optional[datetime]
    name: str
    description: str


class UserGroupCreate(BaseModel):
    name: str
    description: str
    user_ids: Optional[List[UUID]] = Field(default_factory=list)


class UserGroupUpdate(UserGroupCreate):
    id: UUID


class UserGroupFilter(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    user_ids: Optional[List[UUID]] = []


class UserGroup(UserGroupBase):
    users: List["UserBase"] = Field(default_factory=list)


class UserBase(BaseModel):
    model_config = global_model_config

    id: UUID
    email: str
    created_datetime: datetime
    updated_datetime: Optional[datetime]


class UserCreate(BaseModel):
    email: str
    group_ids: List[UUID] = Field(default_factory=list)
    
    item_ids: List[UUID] = Field(default_factory=list)


class UserUpdate(UserCreate):
    id: UUID


class UserFilter(BaseModel):
    email: Optional[str] = None
    group_ids: Optional[List[UUID]] = []
    
    item_ids: Optional[List[UUID]] = []


class User(UserBase):
    # Allows pydantic/sqlalchemy to use ORM to pull out related objects instead of just references to them
    groups: List["UserGroupBase"] = Field(default_factory=list)
    
    items: List["ItemBase"] = Field(default_factory=list)
