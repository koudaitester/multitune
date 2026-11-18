from pydantic import BaseModel, Field

from common.schema_meta import EvalMeta


class FruitClassifyReq(BaseModel):
    image_b64: str
    tag: str | None = None


class FruitClassifyResp(EvalMeta):
    type_id: int = Field(description="1–4 成熟度分型，99 表示图中未识别到目标对象")
    desc: str
    advice: str
    warning: str
