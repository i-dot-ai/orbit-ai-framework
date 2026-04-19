from shared_utils.settings import (
    get_settings,
    get_logger,
)
from uuid import UUID

from decorator import contextmanager
from sqlalchemy import or_
from sqlalchemy.orm import Session

from shared_utils.database.pydantic_schemas import Item as PyItem
from shared_utils.database.pydantic_schemas import ItemCreate
from shared_utils.database.pydantic_schemas import ItemFilter
from shared_utils.database.pydantic_schemas import ItemUpdate


from shared_utils.database.pydantic_schemas import UserGroup as PyUserGroup
from shared_utils.database.pydantic_schemas import UserGroupCreate
from shared_utils.database.pydantic_schemas import UserGroupFilter
from shared_utils.database.pydantic_schemas import UserGroupUpdate
from shared_utils.database.postgres_models import UserGroup as SqUserGroup
from shared_utils.database.postgres_models import user_usergroups


from shared_utils.database.pydantic_schemas import User as PyUser
from shared_utils.database.pydantic_schemas import UserCreate
from shared_utils.database.pydantic_schemas import UserFilter
from shared_utils.database.pydantic_schemas import UserUpdate
from shared_utils.database.postgres_database import SessionLocal
from shared_utils.database.postgres_models import Item as SqItem
from shared_utils.database.postgres_models import User as SqUser


pydantic_model_to_sqlalchemy_model_map = {
    PyItem: SqItem,
    PyUserGroup: SqUserGroup,
    UserGroupCreate: SqUserGroup,
    UserGroupUpdate: SqUserGroup,
    PyUser: SqUser,
    ItemCreate: SqItem,
    UserCreate: SqUser,
    ItemUpdate: SqItem,
    UserUpdate: SqUser,
}

pydantic_update_model_to_base_model = {
    ItemUpdate: PyItem,
    UserGroupUpdate: PyUserGroup,
    
    UserUpdate: PyUser,
}

pydantic_update_model_to_sqlalchemy_model = {
    ItemUpdate: SqItem,
    UserGroupUpdate: SqUserGroup,
    
    UserUpdate: SqUser,
}

pydantic_create_model_to_base_model = {
    ItemCreate: PyItem,
    UserGroupCreate: PyUserGroup,
    
    UserCreate: PyUser,
}

settings = get_settings()
logger   = get_logger()


@contextmanager
def session_manager() -> Session:
    db = SessionLocal()
    try:
        yield db
    except:
        # if we fail somehow rollback the connection
        logger.debug("Db operation failed... rolling back")
        db.rollback()
        raise
    finally:
        db.close()


def get_all(
    model: PyItem  | PyUserGroup  | PyUser,
) -> list[PyItem | PyUserGroup | PyUser] | None:
    with session_manager() as db:
        try:
            sq_model = pydantic_model_to_sqlalchemy_model_map.get(model)
            result = db.query(sq_model).all()
            results = []
            for item in result:
                parsed_item = model.model_validate(item)
                results.append(parsed_item)  # Parse retrieved info into pydantic model and add to list
            return results  # noqa: TRY300
        except Exception as _:
            logger.exception("Failed to get all items, {model}", model=model)


def get_by_id(
    model: PyItem | PyUserGroup | PyUser,
    object_id: UUID,
) -> PyItem | PyUserGroup | PyUser | None:
    with session_manager() as db:
        try:
            sq_model = pydantic_model_to_sqlalchemy_model_map.get(model)
            result = db.query(sq_model).filter_by(id=object_id).one_or_none()
            if result is None:
                return None
            return model.model_validate(result)
        except Exception as _:
            logger.exception("Failed to get item by id, {model}, {object_id}", model=model, object_id=object_id)


def get_or_create_item(
    model: ItemCreate | UserCreate | UserGroupCreate,
) -> PyItem | PyUserGroup | PyUser:
    model_type = type(model)
    with session_manager() as db:
        try:
            if model_type is ItemCreate:
                return _get_or_create_item(model, db)
            if model_type is UserCreate:
                return _get_or_create_user(model, db)
            if model_type is UserGroupCreate:
                return _get_or_create_usergroup(model, db)
            
        except Exception as _:
            logger.exception("Failed to get or create item, {model}", model=model)


def _get_or_create_item(model: ItemCreate, db: Session) -> PyItem:
    sq_model = SqItem
    existing_item = (
        db.query(sq_model)
        .filter(
            sq_model.name == model.name,
            sq_model.user_id == model.user_id,
        )
        .first()
    )
    if existing_item:
        return PyItem.model_validate(existing_item)
    item_to_add = sq_model(
        custom_attribute=model.custom_attribute,
        user_id=model.user_id,
        name=model.name,
    )
    db.add(item_to_add)
    db.commit()
    db.flush()  # Refresh created item to add ID to it

    db.flush()
    return PyItem.model_validate(item_to_add)
def _get_or_create_usergroup(
    model: UserGroupCreate,
    db: Session,
    ) -> PyUserGroup:
    sq_model = SqUserGroup
    existing_item = db.query(sq_model).filter_by(name=model.name).first()
    if existing_item:
        return PyUserGroup.model_validate(existing_item)
    item_to_add = sq_model(
        name=model.name,
        description=model.description,
    )
    for user_id in model.user_ids:
        user = db.query(SqUser).get(user_id)
        item_to_add.users.append(user)
    db.add(item_to_add)
    db.commit()
    db.flush()  # Refresh created item to add ID to it

    py_base_model = pydantic_create_model_to_base_model.get(type(model))
    return py_base_model.model_validate(item_to_add)


def _get_or_create_user(
    model: UserCreate,
    db: Session,
    ) -> PyUser:
    sq_model = SqUser
    existing_item = db.query(sq_model).filter_by(email=model.email).first()
    if existing_item:
        return PyUser.model_validate(existing_item)
    item_to_add = sq_model(email=model.email)

    
    for group_id in model.group_ids:
        group = db.query(SqUserGroup).get(group_id)
        item_to_add.groups.append(group)
    

    for item_id in model.item_ids:
        item = db.query(SqItem).get(item_id)
        item_to_add.items.append(item)

    db.add(item_to_add)
    db.commit()
    db.flush()  # Refresh created item to add ID to it

    return PyUser.model_validate(item_to_add)


def delete_item(
    model: PyUser | PyUserGroup | PyItem,
    ) -> UUID:
    with session_manager() as db:
        try:
            sq_model = pydantic_model_to_sqlalchemy_model_map.get(type(model))
            item = db.query(sq_model).get(model.id)
            db.delete(item)
            db.commit()
            return model.id  # noqa: TRY300
        except Exception as _:
            logger.exception("Failed to delete item, {model}", model=model)


def update_item(
    model: ItemUpdate | UserUpdate | UserGroupUpdate,
) -> PyUser | PyUserGroup | PyItem | None:
    model_type = type(model)
    with session_manager() as db:
        try:
            if model_type is ItemUpdate:
                return _update_item(model, db)
            if model_type is UserUpdate:
                return _update_user(model, db)
            if model_type is UserGroupUpdate:
                return _update_usergroup(model, db)
            
        except Exception as _:
            logger.exception("Failed to update item, {model}", model=model)


def _update_item(model, db: Session):
    sq_model = pydantic_update_model_to_sqlalchemy_model.get(type(model))
    item = db.query(sq_model).filter(sq_model.id == model.id).one_or_none()

    if item is None:
        return None

    item.custom_attribute = model.custom_attribute
    item.name = model.name
    item.user_id = model.user_id if model.user_id else None

    db.commit()
    db.flush()  # Refresh updated item

    return PyItem.model_validate(item)


def _update_usergroup(model: UserGroupUpdate, db: Session) -> PyUserGroup | None:
    item = db.query(SqUserGroup).filter(SqUserGroup.id == model.id).one_or_none()

    if item is None:
        return None

    item.name = model.name
    item.description = model.description

    users = []
    for user_id in model.user_ids:
        user = db.query(SqUser).get(user_id)
        users.append(user)

    item.users = users

    db.commit()
    db.flush()  # Refresh updated item

    return PyUserGroup.model_validate(item)


def _update_user(model: UserUpdate, db: Session) -> PyUser | None:
    sq_model = pydantic_update_model_to_sqlalchemy_model.get(type(model))
    item = db.query(sq_model).filter(sq_model.id == model.id).one_or_none()

    if item is None:
        return None

    item.email = model.email

    
    for group_id in model.group_ids:
        group = db.query(SqUserGroup).get(group_id)
        item.groups.append(group)
    

    for item_id in model.item_ids:
        item = db.query(SqItem).get(item_id)
        item.items.append(item)

    db.commit()
    db.flush()  # Refresh updated item

    return PyUser.model_validate(item)


def filter_items(
    model: UserFilter | ItemFilter | UserGroupFilter,
) -> list[PyUser | PyItem | PyUserGroup]:
    model_type = type(model)
    with session_manager() as db:
        try:
            
            if model_type is UserGroupFilter:
                return _filter_usergroup(model, db)
            if model_type is UserFilter:
                return _filter_user(model, db)
            if model_type is ItemFilter:
                return _filter_item(model, db)
        except Exception as _:
            logger.exception("Failed to filter items, {model}", model=model)


def _filter_item(model, db):
    query = db.query(SqItem)
    if model.name:
        query = query.filter(SqItem.name.ilike(f"%{model.name}%"))
    if model.custom_attribute:
        query = query.filter(SqItem.custom_attribute == model.custom_attribute)
    if model.user_id:
        query = query.filter(SqItem.user_id == model.user_id)

    result = query.all()
    results = []
    for item in result:
        results.append(PyItem.model_validate(item))
    return results


def _filter_user(model: UserFilter, db: Session) -> list[PyUser]:
    query = db.query(SqUser)
    if model.email:
        query = query.filter(SqUser.email == model.email)

    
    if model.group_ids:
        query = query.join(user_usergroups, SqUserGroup.id == user_usergroups.c.user_id)
        query = query.filter(or_(user_usergroups.c.group_id.in_(model.group_ids)))
    

    if model.item_ids:
        query = query.join(SqItem)
        query = query.filter(or_(SqItem.id.in_(model.item_ids)))

    result = query.all()
    results = []
    for item in result:
        results.append(PyUser.model_validate(item))
    return results


def _filter_usergroup(model: UserGroupFilter, db: Session) -> list[PyUserGroup]:
    query = db.query(SqUserGroup)
    if model.name:
        query = query.filter(SqUserGroup.name.ilike(f"%{model.name}%"))
    if model.description:
        query = query.filter(SqUserGroup.description.ilike(f"%{model.description}%"))

    if model.user_ids:
        query = query.join(user_usergroups, SqUserGroup.id == user_usergroups.c.group_id)
        query = query.filter(or_(user_usergroups.c.user_id.in_(model.user_ids)))

    result = query.all()
    results: list[PyUserGroup] = []
    for item in result:
        results.append(PyUserGroup.model_validate(item))
    return results
