from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class LoginResponseForm:
    code: str = field(default='3')     # 结果代码
    username: str = field(default='')
    avatar: str = field(default='')      # 头像地址
    index: str = field(default='')      # 用户编号
    rate: str = field(default='')       # 评级
    token: str = field(default='')      
    message: str = field(default='')      

    def to_dict(self):
        return asdict(self)


@dataclass
class TTSReqForm:
    text: str = None,                   # str.(required) text to be synthesized
    text_lang: str = "auto",            # str.(required) language of the text to be synthesized
    ref_audio_path: str = None,         # str.(required) reference audio path
    prompt_lang: str = None,            # str.(required) language of the prompt text for the reference audio
    prompt_text: str = "",              # str.(optional) prompt text for the reference audio
    top_k: int = 5,                     # int. top k sampling
    top_p: float = 1,                   # float. top p sampling
    temperature: float = 1,             # float. temperature for sampling
    sample_steps: int = 16,             # int. When you use v3 model,you can set this sample_steps
    media_type: str = "wav",            # str. Set the file format for returning audio.
    streaming_mode: bool = False,       # bool. whether to return a streaming response.
    threshold: int = 30                 # int. Text segmentation parameter,the lower value, the faster the streaming inference, but the worse the audio quality.

    def to_dict(self):
        return asdict(self)


@dataclass
class UserItem:
    id: str = field(default='')
    name: str = field(default="")
    sex: str = field(default="")
    age: int = field(default=0)
    pic: str = field(default="")
    pwd: str = field(default="")
    phone: str = field(default="")
    email: str = field(default="")
    rate: str = field(default="")
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    index: str = field(default="")
    salt: str = field(default="")

    def to_dict(self):
        return asdict(self)
    

@dataclass
class AudioRecordItem:
    audio_id: str = field(default='')
    # user_id: str = field(default='')
    audio_path: str = field(default='')
    audio_character: str = field(default='')
    audio_belong: str = field(default='')
    create_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return asdict(self)