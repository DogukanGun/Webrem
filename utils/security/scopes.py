from enum import Enum


class UserScopes(Enum):
    ADMIN_MASTER = "admin:master"
    ADMIN = "admin:-"
    MASTER_MODERATOR = "master:moderator"
    MODERATOR = "moderator"
    USER = "user"
