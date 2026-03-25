import os
from pathlib import Path
from typing import Optional

from ..runtime import character_dic, ip_characters_manifest


def normalize_character_lookup_key(value: str) -> str:
    return os.path.splitext(value or "")[0].strip().replace(" ", "").lower()


def get_ip_character_config(belong: Optional[str]) -> dict:
    return ip_characters_manifest.get(belong or "", {})


def get_ip_character_entries(belong: Optional[str]) -> list[dict]:
    characters = get_ip_character_config(belong).get("characters", [])
    return sorted(characters, key=lambda item: (item.get("order", 9999), item.get("displayName", "")))


def find_ip_character_entry(belong: Optional[str], name: str) -> Optional[dict]:
    lookup_key = normalize_character_lookup_key(name)
    if not lookup_key:
        return None

    for character_item in get_ip_character_entries(belong):
        candidates = [
            character_item.get("key", ""),
            character_item.get("displayName", ""),
            character_item.get("englishName", ""),
            *(character_item.get("aliases", []) or []),
        ]
        if any(normalize_character_lookup_key(candidate) == lookup_key for candidate in candidates if candidate):
            return character_item

    return None


def canonicalize_character_name(name: str, belong: Optional[str] = None) -> str:
    raw_name = os.path.splitext(name)[0].strip()
    if not raw_name:
        return raw_name

    manifest_character = find_ip_character_entry(belong, raw_name)
    if manifest_character:
        return manifest_character.get("key", raw_name)

    normalized_raw = raw_name.replace(" ", "").lower()
    if belong in character_dic:
        for character_name in character_dic[belong].keys():
            if character_name.replace(" ", "").lower() == normalized_raw:
                return character_name

    return raw_name


def resolve_character_asset_filename(directory: str, belong: str, character_name: str, ext: str) -> str:
    character_dir = Path(directory) / belong
    exact_name = f"{character_name}.{ext}"
    if (character_dir / exact_name).exists():
        return exact_name

    for asset_path in sorted(character_dir.glob(f"*.{ext}")):
        if canonicalize_character_name(asset_path.stem, belong) == character_name:
            return asset_path.name

    return exact_name
