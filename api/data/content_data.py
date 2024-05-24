from typing import Optional

from pydantic import BaseModel


class ImageUpload(BaseModel):
    image: Optional[str]
    username: Optional[str]
    upload_time: Optional[str]
    file_path:Optional[str]
    last_modified_date: Optional[str]
    is_image:bool
    file_content_type:Optional[str]


class GetImageResponse(BaseModel):
    id: Optional[str]
    image: str
    username: Optional[str]
    upload_time: Optional[str]
    last_modified_date: Optional[str]
