from datetime import datetime, date
from typing import Annotated, Dict, Any, List

from bson import ObjectId
from fastapi import APIRouter, Depends, Security, HTTPException

from api.data.auth_data import User
from api.data.content_data import ImageUpload, GetImageResponse
from api.data.general import return_success_response, BaseResponse, return_success_response_with_data
from utils.constants.collection_name import CollectionName
from utils.database.database import Database, get_db
from utils.image.image_to_database import image_to_database
from utils.security.authenticate import get_current_user
from utils.security.scopes import UserScopes

router = APIRouter(prefix="/image", tags=["Image"])


@router.post("/")
def upload_image(
        image: ImageUpload,
        current_user: Annotated[User, Security(get_current_user, scopes=[UserScopes.USER.value])],
        db: Database = Depends(get_db),
):
    image = image_to_database(current_user, image)
    obj_id = db.insert_object(CollectionName.IMAGES.value, image.__dict__)
    if obj_id is None or obj_id == "":
        raise HTTPException(status_code=502, detail="Image cannot be uploaded")
    return return_success_response()


@router.patch("/update/{id}")
def update_image(
        id: str,
        image: ImageUpload,
        current_user: Annotated[User, Security(get_current_user, scopes=[UserScopes.USER.value])],
        db: Database = Depends(get_db),
):
    updated_count = db.update_object(CollectionName.IMAGES.value, {"username": current_user["username"],
                                                                   "_id": ObjectId(id)},
                                     {"image": image.image})
    if updated_count is None or updated_count == 0:
        raise HTTPException(status_code=502, detail="Image cannot be uploaded")
    return return_success_response()


@router.delete("/{id}")
def delete_image(
        id: str,
        current_user: Annotated[User, Security(get_current_user, scopes=[UserScopes.USER.value])],
        db: Database = Depends(get_db),
):
    deleted_count = db.delete_object(CollectionName.IMAGES.value, {"username": current_user["username"],
                                                                   "_id": ObjectId(id)}, )
    if deleted_count is None or deleted_count == 0:
        raise HTTPException(status_code=502, detail="Image cannot be uploaded")
    return return_success_response()


@router.get("", response_model=BaseResponse[List[GetImageResponse]])
def get_images(
        current_user: Annotated[User, Security(get_current_user, scopes=[UserScopes.USER.value])],
        db: Database = Depends(get_db),
):
    user_images = db.get_object(CollectionName.IMAGES.value, {"username": current_user["username"]})
    return return_success_response_with_data(user_images)
