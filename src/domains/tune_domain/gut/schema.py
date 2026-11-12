# src/domains/tune_domain/guttune/schema.py
from pydantic import BaseModel, Field

class GutAnalyzeRequest(BaseModel):
    image_b64: str = Field(description="图片base64字符串")

class GutAnalyzeResponse(BaseModel):
    type_id: int
    type_name: str
    description: str
    suggestion: str
    compare_baseline: str
    level: str
    tag: str