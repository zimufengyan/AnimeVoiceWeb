from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, Field, StringConstraints
from typing_extensions import Annotated

from .common import MetaResponse


class TTSRequest(BaseModel):
    text: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=4, max_length=200),
    ] = Field(..., examples=["你好，欢迎使用语音合成服务。"])
    lang: str = "zh"
    belong: str
    character: str = Field(
        ...,
        validation_alias=AliasChoices("character", "charactor"),
        serialization_alias="character",
    )


class GenerateVoiceResponse(BaseModel):
    meta: MetaResponse
    audio_url: str


class BelongStaticsResponse(BaseModel):
    meta: MetaResponse
    stands: List[str]
    avators: List[str]
    names: List[str]


class IpMetaPayload(BaseModel):
    belong: str
    key: str
    displayName: str
    englishName: str


class IpCharacterItem(BaseModel):
    key: str
    displayName: str
    englishName: str
    avatarUrl: str
    standUrl: str
    order: int = 0
    tags: List[str] = []
    accent: Optional[str] = None
    aliases: List[str] = []
    available: bool = True


class IpCharactersResponse(BaseModel):
    meta: MetaResponse
    ip: IpMetaPayload
    characters: List[IpCharacterItem]


class AudioRecordItem(BaseModel):
    audio_id: int | None = None
    user_id: int
    audio_character: str
    audio_belong: str
    audio_path: str
    created_at: Optional[datetime] = datetime.now()
    audio_text: str = ""
    text_lang: str = "zh"
    character_avator_path: str = ""
    audio_filename: str = ""

    model_config = {"from_attributes": True}


class AudioRecordResponse(BaseModel):
    meta: MetaResponse
    records: Optional[List[AudioRecordItem]] = None


@dataclass
class TTSReqForm:
    text: str = None
    text_lang: str = "auto"
    ref_audio_path: str = None
    prompt_lang: str = None
    prompt_text: str = ""
    top_k: int = 5
    top_p: float = 1
    temperature: float = 1
    sample_steps: int = 16
    media_type: str = "wav"
    streaming_mode: bool = False
    threshold: int = 30

    def to_dict(self):
        return asdict(self)
