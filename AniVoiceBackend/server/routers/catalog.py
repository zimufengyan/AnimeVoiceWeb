import logging
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from ..common import build_base_url, join_url_path
from ..runtime import settings
from ..services.characters import get_ip_character_config, get_ip_character_entries


router = APIRouter()


@router.get("/get_belong_statics")
async def get_belong_statics(request: Request, belong: Optional[str] = Query(None)):
    logging.info("get belong statics for %s", belong)
    ip_config = get_ip_character_config(belong)
    if not ip_config:
        logging.warning("belong %s not in ip_characters_manifest", belong)
        return JSONResponse(content={"code": "-1", "messaage": "该IP不存在"}, status_code=201)

    base_url = build_base_url(request)
    names, stand_urls, avator_urls = [], [], []
    for character_item in get_ip_character_entries(belong):
        names.append(character_item.get("key", ""))
        stand_urls.append(
            f"{base_url}/{join_url_path(settings.STANDS_LOCAL_DIR, belong, character_item.get('standFile', ''))}"
        )
        avator_urls.append(
            f"{base_url}/{join_url_path(settings.CHARACTER_AVATOR_LOCAL_DIR, belong, character_item.get('avatarFile', ''))}"
        )
    return {"code": 1, "names": names, "stands": stand_urls, "avators": avator_urls}


@router.get("/get_ip_characters")
async def get_ip_characters(request: Request, belong: Optional[str] = Query(None)):
    logging.info("get ip characters for %s", belong)
    ip_config = get_ip_character_config(belong)
    if not ip_config:
        logging.warning("belong %s not in ip_characters_manifest", belong)
        return JSONResponse(content={"code": "-1", "message": "该IP不存在"}, status_code=404)

    base_url = build_base_url(request)
    characters = []
    for character_item in get_ip_character_entries(belong):
        characters.append(
            {
                "key": character_item.get("key", ""),
                "displayName": character_item.get("displayName", ""),
                "englishName": character_item.get("englishName", ""),
                "avatarUrl": f"{base_url}/{join_url_path(settings.CHARACTER_AVATOR_LOCAL_DIR, belong, character_item.get('avatarFile', ''))}",
                "standUrl": f"{base_url}/{join_url_path(settings.STANDS_LOCAL_DIR, belong, character_item.get('standFile', ''))}",
                "order": character_item.get("order", 0),
                "tags": character_item.get("tags", []),
                "accent": character_item.get("accent", ""),
                "aliases": character_item.get("aliases", []),
                "available": character_item.get("available", True),
            }
        )

    return {
        "code": 1,
        "ip": {
            "belong": ip_config.get("belong", belong or ""),
            "key": ip_config.get("key", ""),
            "displayName": ip_config.get("displayName", belong or ""),
            "englishName": ip_config.get("englishName", ip_config.get("displayName", belong or "")),
        },
        "characters": characters,
    }
