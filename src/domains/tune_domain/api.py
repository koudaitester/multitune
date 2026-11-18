from fastapi import APIRouter, HTTPException
from domains.tune_domain.plant.schema import PlantTuneIn, PlantTuneOut
from domains.tune_domain.pet.schema import PetTuneIn, PetTuneOut
from domains.tune_domain.plant.service import plant_tune_service
from domains.tune_domain.pet.service import pet_tune_service
from common.vision_client import vision_predict
from domains.tune_domain.plant.rules import PLANT_PROMPT
from domains.tune_domain.pet.rules import PET_PROMPT
from domains.tune_domain.fruit.rules import FRUIT_PROMPT
from domains.tune_domain.gut.rules import GUTTUNE_PROMPT
from domains.tune_domain.fruit.schema import FruitClassifyReq, FruitClassifyResp
from domains.tune_domain.fruit.service import fruit_classify
from domains.tune_domain.gut.schema import GutAnalyzeRequest, GutAnalyzeResponse
from domains.tune_domain.gut.service import analyze_gut


router = APIRouter(prefix="/tune", tags=["活体调校域"])

@router.post("/plant", response_model=PlantTuneOut)
async def plant_tune(req: PlantTuneIn):
    raw_text = await vision_predict(req.img_b64, PLANT_PROMPT)
    if not raw_text:
        raise HTTPException(status_code=500, detail="调用视觉模型失败")
    result = await plant_tune_service(raw_text, req.tag)
    return result

@router.post("/pet", response_model=PetTuneOut)
async def pet_tune(req: PetTuneIn):
    raw_text = await vision_predict(req.img_b64, PET_PROMPT)
    if not raw_text:
        raise HTTPException(status_code=500, detail="调用视觉模型失败")
    result = await pet_tune_service(raw_text, req.tag)
    return result

@router.post("/fruit", response_model=FruitClassifyResp)
async def fruit_evaluate(req: FruitClassifyReq):
    # 调用common vision_client拿到moondream raw文本
    raw_text = await vision_predict(req.image_b64, FRUIT_PROMPT)
    if not raw_text:
        raise HTTPException(status_code=500, detail="调用视觉模型失败")
    return await fruit_classify(raw_text)

@router.post("/gut", response_model=GutAnalyzeResponse)
async def guttune_analyze(req: GutAnalyzeRequest):
    # 这里调用Moondream视觉模型，传入image_b64，拿到图片描述文本
    raw_text = await vision_predict(req.image_b64, GUTTUNE_PROMPT)
    print("==== Moondream RAW OUTPUT ====")
    print(raw_text)
    print("==============================")
    # ============插桩调试用，测试的时候直接写死返回文本，正式启用再替换上面========
    # raw_text = "the image shows smooth sausage shaped stool"
    # ==========================================================================
    result = analyze_gut(raw_text)
    return result