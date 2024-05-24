from datetime import date
from typing import Annotated

import bson
from PIL import Image
from bson import ObjectId
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends, Security
from starlette.responses import FileResponse
import os

from api.data.auth_data import User
from api.data.content_data import ImageUpload
from api.data.general import return_success_response, return_success_response_with_data
from utils.constants.collection_name import CollectionName
from utils.database.database import Database, get_db
from utils.image.image_to_base64 import image_to_base64
from utils.security.authenticate import get_current_user
from utils.security.scopes import UserScopes
from utils.video.thumbnail import extract_thumbnail

router = APIRouter(prefix="/video", tags=["Video"])

UPLOAD_DIR = "uploaded_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("")
async def upload_video(
        current_user: Annotated[User, Security(get_current_user, scopes=[UserScopes.USER.value])],
        db: Database = Depends(get_db),
        file: UploadFile = File(...),
):
    # Check the file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File is not a video")

    # Create a path for saving the file
    user_upload_dir = os.path.join(UPLOAD_DIR, current_user["username"])
    os.makedirs(user_upload_dir, exist_ok=True)
    file_path = os.path.join(user_upload_dir, file.filename)

    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    # Extract and convert thumbnail to Base64
    thumbnail_buffer = extract_thumbnail(file_path)
    thumbnail_image = Image.open(thumbnail_buffer)
    thumbnail_base64 = image_to_base64(thumbnail_image)
    image = ImageUpload(
        username=current_user["username"],
        upload_time=date.today().isoformat(),
        last_modified_date=date.today().isoformat(),
        image=thumbnail_base64,
        file_path=file_path,
        is_image=False,
        file_content_type=file.content_type
    )
    obj_id = db.insert_object(CollectionName.IMAGES.value, image.__dict__)
    if obj_id is None or obj_id == "":
        raise HTTPException(status_code=502, detail="Image cannot be uploaded")
    return return_success_response_with_data({"filename": file.filename})


@router.delete("/{file_id}")
async def delete_video(
        current_user: Annotated[User, Security(get_current_user, scopes=[UserScopes.USER.value])],
        file_id: str,
        db: Database = Depends(get_db),
):
    obj = db.get_object(CollectionName.IMAGES.value, {"_id": ObjectId(file_id), "username": current_user["username"]})
    if len(obj) == 0 or obj is None:
        raise HTTPException(status_code=502, detail="Video cannot be found")
    video_upload = ImageUpload(**obj[0])
    if os.path.exists(video_upload.file_path):
        os.remove(video_upload.file_path)
    return return_success_response()


@router.post("/download")
async def download_file(
        current_user: Annotated[User, Security(get_current_user, scopes=[UserScopes.USER.value])],
        file_id: str,
        db: Database = Depends(get_db),
):
    obj = db.get_single_object(CollectionName.IMAGES.value,
                               {"_id": ObjectId(file_id), "username": current_user["username"]})
    if obj is None:
        raise HTTPException(status_code=502, detail="Video cannot be found")
    video_upload = ImageUpload(**obj)
    filename = video_upload.file_path.split("/")[-1]
    return FileResponse(video_upload.file_path, media_type=video_upload.file_content_type, filename=filename)
