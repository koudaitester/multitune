# src/domains/tune_domain/posture/schema.py
from typing import List, Optional

from pydantic import BaseModel, Field

from common.schema_meta import EvalMeta


class PostureReq(BaseModel):
    image_b64: str = Field(
        description="人物体态照片 base64（裸串，不带 data: 前缀）。要求正侧位、单人、全身入镜"
    )


class PostureMetrics(BaseModel):
    """图像平面内的角度，单位度。全身未拍全时骨盆与膝为 null。"""

    head_forward_deg: Optional[float] = Field(None, description="耳-肩连线与竖直方向的夹角")
    shoulder_offset_deg: Optional[float] = Field(None, description="肩-髋连线与竖直方向的夹角")
    pelvic_tilt_deg: Optional[float] = Field(None, description="髋-膝连线与竖直方向的夹角")
    knee_deg: Optional[float] = Field(None, description="膝-踝连线与竖直方向的夹角")


class PostureIssue(BaseModel):
    item: str = Field(description="问题名称，如 头前倾 / 圆肩 / 骨盆前倾")
    severity: str = Field(description="明显 / 中度 / 轻度")
    note: str = Field(description="该问题的说明与影响")
    measured_deg: float = Field(description="实测角度")
    threshold_deg: float = Field(description="该项的正常上限")


class PostureResp(EvalMeta):
    posture_score: int = Field(description="0–100，越低体态代偿越多")
    posture_level: str = Field(description="优 / 良 / 一般 / 差 / 无效")
    metrics: PostureMetrics
    issues: List[PostureIssue]
    suggestions: List[str]
    camera_advice: List[str] = Field(description="为了拍出可评估的照片，应该怎么拍")
    reliability: str = Field(description="full = 全身入镜；upper_only = 仅上半身；none = 无效")
    notice: str = Field(description="使用边界说明")
