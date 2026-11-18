from pydantic import BaseModel

from common.schema_meta import EvalMeta


class ClothClassifyReq(BaseModel):
    image_b64: str
    tag: str | None = None


class ClothClassifyResp(EvalMeta):
    type_id: int
    desc: str
    advice: str
    warning: str
