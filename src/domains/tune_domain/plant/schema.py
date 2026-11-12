from pydantic import BaseModel, Field

class PlantTuneIn(BaseModel):
    img_b64: str = Field(..., description="裸base64图片，不要data:image前缀")
    tag: str = Field(default="", description="用户附加备注上下文")

class PlantTuneOut(BaseModel):
    type_id: int | None
    desc: str
    advice: str
    warning: str
