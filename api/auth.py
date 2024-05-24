from datetime import timedelta, datetime
from typing import List, Any
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated
from api.data.auth_data import User, Token
from utils.constants.collection_name import CollectionName
from utils.constants.user_types import get_user_type_from_scope
from utils.database.database import Database, get_db
from utils.environment.environment_manager import EnvironmentManager, get_environment_manager
from utils.error_handler.error_codes import ErrorCode
from utils.error_handler.response_handler import return_error_message
from utils.notification.send_email import send_email_notification, OTPNotification
from utils.security.authenticate import create_access_token, authenticate_user, \
    get_password_hash, get_current_user
from api.data.general import return_success_response, return_success_response_with_data
from utils.security.otp import generate_otp
from utils.security.scopes import UserScopes

router = APIRouter(prefix="/auth", tags=["Auth"])


def create_token(username: str, scopes: List[str], env_manager: EnvironmentManager) -> str:
    access_token_expires = timedelta(minutes=60 * 60 * 8)
    return create_access_token(
        env_manager=env_manager,
        data={"sub": username, "scopes": scopes},
        expires_delta=access_token_expires,
    )


@router.post("/login", response_model=Token)
def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Database = Depends(get_db),
        env_manager: EnvironmentManager = Depends(get_environment_manager),
):
    user = authenticate_user(username=form_data.username, password=form_data.password, db=db)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_token(form_data.username, user["scopes"], env_manager)
    return {"access_token": access_token, "token_type": "bearer"}


def get_user(db: Database, username: str) -> [Any]:
    return db.get_object(CollectionName.USER.value, {"username": username})


def get_user_by_oauth2(db: Database, form_data: OAuth2PasswordRequestForm) -> Any:
    results = get_user(db, form_data.username)
    if results is None or len(results) != 0:
        raise HTTPException(status_code=400, detail="User is already exist")


def add_user_with_scopes(db: Database,
                         username: str,
                         password: str,
                         scopes: List[str],
                         email: str,
                         fullname: str):
    object_id = db.insert_object(CollectionName.USER.value,
                                 User(username=username,
                                      email=email,
                                      fullname=fullname,
                                      password=get_password_hash(password),
                                      scopes=scopes).__dict__)
    if object_id is None:
        raise HTTPException(status_code=400, detail="Database error")


@router.post("/register/moderator/master")
def register_as_moderator_master(
        fullname: str,
        email: str,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        current_user: Annotated[User, Security(get_current_user
            , scopes=[UserScopes.ADMIN_MASTER.value, UserScopes.ADMIN.value])],
        db: Database = Depends(get_db)
):
    get_user_by_oauth2(db, form_data)
    add_user_with_scopes(db, form_data.username, form_data.password,
                         [UserScopes.MODERATOR.value, UserScopes.MASTER_MODERATOR.value, UserScopes.USER.value]
                         , email, fullname)
    return return_success_response()


@router.post("/register/moderator")
def register_as_moderator_master(
        fullname: str,
        email: str,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        current_user: Annotated[User, Security(get_current_user
            , scopes=[UserScopes.ADMIN_MASTER.value, UserScopes.ADMIN.value])],
        db: Database = Depends(get_db)
):
    get_user_by_oauth2(db, form_data)
    add_user_with_scopes(db, form_data.username, form_data.password,
                         [UserScopes.MODERATOR.value, UserScopes.USER.value], email, fullname)
    return return_success_response()


@router.post("/register", response_model=Token)
def register(
        email: str,
        fullname: str,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Database = Depends(get_db),
        env_manager: EnvironmentManager = Depends(get_environment_manager)
):
    get_user_by_oauth2(db, form_data)
    scopes = [UserScopes.USER.value]
    add_user_with_scopes(db, form_data.username, form_data.password, scopes, email, fullname)
    access_token = create_token(form_data.username, scopes, env_manager)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/assign/moderator")
def assign_someone_as_moderator(
        username: str,
        current_user: Annotated[User, Security(get_current_user
            , scopes=[UserScopes.ADMIN_MASTER.value, UserScopes.ADMIN.value])],
        db: Database = Depends(get_db),
):
    users = get_user(db, username)
    if users is None or len(users) == 0:
        raise HTTPException(status_code=502, detail="User is not exist")
    user = User(**users[0])
    user.scopes.append(UserScopes.MODERATOR.value)
    updated_count = db.update_object(CollectionName.USER.value, {"username": user.username}, user.__dict__)
    if updated_count == 0:
        raise HTTPException(status_code=502, detail="User cannot be updated")
    return return_success_response()


@router.post("/forget/password/{username}")
def forget_password(
        username: str,
        db: Database = Depends(get_db),
        env_manager: EnvironmentManager = Depends(get_environment_manager)
):
    users = get_user(db, username)
    if users is None or len(users) == 0:
        raise HTTPException(status_code=502, detail="User is not exist")
    user = User(**users[0])
    current_time = datetime.utcnow()
    reset_request = db.get_single_object(
        CollectionName.PASSWORD_RESET_REQUESTS.value,
        {"user_id": users[0]['_id']}
    )
    if reset_request:
        last_change = reset_request.get('last_password_change')
        if last_change and (current_time - last_change).total_seconds() < 7200:  # 7200 seconds = 2 hours
            return return_success_response()
    otp_code = generate_otp(env_manager)
    expiry_time = current_time + timedelta(hours=2)
    db.update_object(
        "PasswordResetRequests",
        {"user_id": users[0]['_id']},
        {
            "reset_otp": otp_code,
            "otp_expiry": expiry_time,
            "password_changed": False,
            "last_password_change": None,
            "is_deleted": False
        },
        upsert=True
    )
    send_email_notification(
        user.email,
        OTPNotification("Your password reset code", "OTP Code", otp_code),
    )
    return return_success_response()


@router.post("/forget/password/verify")
def otp_verify(
        current_user: Annotated[User, Depends(get_current_user)],
        otp_code: str,
        new_password: str,
        db: Database = Depends(get_db)
):
    reset_request = db.get_single_object(
        CollectionName.PASSWORD_RESET_REQUESTS.value,
        {"user_id": current_user["_id"]}
    )
    if not reset_request:
        return return_error_message(db, ErrorCode.RESET_REQUEST_NOT_FOUND)

    current_time = datetime.utcnow()
    if (reset_request['reset_otp'] == otp_code and
            reset_request['otp_expiry'] > current_time and
            not reset_request['password_changed']):
        db.update_object(
            CollectionName.USER.value,
            {"_id": current_user['_id']},
            {"password": get_password_hash(new_password), }
        )
        db.update_object(
            "PasswordResetRequests",
            {"user_id": current_user['_id']},
            {
                "password_changed": True,
                "last_password_change": current_time
            }
        )
        return return_success_response()
    else:
        return return_error_message(db, ErrorCode.INVALID_OTP_OR_EXPIRED)


@router.post("/type")
def get_user_type(
        current_user: Annotated[User, Depends(get_current_user)],
):
    scopes = current_user["scopes"]
    return return_success_response_with_data(get_user_type_from_scope(scopes))
