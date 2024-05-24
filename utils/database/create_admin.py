import os

from fastapi import Depends

from api.data.auth_data import User
from utils.constants.collection_name import CollectionName
from utils.database.database import Database, get_db
from utils.security.authenticate import get_password_hash
from utils.security.scopes import UserScopes


def __create_admin__(db: Database):
    object_id = db.insert_object(CollectionName.USER.value,
                                 User(username="admin",
                                      email="admin",
                                      fullname="admin",
                                      password=get_password_hash("admin"),
                                      scopes=[
                                          UserScopes.ADMIN.value,
                                          UserScopes.ADMIN_MASTER.value,
                                          UserScopes.USER.value
                                      ]).__dict__)
    if object_id is None:
        os.abort()


def create_admin_if_not_exist():
    db = Database("platform")
    obj = db.get_single_object(CollectionName.USER.value, {"username": "admin", "email": "admin"})
    if obj is None:
        __create_admin__(db)
