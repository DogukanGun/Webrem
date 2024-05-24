from typing import Annotated, List

from fastapi import APIRouter, Security, Depends

from api.data.auth_data import User
from api.data.content_data import ImageUpload
from api.data.general import return_success_response_with_data
from utils.constants.collection_name import CollectionName
from utils.database.database import get_db, Database
from utils.security.authenticate import get_current_user
from utils.security.scopes import UserScopes

router = APIRouter(prefix="/content", tags=["Content"])


@router.get("", response_model=List[ImageUpload])
def get_content(
        current_user: Annotated[User, Security(get_current_user, scopes=[UserScopes.USER.value])],
        db: Database = Depends(get_db),
):
    objs = db.get_object(CollectionName.IMAGES.value, {"username": current_user["username"]})
    return return_success_response_with_data(objs)

