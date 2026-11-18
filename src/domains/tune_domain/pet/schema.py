from pydantic import BaseModel, Field

from common.schema_meta import EvalMeta


class PetTuneIn(BaseModel):
    img_b64: str = Field(..., description="裸base64图片，不要data:image前缀")
    tag: str = Field(default="", description="用户附加备注上下文")


class PetTuneOut(EvalMeta):
    type_id: int = Field(description="1–4 正常分型，99 表示图中未识别到目标对象")
    desc: str
    advice: str
    warning: str
