from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EnvRecord(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    temp: Optional[float] = Field(None, description="温度 ℃")
    humidity: Optional[float] = Field(None, description="相对湿度 %")
    co2: Optional[int] = Field(None, description="CO2 ppm")
    mold_risk: int = Field(ge=0, le=5, description="霉菌风险 0~5")
    resp_feel: int = Field(ge=1, le=5, description="呼吸体感 1最差~5最好")
    sleep_feel: int = Field(ge=1, le=5, description="睡眠体感 1最差~5最好")
    notes: str = Field("", description="备注，开窗/拖地/净化器等")

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
