from domains.good_domain.wall.rules import GOODWALL_PROMPT
from domains.good_domain.cloth.schema import ClothClassifyReq, ClothClassifyResp
from domains.good_domain.cloth.service import cloth_classify
from fastapi import APIRouter, HTTPException
from common.vision_client import vision_predict
from domains.good_domain.cloth.rules import CLOTH_PROMPT
from domains.good_domain.wall.schema import GoodWallClassifyReq, GoodWallClassifyResp
from domains.good_domain.wall.service import goodwall_classify

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
