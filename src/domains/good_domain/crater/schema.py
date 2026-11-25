from pydantic import BaseModel, Field
from typing import List, Optional

class CraterDoubleReq(BaseModel):
    image_overview_b64: str = Field(description="远景全貌图base64")
    image_detail_b64: str = Field(description="近景局部图base64")

class CraterDoubleResp(BaseModel):
    is_crater: bool
    confidence: float = Field(ge=0, le=1, description="置信度0~1")
    evidence: List[str]
    reject_reason: Optional[str] = None
