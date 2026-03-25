import asyncio
import logging
import os
import uuid
from pathlib import Path

import aiofiles
import httpx
from fastapi import Request, status
from fastapi.responses import JSONResponse

from save_big_file import save_wav_bytes, save_wav_stream
from utils import async_execute_request

from ..common import build_base_url, join_url_path, model_config_error_response, resolve_local_backend_path
from ..runtime import (
    audio_record_manager,
    character_dic,
    get_current_activated_character,
    set_current_activated_character,
    settings,
)
from ..schemas.audio import AudioRecordItem, TTSReqForm, TTSRequest
from ..schemas.profile import UserItem
from .characters import canonicalize_character_name, resolve_character_asset_filename


async def generate_voice_response(request: Request, current_user: UserItem, form: TTSRequest):
    logging.info("current user: %s", current_user)
    character_name = canonicalize_character_name(form.character, form.belong)
    if character_name != form.character:
        logging.info("normalized character name from %s to %s", form.character, character_name)
        form.character = character_name

    if form.belong not in character_dic:
        logging.warning("belong %s not in character_dic", form.belong)
        return JSONResponse(
            content={"code": "-1", "message": "该IP不存在"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    all_characters: dict = character_dic[form.belong]
    if form.character not in all_characters:
        logging.warning("character %s not in all_characters", form.character)
        return JSONResponse(
            content={"code": "-2", "message": "该角色不存在或暂不支持"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    model_info = all_characters[form.character]
    required_model_keys = [
        "gpt_weights_path",
        "sovits_weights_path",
        "promot_lang",
        "prompt_text_path",
        "ref_audio_path",
    ]
    missing_keys = [key for key in required_model_keys if not model_info.get(key)]
    if missing_keys:
        logging.warning(
            "character %s missing model config keys: %s",
            form.character,
            ", ".join(missing_keys),
        )
        return model_config_error_response(f"角色 {form.character} 缺少模型配置，暂时无法生成语音")

    active_character = get_current_activated_character()
    if not active_character or form.character != active_character:
        logging.info("set model for character: %s", form.character)
        try:
            succ1, _ = await async_execute_request(
                url=settings.SOVITS_SET_GPT_API,
                param={"weights_path": model_info["gpt_weights_path"]},
            )
            succ2, _ = await async_execute_request(
                url=settings.SOVITS_SET_VIT_API,
                param={"weights_path": model_info["sovits_weights_path"]},
            )
        except Exception as exc:
            logging.error("failed to reach GPT-SoVITS weight APIs: %s", exc, exc_info=True)
            return JSONResponse(
                content={"code": "-1", "message": f"无法连接 GPT-SoVITS 服务: {settings.SOVITS_ADDR}"},
                status_code=status.HTTP_502_BAD_GATEWAY,
            )

        if not succ1 or not succ2:
            return JSONResponse(
                content={"code": "-1", "message": f"GPT-SoVITS 模型切换失败: {settings.SOVITS_ADDR}"},
                status_code=status.HTTP_502_BAD_GATEWAY,
            )
        logging.info("successfully set model for character: %s", form.character)
        set_current_activated_character(form.character)

    prompt_text_path = resolve_local_backend_path(model_info["prompt_text_path"])
    if not os.path.exists(prompt_text_path):
        logging.error("prompt text file not found: %s", prompt_text_path)
        return JSONResponse(
            content={"code": "-4", "message": f"提示词文件不存在: {prompt_text_path}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    async with aiofiles.open(prompt_text_path, "r", encoding="utf-8") as file:
        prompt_text = (await file.read()).replace("/n", "").strip()

    tts_data = TTSReqForm(
        text=form.text,
        text_lang=form.lang,
        ref_audio_path=model_info["ref_audio_path"],
        prompt_lang=model_info["promot_lang"],
        prompt_text=prompt_text,
    )
    logging.info(
        "sending TTS request to %s with ref_audio_path=%s prompt_lang=%s",
        settings.SOVITS_TTS_API,
        tts_data.ref_audio_path,
        tts_data.prompt_lang,
    )

    unique_id = str(uuid.uuid4())
    audio_dir = Path(settings.GENERATED_AUDIO_DIR)
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / f"{unique_id}.wav"
    audio_local_path = join_url_path(settings.GENERATED_AUDIO_LOCAL_DIR, f"{unique_id}.wav")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                settings.SOVITS_TTS_API,
                json=tts_data.to_dict(),
                headers={"Content-Type": "application/json"},
            )
        except httpx.HTTPError as exc:
            logging.error("failed to reach GPT-SoVITS TTS API: %s", exc, exc_info=True)
            return JSONResponse(
                content={"code": "-1", "message": f"无法连接 GPT-SoVITS 语音接口: {settings.SOVITS_TTS_API}"},
                status_code=status.HTTP_502_BAD_GATEWAY,
            )

        if response.status_code != 200:
            logging.error("GPT-SoVITS TTS API returned %s: %s", response.status_code, response.text)
            return JSONResponse(
                content={"code": "-1", "message": f"GPT-SoVITS 返回异常: {response.status_code}"},
                status_code=status.HTTP_502_BAD_GATEWAY,
            )

        if tts_data.streaming_mode:
            async def streaming_wrapper():
                async for chunk in response.aiter_bytes():
                    yield chunk

            asyncio.create_task(save_wav_stream(streaming_wrapper(), audio_path))
        else:
            await save_wav_bytes(response.content, audio_path)

    logging.info("successfully write audio into path : %s", audio_path)
    base_url = build_base_url(request)
    local_audio_url = f"{base_url}/{audio_local_path}"
    avatar_filename = resolve_character_asset_filename(
        settings.CHARACTER_AVATOR_DIR,
        form.belong,
        form.character,
        settings.CHARACTER_AVATOR_EXT,
    )
    character_avatar_url = (
        f"{base_url}/"
        f"{join_url_path(settings.CHARACTER_AVATOR_LOCAL_DIR, form.belong, avatar_filename)}"
    )

    record_created, record_message = await audio_record_manager.create_audio_record(
        AudioRecordItem(
            user_id=current_user.id,
            audio_character=form.character,
            audio_belong=form.belong,
            audio_path=local_audio_url,
            audio_text=form.text,
            text_lang=form.lang,
            character_avator_path=character_avatar_url,
            audio_filename=audio_path.name,
        )
    )
    if not record_created:
        logging.warning("failed to create audio record: %s", record_message)

    return {"code": 1, "audio_url": local_audio_url, "message": "语音生成成功"}
