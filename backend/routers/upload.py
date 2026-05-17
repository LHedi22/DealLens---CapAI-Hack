from fastapi import APIRouter, UploadFile, File, Form
from typing import List
import os

from backend.schemas import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    startup_id: str = Form(...),
    files: List[UploadFile] = File(...),
):
    upload_dir = os.path.join("uploads", startup_id)
    os.makedirs(upload_dir, exist_ok=True)

    saved_names = []
    for file in files:
        dest = os.path.join(upload_dir, file.filename)
        content = await file.read()
        with open(dest, "wb") as out:
            out.write(content)
        saved_names.append(file.filename)

    return UploadResponse(
        startup_id=startup_id,
        files_received=len(saved_names),
        file_names=saved_names,
        message=f"Uploaded {len(saved_names)} file(s) successfully.",
    )
