from pydantic import BaseModel

class FruitClassifyReq(BaseModel):
    image_b64: str
    tag: str | None = None

class FruitClassifyResp(BaseModel):
    type_id: int
    desc: str
    advice: str
    warning: str
