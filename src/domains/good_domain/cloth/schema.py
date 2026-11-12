from pydantic import BaseModel

class ClothClassifyReq(BaseModel):
    image_b64: str
    tag: str | None = None

class ClothClassifyResp(BaseModel):
    type_id: int
    desc: str
    advice: str
    warning: str
