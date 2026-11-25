from domains.good_domain.wall.rules import GOODWALL_PROMPT
from domains.good_domain.cloth.schema import ClothClassifyReq, ClothClassifyResp
from domains.good_domain.cloth.service import cloth_classify
from fastapi import APIRouter, HTTPException
from common.vision_client import vision_predict
from domains.good_domain.cloth.rules import CLOTH_PROMPT
from domains.good_domain.wall.schema import GoodWallClassifyReq, GoodWallClassifyResp
from domains.good_domain.wall.service import goodwall_classify
from domains.good_domain.oldman_space.service import MoldOldManEvalService
from domains.good_domain.oldman_space.schema import OldManVisualEvalRequest, OldManVisualEvalResponse
from domains.good_domain.oldman_space.rules import OLDMAN_SPACE_PROMPT
from domains.good_domain.env_monitor.schema import EnvMonitorReq, EnvMonitorResp
from domains.good_domain.env_monitor.service import evaluate_env
from domains.good_domain.env_monitor.rules import ENV_MONITOR_PROMPT
from domains.good_domain.mold.schema import MoldReq, MoldResp
from domains.good_domain.mold.service import evaluate_mold
from domains.good_domain.mold.rules import MOLD_PROMPT
from domains.good_domain.moon_site.visual import (
    MOON_PROMPT, REGION_PROMPT, MoonReq, MoonResp, analyze_surface,
)
from domains.good_domain.crater.schema import CraterDoubleReq, CraterDoubleResp
from domains.good_domain.crater.service import crater_double_image_verify
from domains.good_domain.crater.rules import CRATER_OVERVIEW_PROMPT, CRATER_DETAIL_PROMPT
from .env_note.schema import EnvNoteCreate, EnvNoteItem
from .env_note.service import add_note, list_note
from typing import Optional

router = APIRouter(prefix="/good", tags=["介质品质域"])

@router.post("/cloth", response_model=ClothClassifyResp)
async def cloth_evaluate(req: ClothClassifyReq):
    raw_text = await vision_predict(req.image_b64, CLOTH_PROMPT)
    raw_text = "clean cloth, no stain, intact"
    return await cloth_classify(raw_text)

@router.post("/goodwall", response_model=GoodWallClassifyResp)
async def goodwall_evaluate(req: GoodWallClassifyReq):
    raw_text = await vision_predict(req.image_b64, GOODWALL_PROMPT)
    raw_text = "intact wall, no crack, clean surface"
    return await goodwall_classify(raw_text)

@router.post("/oldman", response_model=OldManVisualEvalResponse)
async def oldman_visual_eval(req: OldManVisualEvalRequest):
    raw_text = await vision_predict(req.image_b64, OLDMAN_SPACE_PROMPT)
    raw_text = ""
    result = await MoldOldManEvalService.evaluate(raw_text)
    return result

@router.post("/env", response_model=EnvMonitorResp)
async def env_monitor(req: EnvMonitorReq):
    raw_text = await vision_predict(req.image_b64, ENV_MONITOR_PROMPT)
    if not raw_text:
        raise HTTPException(status_code=500, detail="调用视觉模型失败")
    return evaluate_env(raw_text)


@router.post("/mold", response_model=MoldResp)
async def mold_evaluate(req: MoldReq):
    # 霉菌风险：视觉描述提取特征，温湿度（若传）参与加权；没传就不猜
    raw_text = await vision_predict(req.image_b64, MOLD_PROMPT)
    if not raw_text:
        raise HTTPException(status_code=500, detail="调用视觉模型失败")
    return evaluate_mold(raw_text, req.humidity, req.temperature)


@router.post("/moon", response_model=MoonResp)
async def moon_surface(req: MoonReq):
    # 行星表面预筛：只对照片能观测的项打分，需要外部数据的项单列不参与加权。
    # view 由调用方声明（地面近景 / 远景俯瞰），两种尺度用不同 prompt 与不同判分：
    # 同一套近场阈值套在远景上，会把远处坑壁当成脚下坡面。
    is_region = (req.view or "ground").strip().lower() == "region"
    prompt = REGION_PROMPT if is_region else MOON_PROMPT
    raw_text = await vision_predict(req.image_b64, prompt)
    if not raw_text:
        raise HTTPException(status_code=500, detail="调用视觉模型失败")
    return analyze_surface(raw_text, req.view)

@router.post("/mars_site", response_model=MoonResp)
async def mars_surface(req: MoonReq):
    # 行星表面预筛：只对照片能观测的项打分，需要外部数据的项单列不参与加权。
    # view 由调用方声明（地面近景 / 远景俯瞰），两种尺度用不同 prompt 与不同判分：
    # 同一套近场阈值套在远景上，会把远处坑壁当成脚下坡面。
    is_region = (req.view or "ground").strip().lower() == "region"
    prompt = REGION_PROMPT if is_region else MOON_PROMPT
    raw_text = await vision_predict(req.image_b64, prompt)
    if not raw_text:
        raise HTTPException(status_code=500, detail="调用视觉模型失败")
    return analyze_surface(raw_text, req.view)

@router.post("/env-note/add", response_model=EnvNoteItem)
def env_note_add(payload: EnvNoteCreate):
    return add_note(payload)

@router.get("/env-note/list")
def env_note_list(start:Optional[str]=None, end:Optional[str]=None):
    return list_note(start, end)

@router.post("/crater", response_model=CraterDoubleResp)
async def crater_verify(req: CraterDoubleReq):
    """陨石坑双图校验：远景全貌 + 近景局部，联合判断是否撞击坑"""
    raw_overview = await vision_predict(req.image_overview_b64, CRATER_OVERVIEW_PROMPT)
    raw_detail = await vision_predict(req.image_detail_b64, CRATER_DETAIL_PROMPT)
    if not raw_overview or not raw_detail:
        raise HTTPException(status_code=500, detail="视觉模型调用失败，远景或近景图无返回")
    return await crater_double_image_verify(raw_overview, raw_detail)
