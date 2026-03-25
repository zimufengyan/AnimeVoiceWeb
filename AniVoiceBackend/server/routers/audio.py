import logging
from pathlib import Path
from typing import List

import aiofiles
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from ..runtime import audio_record_manager, settings
from ..schemas import AudioRecordResponse, MetaResponse, TTSRequest, UserItem
from ..security import get_current_user
from ..services.tts import generate_voice_response


router = APIRouter()


@router.post("/generate_voice")
async def generate_voice(
    request: Request,
    current_user: UserItem = Depends(get_current_user),
    form: TTSRequest = Body(...),
):
    return await generate_voice_response(request, current_user, form)


@router.get("/get_recent_audio_records", response_model=AudioRecordResponse)
async def get_recent_audio_records(current_user: UserItem = Depends(get_current_user)):
    logging.info("current user: %s", current_user.name)
    success, records = await audio_record_manager.get_rencent_audio_records_by_user_id(
        current_user.id,
        days=settings.AUDIO_RECORD_EXPIRE,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="faild to get recent audio records")
    return {"meta": MetaResponse(code="1", message="获取成功"), "records": records}


@router.get("/delete_audio_record")
async def delete_audio_record(current_user: UserItem = Depends(get_current_user), audio_id: int = Query(...)):
    logging.info("current user: %s", current_user.name)
    success, message = await audio_record_manager.delete_audio_record_by_id(audio_id)
    logging.info(message)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    success, records = await audio_record_manager.get_rencent_audio_records_by_user_id(
        current_user.id,
        days=settings.AUDIO_RECORD_EXPIRE,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="faild to get recent audio records")
    return {"meta": MetaResponse(code="1", message="删除成功"), "records": records}


@router.get("/delete_audio_records")
async def delete_audio_records(current_user: UserItem = Depends(get_current_user), audio_ids: List[int] = Query(...)):
    logging.info("current user: %s", current_user.name)
    success, message = await audio_record_manager.delete_audio_records_by_ids(audio_ids)
    logging.info(message)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    success, records = await audio_record_manager.get_rencent_audio_records_by_user_id(
        current_user.id,
        days=settings.AUDIO_RECORD_EXPIRE,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="faild to get recent audio records")
    return {"meta": MetaResponse(code="1", message="删除成功"), "records": records}


@router.get("/download/{filename}")
async def download_file(filename: str):
    file_path = Path(f"uploads/{filename}")
    if not file_path.is_file():
        return {"error": "File not found"}

    async def file_sender():
        async with aiofiles.open(file_path, "rb") as file:
            while chunk := await file.read(1024 * 1024):
                yield chunk

    return StreamingResponse(file_sender(), media_type="application/octet-stream")
