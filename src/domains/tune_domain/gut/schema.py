# src/domains/tune_domain/guttune/schema.py
from pydantic import BaseModel, Field

from common.schema_meta import EvalMeta


class GutAnalyzeRequest(BaseModel):
    image_b64: str = Field(description="图片base64字符串")


class GutAnalyzeResponse(EvalMeta):
    type_id: int = Field(description="1–7 布里斯托分型，99 表示图中未识别到目标对象")
    type_name: str
    description: str
    suggestion: str
    compare_baseline: str
    level: str
    tag: str
