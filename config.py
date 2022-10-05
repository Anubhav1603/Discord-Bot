import json
from typing import Dict, List

from pydantic import BaseModel, BaseSettings, PostgresDsn, validator


class AoC(BaseModel):
    channel_id: int
    role_id: int
    session_cookie: str


class Bot(BaseModel):
    commands_channels_ids: List[int]
    games_channel_id: int  # #bot-games
    token: str

    @validator("commands_channels_ids", pre=True)
    def val_func(cls, v):
        return json.loads(v)


class Challenges(BaseModel):
    channel_id: int
    host_helper_role_id: int
    host_role_id: int
    info_channel_id: int
    participant_role_id: int
    submissions_channel_id: int
    submitted_role_id: int
    submit_channel_id: int
    winner_role_id: int


class CoC(BaseModel):
    channel_id: int
    message_id: int
    role_id: int


class Database(BaseModel):
    max_poll_connections: int
    min_poll_connections: int
    uri: PostgresDsn


class Guild(BaseModel):
    id: int
    welcomes_channel_id: int


class Moderation(BaseModel):
    admin_roles_ids: List[int]
    staff_role_id: int

    @validator("admin_roles_ids", pre=True)
    def val_func(cls, v):
        return json.loads(v)


class Notification(BaseModel):
    api_key: str  # Youtube Data AP - API Key: https://developers.google.com/youtub/docs
    channel_id: int
    role_id: int
    webhook: str


class ReactionRoles(BaseModel):
    required_role_id: int  # [lvl 20] Developer
    roles: Dict[int, int]  # Dict[emoji_id, role_id]
    message_id: int

    @validator("roles", pre=True)
    def val_func(cls, val):
        return {int(k): v for k, v in json.loads(val).items()}


class Tags(BaseModel):
    log_channel_id: int
    requests_webhook: str
    required_role_id: int  # [lvl 30] Engineer


class Timathon(BaseModel):
    channel_id: int
    participant_role_id: int


class Settings(BaseSettings):
    aoc: AoC
    bot: Bot
    challenges: Challenges
    coc: CoC
    db: Database
    guild: Guild
    moderation: Moderation
    notification: Notification  # For tim's youtube channel (currently unused)
    reaction_roles: ReactionRoles
    tags: Tags
    timathon: Timathon

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


settings = Settings()
