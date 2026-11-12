from pydantic import BaseModel, Field
from typing import List, Optional


# 入参
class OldManVisualEvalRequest(BaseModel):
    image_b64: str = Field(description="图片base64")


# 模型原始观测返回（moondream原始英文描述）
class RawObservation(BaseModel):
    text: str


# 业务输出结构（沿用之前定义）
class RiskAreaItem(BaseModel):
    area_name: str
    risk_level: str
    note: str


class MmwaveSensorItem(BaseModel):
    suggest_pos: str
    install_height: str
    angle: str
    block_risk: str


class CameraSensorItem(BaseModel):
    suggest_pos: str
    install_height: str
    angle: str
    light_risk: str


class PanicButtonItem(BaseModel):
    suggest_pos: str
    note: str


class OldManVisualEvalResponse(BaseModel):
    space_type: str
    risk_area_list: List[RiskAreaItem]
    mmwave_sensor: List[MmwaveSensorItem]
    camera_sensor: List[CameraSensorItem]
    panic_button: List[PanicButtonItem]
    blind_zone: List[str]
    layout_score: int
    improve_suggest: List[str]
