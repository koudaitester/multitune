# src/domains/good_domain/env_monitor/schema.py
from pydantic import BaseModel, Field
from typing import List

from common.schema_meta import EvalMeta


class EnvMonitorReq(BaseModel):
    image_b64: str = Field(description="室内环境照片 base64（裸 base64，不带 data: 前缀）")


class EnvIssue(BaseModel):
    item: str = Field(description="指标名称，如 温度/湿度/空气质量/光照/通风")
    level: str = Field(description="异常方向，如 偏高/偏低/异常/不足")
    note: str = Field(description="该指标的问题说明")


class EnvMonitorResp(EvalMeta):
    scene_type: str = Field(description="indoor / outdoor / unknown")
    comfort_score: int = Field(description="0–100，越低越不舒适")
    env_level: str = Field(description="优 / 良 / 一般 / 差 / 无效")
    issues: List[EnvIssue]
    suggestions: List[str]
    monitor_points: List[str] = Field(description="建议的传感器布点位置")
