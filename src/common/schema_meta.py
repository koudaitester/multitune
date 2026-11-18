"""对外响应统一元信息

所有视觉评估接口都返回 status / reason，让调用方用一个分支就能判断结论是否可用，
不用再分别解析 type_id=None、type_id=99、space_type=unknown、env_level=无效 四种写法。

约定：
- status="ok"      结论有效
- status="invalid" 无法给出有效结论（图中没有目标对象、或场景不符合业务前提）
- reason 是给前端直接展示的中文原因
- 模型调用失败不占用 status，由接口层返回 HTTP 500
"""
from pydantic import BaseModel, Field

STATUS_OK = "ok"
STATUS_INVALID = "invalid"

REASON_NO_TARGET = "图中未识别到目标对象"


class EvalMeta(BaseModel):
    status: str = Field(default=STATUS_OK, description="ok=结论有效；invalid=无法给出有效结论")
    reason: str = Field(default="", description="invalid 时的具体原因，供前端直接展示")
