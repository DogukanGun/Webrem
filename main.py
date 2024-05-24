from fastapi import FastAPI
from api import auth, image, video
from utils.database.create_admin import create_admin_if_not_exist
from utils.logger.logger import logger
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

routers = [
    auth.router,
    image.router,
    video.router
]

for router in routers:  # routers_test
    app.include_router(router)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
                   allow_credentials=True)


@app.on_event("startup")
async def startup_event():
    logger.info("API STARTED, docs at /docs#")
    create_admin_if_not_exist()


if __name__ == "__main__":
    """
    https://github.com/tiangolo/fastapi/issues/1508
    """
    import uvicorn

    load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=8080)
