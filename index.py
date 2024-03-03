import traceback
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from mangum import Mangum
# from db_config import DbHandler

app = FastAPI()


@app.get("/scan-qr/{qr_id}")
async def redirect_instagram(qr_id: str):
    try:
        qr_details = "DbHandler.get_qr_details(qr_id=qr_id)"

        if not qr_details or not qr_details['username']:
            return RedirectResponse("https://www.instagram.com/")

        instagram_url = f"https://www.instagram.com/{qr_details['username']}/"
        return RedirectResponse(instagram_url)

    except Exception as e:
        print(traceback.format_exc())
        return RedirectResponse("https://www.instagram.com/")


@app.post("/scan-qr")
async def map_qr_id(qr_id: str, username: str):
    try:
        qr_details = "DbHandler.update_mapping(qr_id=qr_id, username=username)"

        if not qr_details:
            return {'message': "Try again"}
        instagram_url = f"https://www.instagram.com/{qr_details['username']}/"
        return {'message': "updated successfully", "url": instagram_url}
    except Exception as e:
        print(traceback.format_exc())
        return {'message': "Try again"}



