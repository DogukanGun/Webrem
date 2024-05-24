from enum import Enum
from typing import List

from utils.security.scopes import UserScopes


class UserTypes(Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    MASTER_MODERATOR = "master_moderator"
    USER = "user"


def get_user_type_from_scope(scopes: List[str]):
    if UserScopes.ADMIN in scopes or UserScopes.ADMIN_MASTER in scopes:
        return {
            "type": UserTypes.ADMIN
        }
    elif UserScopes.MODERATOR in scopes:
        return {
            "type": UserTypes.MODERATOR
        }
    elif UserScopes.MASTER_MODERATOR in scopes:
        return {
            "type": UserTypes.MASTER_MODERATOR
        }
    else:
        return {
            "type": UserTypes.USER
        }
