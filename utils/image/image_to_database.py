from datetime import date

from api.data.auth_data import User
from api.data.content_data import ImageUpload


def image_to_database(
        current_user: User,
        image: ImageUpload = None
):

    image.username = current_user["username"]
    image.upload_time = date.today().isoformat()
    image.last_modified_date = date.today().isoformat()
    image.is_image = True
    return image
