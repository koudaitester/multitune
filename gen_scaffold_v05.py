"""
极简FastAPI脚手架生成器 v0.5.0
--name 项目名
--ext 生成扩展模块(llm/user等)
--demo 生成睡眠环境评估完整业务Demo
"""
import os
import argparse
def render_text(tpl: str, project_name: str) -> str:
    return tpl.replace("Env POC Scaffold", project_name)
core_tpl = {
".gitignore": '''# python cache
__pycache__/
*.pyc
*.pyo
*.pyd
# venv
venv/
.venv/
.env
# runtime dir
log/
tmp/
# ide
.idea/
.vscode/
*.swp
*.swo
# os
.DS_Store
''',
"README.md": "",
"config/app_config.py": '''# config/app_config.py
from pydantic_settings import BaseSettings
class AppConfig(BaseSettings):
    app_name: str = "Env POC Scaffold"
    debug: bool = True
    class OllamaCfg(BaseSettings):
        base_url: str = "http://127.0.0.1:11434"
        model_name: str = "moondream"
        temperature: float = 0.1
        max_tokens: int = 1024
    ollama: OllamaCfg = OllamaCfg()
cfg = AppConfig()
''',
"config/prompt_config.py": '''# config/prompt_config.py
from typing import Dict
PROMPT_TEMPLATES: Dict[str, str] = {
    "moondream_visual": """你是室内人居环境检测助手，识别图片里的霉斑、水渍、返潮痕迹。
区分：霉斑 / 水渍 / 普通污渍，不要幻觉。
输出结构化结论。""",
    "idol_agent": """你是一个务实、克制、极简风格的本地助手，偏向工程协同。
回答简短，优先给可直接运行的代码/方案，少空话。
如果参数、条件不足，只问必要信息，不发散闲聊。
"""
}
''',
"config/prompt_loader.py": '''# config/prompt_loader.py
from config.prompt_config import PROMPT_TEMPLATES
class PromptNotFoundError(Exception):
    """模板不存在异常"""
    pass
def get_raw_prompt_template(template_key: str) -> str:
    """获取原始prompt模板文本，不做渲染"""
    if template_key not in PROMPT_TEMPLATES:
        raise PromptNotFoundError(
            f"Prompt模板[{template_key}]不存在，可用模板：{list(PROMPT_TEMPLATES.keys())}"
        )
    return PROMPT_TEMPLATES[template_key]
def get_prompt(template_key: str, **kwargs) -> str:
    """
    获取并渲染prompt模板
    :param template_key: 模板key名称
    :param kwargs: 占位符变量，用于str.format填充
    :return: 渲染完成的prompt字符串
    """
    template = get_raw_prompt_template(template_key)
    try:
        rendered = template.format(**kwargs)
    except KeyError:
        rendered = template
    return rendered
__all__ = ["get_prompt"]
''',
"schemas/base_schema.py": '''# schemas/base_schema.py
from typing import Any
from pydantic import BaseModel
class BaseResp(BaseModel):
    code: int
    msg: str
    data: Any = None
    @staticmethod
    def ok(data: Any = None, msg: str = "ok") -> "BaseResp":
        return BaseResp(code=0, msg=msg, data=data)
    @staticmethod
    def fail(code: int = 400, msg: str = "fail", data: Any = None) -> "BaseResp":
        return BaseResp(code=code, msg=msg, data=data)
''',
"services/base_service.py": '''# services/base_service.py
from typing import Any
from schemas.base_schema import BaseResp
class BaseService:
    """所有Service基类，统一返回封装"""
    @staticmethod
    def success(data: Any = None, msg: str = "ok") -> BaseResp:
        return BaseResp.ok(data=data, msg=msg)
    @staticmethod
    def fail(msg: str, code: int = 400, data: Any = None) -> BaseResp:
        return BaseResp.fail(code=code, msg=msg, data=data)
''',
"services/log_service.py": '''# services/log_service.py
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from utils.sse_log_helper import push_log
LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)
class SseLogHandler(logging.Handler):
    """自定义日志Handler，日志消息自动推送到SSE缓冲区"""
    def emit(self, record):
        try:
            line = self.format(record)
            push_log(line)
        except Exception:
            pass
logger = logging.getLogger("Env POC Scaffold")
logger.setLevel(logging.INFO)
logger.propagate = False
log_format = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(log_format)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
sse_handler = SseLogHandler()
sse_handler.setFormatter(log_format)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.addHandler(sse_handler)
''',
"utils/sse_log_helper.py": '''# utils/sse_log_helper.py
import asyncio
from collections import deque
log_buffer = deque(maxlen=200)
def push_log(line: str):
    log_buffer.append(line)
async def log_stream_generator():
    while True:
        if log_buffer:
            line = log_buffer.popleft()
            yield f"data: {line}\\n\\n"
        await asyncio.sleep(0.15)
''',
"utils/common.py": '''# utils/common.py
import re
import json
def parse_json_safely(raw: str):
    """剥离markdown ```json 标记，安全解析json"""
    raw = re.sub(r"```(json)?", "", raw).strip()
    return json.loads(raw)
def bayes_two_pair(
    prior_h: float,
    p_x_given_h: dict,
    p_x_given_not_h: dict,
    p_y_given_h_x: dict,
    p_y_given_not_h_x: dict,
    x_state: str,
    y_state: str,
    scale: float
) -> tuple[float, float]:
    """
    二元配对贝叶斯，用于一组耦合变量 (X,Y)
    返回：本组后验P(H|x,y)，缩放后的风险增量
    """
    ph = prior_h
    pnh = 1.0 - ph
    p_x_h = p_x_given_h[x_state]
    p_y_hx = p_y_given_h_x[(x_state, y_state)]
    p_x_nh = p_x_given_not_h[x_state]
    p_y_nhx = p_y_given_not_h_x[(x_state, y_state)]
    joint_h = ph * p_x_h * p_y_hx
    joint_nh = pnh * p_x_nh * p_y_nhx
    denom = joint_h + joint_nh
    if denom <= 0:
        return 0.0, 0.0
    post = joint_h / denom
    add_delta = post * scale
    return post, add_delta
''',
"utils/idol_helper.py": '''# utils/idol_helper.py
"""
Idol 轻量Agent助手
风格：极简、务实、工程向，适合本地ollama对话/工具调用
"""
import ollama
from typing import List, Dict, Optional
from config.app_config import cfg
from config.prompt_loader import get_prompt
from services.log_service import logger
class IdolAgent:
    def __init__(self, model: Optional[str] = None):
        self.model = model or cfg.ollama.model_name
        self.system_prompt = get_prompt("idol_agent")
        self.history: List[Dict[str, str]] = []
    def reset(self):
        """清空对话上下文"""
        self.history.clear()
    def add_user_msg(self, content: str):
        self.history.append({"role": "user", "content": content})
    def add_assistant_msg(self, content: str):
        self.history.append({"role": "assistant", "content": content})
    async def chat(self, user_msg: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        """单轮对话，自动维护历史上下文"""
        temp = temperature if temperature is not None else cfg.ollama.temperature
        maxtok = max_tokens if max_tokens is not None else cfg.ollama.max_tokens
        ollama.base_url = cfg.ollama.base_url
        self.add_user_msg(user_msg)
        messages = [{"role": "system", "content": self.system_prompt}] + self.history
        try:
            resp = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temp,
                    "num_predict": maxtok
                }
            )
            reply = resp["message"]["content"]
            self.add_assistant_msg(reply)
            return reply
        except Exception as e:
            logger.exception("idol agent chat error")
            return f"[IdolError] {str(e)}"
    async def quick_ask(self, user_msg: str, temperature: Optional[float] = None) -> str:
        """无记忆一次性问答，不写入history"""
        temp = temperature if temperature is not None else cfg.ollama.temperature
        ollama.base_url = cfg.ollama.base_url
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_msg}
        ]
        try:
            resp = ollama.chat(
                model=self.model,
                messages=messages,
                options={"temperature": temp}
            )
            return resp["message"]["content"]
        except Exception as e:
            logger.exception("idol quick ask error")
            return f"[IdolError] {str(e)}"
''',
"utils/validator.py": '''# utils/validator.py
from typing import Any
import re
def validate_no_special_char(v: str) -> str:
    """防危险特殊字符过滤，用于文本输入，禁止 ; $ " ' < > { }"""
    if re.search(r"[;$\"'<>{}]", v):
        raise ValueError("内容包含非法特殊字符")
    return v.strip()
def validate_positive_number(v: float | int) -> float | int:
    """校验数值必须大于0，温湿度、图片尺寸等场景"""
    if v <= 0:
        raise ValueError("数值必须大于0")
    return v
def validate_range(v: float, min_val: float, max_val: float) -> float:
    """通用范围校验：校验数字落在 [min_val, max_val]"""
    if not (min_val <= v <= max_val):
        raise ValueError(f"数值必须在 {min_val} ~ {max_val} 之间")
    return v
class CommonValidators:
    """Pydantic 可复用校验器类，直接 @field_validator 调用"""
    @classmethod
    def str_strip(cls, v: Any) -> Any:
        """字符串自动去除首尾空白，非字符串原样返回"""
        if isinstance(v, str):
            return v.strip()
        return v
''',
"utils/knowledge_loader.py": '''# utils/knowledge_loader.py
import os
from typing import Dict
KNOWLEDGE_DIR = "knowledge"
def load_knowledge_file(file_name: str) -> str:
    """读取 knowledge 下单个md文件，不带后缀或者带.md都可以"""
    if not file_name.endswith(".md"):
        file_name = f"{file_name}.md"
    fp = os.path.join(KNOWLEDGE_DIR, file_name)
    if not os.path.exists(fp):
        raise FileNotFoundError(f"知识库文件不存在：{file_name}")
    with open(fp, "r", encoding="utf-8") as f:
        return f.read()
def load_all_knowledge() -> Dict[str, str]:
    """一次性加载全部md，key为文件名（去掉.md后缀）"""
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    res = {}
    for fname in os.listdir(KNOWLEDGE_DIR):
        if fname.lower().endswith(".md"):
            key = os.path.splitext(fname)[0]
            with open(os.path.join(KNOWLEDGE_DIR, fname), "r", encoding="utf-8") as f:
                res[key] = f.read()
    return res
''',
"utils/image_helper.py": '''# utils/image_helper.py
import base64
from pathlib import Path
from typing import Union, Optional

SUPPORTED_SUFFIX = {".jpg", ".jpeg", ".png", ".webp"}


def image_to_base64(source: Union[str, Path, bytes]) -> str:
    """
    图片转base64，返回纯b64串，**不带data URI前缀**，直接给ollama/moondream接口使用
    :param source: 图片文件路径字符串 / Path对象 / 图片二进制bytes
    :return: 裸base64字符串
    """
    if isinstance(source, bytes):
        raw = source
    else:
        p = Path(source)
        suffix = p.suffix.lower()
        if suffix not in SUPPORTED_SUFFIX:
            raise ValueError(f"不支持图片格式: {suffix}，支持{SUPPORTED_SUFFIX}")
        raw = p.read_bytes()
    return base64.b64encode(raw).decode("utf-8")


def base64_to_image(b64_str: str, out_path: Union[str, Path]) -> None:
    """
    base64还原保存为本地图片文件
    :param b64_str: 裸base64字符串（不要带data:image前缀）
    :param out_path: 输出文件路径
    """
    raw = base64.b64decode(b64_str)
    Path(out_path).write_bytes(raw)
''',
"routers/logview_router.py": '''# routers/logview_router.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from utils.sse_log_helper import log_stream_generator
router = APIRouter()
@router.get("/stream")
async def log_stream():
    """SSE实时日志流"""
    return StreamingResponse(log_stream_generator(), media_type="text/event-stream")
''',
"routers/tools_router.py": '''# routers/tools_router.py
from fastapi import APIRouter, UploadFile, File
from schemas.base_schema import BaseResp
from utils.image_helper import image_to_base64

router = APIRouter(prefix="/tools", tags=["开发小工具"])

@router.post("/img2b64/api")
async def img2b64_api(file: UploadFile = File(...)):
    """接收上传图片，返回纯裸base64字符串，适配ollama images参数"""
    raw_bytes = await file.read()
    b64 = image_to_base64(raw_bytes)
    return BaseResp.ok(data={"b64": b64})
''',
"html_basic/static/index.html": '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>人居微环境视觉检测系统</title>
<style>
* {
margin: 0;
padding: 0;
box-sizing: border-box;
font-family: system-ui, sans-serif;
}
body {
height: 100vh;
overflow: hidden;
}
.container {
display: flex;
height: 100%;
}
.sidebar {
width: 220px;
background-color: #2c3e50;
color: #fff;
padding-top: 24px;
transition: 0.3s;
}
.sidebar .menu-item {
padding: 14px 24px;
cursor: pointer;
font-size: 16px;
}
.sidebar .menu-item:hover {
background-color: #34495e;
}
.sidebar .menu-item.active {
background-color: #3498db;
}
.main-content {
flex: 1;
height: 100%;
}
#content-iframe {
width: 100%;
height: 100%;
border: none;
}
.hamburger {
display: none;
position: fixed;
top: 12px;
left: 12px;
z-index: 99;
background: #2c3e50;
color: white;
border: none;
padding: 8px 12px;
font-size: 18px;
}
@media (max-width:768px){
.hamburger {
display: block;
}
.sidebar {
position: fixed;
left: -220px;
height: 100%;
z-index: 98;
}
.sidebar.open {
left: 0;
}
}
</style>
</head>
<body>
<button class="hamburger" id="hamburger">☰</button>
<div class="container">
<aside class="sidebar" id="sidebar">
<div class="menu-item active" data-src="index_day.html">图片评估</div>
<div class="menu-item" data-src="mold_detect.html">视频轮巡</div>
<div class="menu-item" data-src="img2b64.html">图片B64工具</div>
<div class="menu-item" data-src="help.html">使用帮助</div>
</aside>
<main class="main-content">
<iframe id="content-iframe" src="index_day.html"></iframe>
</main>
</div>
<script>
const menuItems = document.querySelectorAll('.menu-item');
const iframe = document.getElementById('content-iframe');
const hamburger = document.getElementById('hamburger');
const sidebar = document.getElementById('sidebar');
menuItems.forEach(item => {
item.addEventListener('click', ()=>{
menuItems.forEach(mi=>mi.classList.remove('active'));
item.classList.add('active');
const pageUrl = item.getAttribute('data-src');
iframe.src = pageUrl;
if(window.innerWidth <=768){
sidebar.classList.remove('open');
}
})
})
hamburger.addEventListener('click',()=>{
sidebar.classList.toggle('open');
})
</script>
</body>
</html>''',
"html_basic/static/img2b64.html": '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>图片转 Ollama Base64</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui}
body{padding:24px;max-width:900px;margin:0 auto}
.upload{border:2px dashed #aaa;border-radius:10px;padding:32px;text-align:center;margin-bottom:16px;cursor:pointer}
.upload:hover{border-color:#444}
#preview{max-height:240px;margin:12px 0}
textarea{width:100%;height:260px;padding:10px;font-family:monospace}
button{padding:8px 16px;margin-top:8px;cursor:pointer}
.tip{color:#666;margin:8px 0;font-size:14px}
</style>
</head>
<body>
<h2>图片转 Ollama Base64</h2>
<p class="tip">输出纯base64，不带 data:image 前缀，直接给 ollama images 字段使用</p>
<div class="upload" id="uploadArea">
<input type="file" id="fileInput" accept="image/jpeg,image/png,image/webp" style="display:none">
<div>点击上传图片</div>
<img id="preview">
</div>
<textarea id="result" readonly placeholder="base64 输出在这里"></textarea>
<br>
<button id="copyBtn">复制</button>
<script>
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const result = document.getElementById('result');
const copyBtn = document.getElementById('copyBtn');

uploadArea.onclick = ()=>fileInput.click();
fileInput.onchange = async ()=>{
const f = fileInput.files[0];
if(!f) return;
const reader = new FileReader();
reader.onload = e=>preview.src = e.target.result;
reader.readAsDataURL(f);

const fd = new FormData();
fd.append('file', f);
const resp = await fetch('/api/v1/tools/img2b64/api', {method:'POST', body:fd});
const data = await resp.json();
result.value = data.data.b64;
}
copyBtn.onclick = async ()=>{
await navigator.clipboard.writeText(result.value);
alert('已复制');
}
</script>
</body>
</html>
''',
"main.py": '''# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from services.log_service import logger
from routers.logview_router import router as logview_router

# 开发小工具路由（容错导入，没有文件也不崩溃）
try:
    from routers.tools_router import router as tools_router
except ImportError:
    tools_router = None

# --- demo标记会被生成脚本替换，请勿修改这行注释 ---
DEMO_MODE = False
if DEMO_MODE:
    from routers.sleep_router import router as sleep_router

os.makedirs("./tmp", exist_ok=True)
app = FastAPI(title="Env POC Scaffold", version="0.5.0")
app.mount("/html_basic/static", StaticFiles(directory="html_basic/static"), name="static")
app.include_router(logview_router, prefix="/logview")

# 注册工具路由
if tools_router is not None:
    app.include_router(tools_router, prefix="/api/v1")

if DEMO_MODE:
    app.include_router(sleep_router, prefix="/api/v1/sleep")

@app.get("/", tags=["首页"])
async def root():
    logger.info("访问根路径")
    return RedirectResponse(url="/html_basic/static/index.html")
if __name__ == "__main__":
    import uvicorn
    logger.info("服务启动 v0.5.0")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
''',
"requirements.txt": '''# requirements.txt
# ========== 核心必选 ==========
fastapi
uvicorn[standard]
pydantic>=2.0
pydantic-settings
python-multipart
ollama
# ========== 可选扩展（llm/图像） ==========
Pillow
# passlib[bcrypt]
''',
}
ext_tpl = {
"services/llm_base_service.py": '''# services/llm_base_service.py
import ollama
from typing import Optional
from config.app_config import cfg
from services.base_service import BaseService
from services.log_service import logger
class LlmBaseService(BaseService):
    @staticmethod
    async def chat(
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        model_name = model or cfg.ollama.model_name
        temp = temperature if temperature is not None else cfg.ollama.temperature
        maxtok = max_tokens if max_tokens is not None else cfg.ollama.max_tokens
        ollama.base_url = cfg.ollama.base_url
        try:
            resp = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": temp,
                    "num_predict": maxtok
                }
            )
            return LlmBaseService.success(data=resp)
        except Exception as e:
            logger.exception("ollama chat failed")
            return LlmBaseService.fail(msg=f"大模型调用失败：{str(e)}")
    @staticmethod
    async def vision(
        prompt: str,
        image_bytes: bytes,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        model_name = model or cfg.ollama.model_name
        temp = temperature if temperature is not None else cfg.ollama.temperature
        maxtok = max_tokens if max_tokens is not None else cfg.ollama.max_tokens
        ollama.base_url = cfg.ollama.base_url
        try:
            resp = ollama.chat(
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [image_bytes]
                }],
                options={
                    "temperature": temp,
                    "num_predict": maxtok
                }
            )
            return LlmBaseService.success(data=resp)
        except Exception as e:
            logger.exception("ollama vision failed")
            return LlmBaseService.fail(msg=f"视觉模型调用失败：{str(e)}")
''',
"services/user_service.py": '''# services/user_service.py
from services.dao.app_user_dao import (
    get_user_by_username as dao_get_user_by_username,
    create_user as dao_create_user
)
from utils.security import get_password_hash, verify_password
from typing import Optional, Dict
def get_user_by_username(username: str):
    return dao_get_user_by_username(username)
def create_user(username: str, password: str, nickname: str = None):
    hashed_pw = get_password_hash(password)
    return dao_create_user(username, hashed_pw, nickname)
def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user
''',
"utils/security.py": '''# utils/security.py
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
''',
"schemas/env_schema.py": '''# schemas/env_schema.py
from pydantic import BaseModel
from utils.validator import validate_range
class EnvInput(BaseModel):
    temp: float
    humidity: float
    @classmethod
    def check_temp(cls, v):
        return validate_range(v, 0, 50)
    @classmethod
    def check_hum(cls, v):
        return validate_range(v, 0, 100)
'''
}
demo_tpl = {
"schemas/sleep_env_schema.py": '''# schemas/sleep_env_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
class VisionObs(BaseModel):
    air_hint: Optional[str] = None
    mold_moisture: Optional[str] = None
    vent_condition: Optional[str] = None
    furniture_layout: Optional[str] = None
    electronics: Optional[str] = None
    bed_occlusion: Optional[str] = None
    bedding_status: Optional[str] = None
    mattress_situation: Optional[str] = None
    clutter_level: Optional[str] = None
    dust_accumulation: Optional[str] = None
    window_curtain: Optional[str] = None
    light_source: Optional[str] = None
    wall_ceiling: Optional[str] = None
    odor_cue: Optional[str] = None
    space_type: Optional[str] = None
    infer_cost_sec: Optional[float] = None
    __raw_text__: Optional[str] = Field(default=None, alias="__raw_text__")
class SleepEnvEvalReq(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2: Optional[float] = None
    noise: Optional[float] = None
    illuminance: Optional[float] = None
    sleep_start_hour: Optional[int] = None
    mold_risk_level: Optional[str] = None
    vision_obs: Optional[VisionObs] = None
class SleepEnvEvalResp(BaseModel):
    riskLevel: str
    riskClass: str
    desc: str
    suggest: str
    extraNote: str
    bayes: Dict[str, Any]
''',
"services/sleep_env_service.py": '''# services/sleep_env_service.py
from fastapi import HTTPException
from schemas.sleep_env_schema import SleepEnvEvalReq, SleepEnvEvalResp
from services.log_service import logger
from utils.common import bayes_two_pair
RULES = [
    # 此处为业务规则占位，实际使用填充规则列表
]
GRADE_MAP = [
    {"min_p": 0.70, "level": "高风险", "cls": "risk-high"},
    {"min_p": 0.40, "level": "中风险", "cls": "risk-mid"},
    {"min_p": 0.0, "level": "低风险", "cls": "risk-low"},
]
def filter_conflict_rules(hit_ids: list) -> list:
    """冲突规则过滤占位"""
    return hit_ids
class SleepEnvService:
    @staticmethod
    async def evaluate(req: SleepEnvEvalReq) -> SleepEnvEvalResp:
        vision = req.vision_obs
        logger.info(f"[SleepEval] temp={req.temperature}, hum={req.humidity}, sleep_start_hour={req.sleep_start_hour}")
        if vision:
            logger.info(f"[SleepEval] vision_obs={vision.model_dump(by_alias=True)}")
        hit_ids = []
        desc_items = []
        suggest_items = []
        trace = []
        posterior = 0.0
        for rule in RULES:
            if rule["test"](vision, req):
                hit_ids.append(rule["id"])
        hit_ids = filter_conflict_rules(hit_ids)
        rule_map = {r["id"]: r for r in RULES}
        for rid in hit_ids:
            rule = rule_map[rid]
            d = rule["desc"](vision, req) if callable(rule["desc"]) else rule["desc"]
            s = rule["suggest"]
            desc_items.append(d)
            suggest_items.append(s)
            trace.append(f"rule:{rid} +{rule['delta']}")
            posterior += rule["delta"]
        # -------- 湿度‑霉菌二元贝叶斯耦合计算 --------
        BAYES_RH_MOLD_CONF = {
            "prior_h": 0.10,
            "p_x_given_h": {"high": 0.60, "normal": 0.30},
            "p_x_given_not_h": {"high": 0.20, "normal": 0.75},
            "p_y_given_h_x": {("high", "yes"):0.90, ("high","no"):0.10, ("normal","yes"):0.40, ("normal","no"):0.60},
            "p_y_given_not_h_x": {("high","yes"):0.30, ("high","no"):0.70, ("normal","yes"):0.08, ("normal","no"):0.92},
            "scale":0.22
        }
        if req.humidity is not None and req.humidity > 55:
            rh_state = "high"
        else:
            rh_state = "normal"
        m_state = "no"
        if vision and vision.mold_moisture:
            if "mold" in vision.mold_moisture or "damp" in vision.mold_moisture:
                m_state = "yes"
        post_rh_mold, add_rh_mold = bayes_two_pair(
            prior_h=BAYES_RH_MOLD_CONF["prior_h"],
            p_x_given_h=BAYES_RH_MOLD_CONF["p_x_given_h"],
            p_x_given_not_h=BAYES_RH_MOLD_CONF["p_x_given_not_h"],
            p_y_given_h_x=BAYES_RH_MOLD_CONF["p_y_given_h_x"],
            p_y_given_not_h_x=BAYES_RH_MOLD_CONF["p_y_given_not_h_x"],
            x_state=rh_state,
            y_state=m_state,
            scale=BAYES_RH_MOLD_CONF["scale"]
        )
        trace.append(f"bayes:rh‑mold | post={post_rh_mold:.4f} +{add_rh_mold:.4f}")
        posterior += add_rh_mold
        if rh_state == "high" and m_state == "yes":
            if add_rh_mold < 0.20:
                trace.append(f"bayes:rh‑mold safeguard, override +0.20")
                posterior -= add_rh_mold
                add_rh_mold = 0.20
                posterior += add_rh_mold
        evidence_count = len(hit_ids) + 1
        posterior = min(posterior, 0.95)
        riskLevel, riskClass = "低风险", "risk-low"
        for g in GRADE_MAP:
            if posterior >= g["min_p"]:
                riskLevel, riskClass = g["level"], g["cls"]
                break
        desc_str = "；".join(desc_items) if desc_items else "综合评估结果：低风险"
        suggest_str = "；".join(suggest_items) if suggest_items else "卧室环境条件良好，保持现有通风与温湿度即可。"
        raw_text = vision.model_dump().get("__raw_text__", "") if vision else ""
        space_type = vision.model_dump().get("space_type", "") if vision else ""
        if space_type and "卧室" != space_type.lower():
            raise HTTPException(status_code=400, detail="识别非卧室场景，请上传卧室照片进行评估")
        extraNote = f"{raw_text}" if raw_text else "单环境评估，无异常风险"
        return SleepEnvEvalResp(
            riskLevel=riskLevel,
            riskClass=riskClass,
            desc=desc_str,
            suggest=suggest_str,
            extraNote=extraNote,
            bayes={
                "posterior": round(posterior,2),
                "trace": trace,
                "evidence_count": evidence_count
            }
        )
''',
"routers/sleep_router.py": '''# routers/sleep_router.py
from fastapi import APIRouter
from schemas.sleep_env_schema import SleepEnvEvalReq, SleepEnvEvalResp
from services.sleep_env_service import SleepEnvService
router = APIRouter()
@router.post("/eval", response_model=SleepEnvEvalResp)
async def sleep_env_eval(req: SleepEnvEvalReq):
    return await SleepEnvService.evaluate(req)
''',
"html_basic/static/index_day.html": '''<!-- demo页面占位，实际使用拷贝业务页面完整html -->''',
"html_basic/static/mold_analyze.html": '''<!-- demo页面占位 -->''',
"html_basic/static/mold_detect.html": '''<!-- demo页面占位 -->''',
"html_basic/static/help.html": '''<!-- demo页面占位 -->''',
}
def write_file(filepath: str, content: str):
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ {filepath}")
def main():
    parser = argparse.ArgumentParser(description="FastAPI脚手架生成器｜v0.5.0｜支持自定义项目名")
    parser.add_argument("--name", default="Env POC Scaffold", help="项目名称")
    parser.add_argument("--ext", action="store_true", help="同时生成可选扩展文件(llm/user)")
    parser.add_argument("--demo", action="store_true", help="生成睡眠环境评估完整业务Demo")
    args = parser.parse_args()
    proj_name = args.name
    print(f"=== 开始生成脚手架【{proj_name}】 v0.5.0 ===")
    for fp, txt in core_tpl.items():
        write_file(fp, render_text(txt, proj_name))
    if args.ext:
        print("\n=== 开始生成扩展文件 ===")
        for fp, txt in ext_tpl.items():
            write_file(fp, render_text(txt, proj_name))
    if args.demo:
        print("\n=== 开始生成睡眠评估Demo业务代码 ===")
        for fp, txt in demo_tpl.items():
            write_file(fp, render_text(txt, proj_name))
        # 修改main.py开启DEMO_MODE=True
        main_path = "main.py"
        with open(main_path, "r", encoding="utf-8") as f:
            main_content = f.read()
        main_content = main_content.replace("DEMO_MODE = False", "DEMO_MODE = True")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(main_content)
    for d in ("knowledge", "log", "tmp"):
        os.makedirs(d, exist_ok=True)
    print("\n🎉 脚手架 v0.5.0 生成完成！")
    print("使用示例：")
    print("  python gen_scaffold_v05.py --name myproj")
    print("  python gen_scaffold_v05.py --name myproj --ext --demo")
    print("\n👉图片B64调试工具页面地址： /html_basic/static/img2b64.html")
if __name__ == "__main__":
    main()

