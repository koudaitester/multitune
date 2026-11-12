# PlantTune 业务规则，仅本域使用
PLANT_PROMPT = """Describe this potted plant and soil simply and objectively.
Only describe visual facts: leaf color, wilting, spots, soil dry or wet.
Do NOT give diagnosis, conclusion or care advice.
No json, no bounding boxes, only plain english text.
"""

TYPE_MAP = {
    1: "植株状态看起来良好，叶片翠绿舒展",
    2: "叶片萎蔫下垂，有缺水外观表现",
    3: "叶片存在晒斑、叶尖焦枯，光照可能过强",
    4: "盆土潮湿，存在积水过涝嫌疑",
    5: "叶片出现斑点、孔洞，怀疑虫害或叶部病害",
    99: "图片不是盆栽，请拍摄完整盆栽特写"
}

ADVICE_MAP = {
    1: "维持现有浇水与光照条件，继续观察",
    2: "优先检查盆土干湿；若土壤干燥可适度浇透水，避免频繁少量浇水",
    3: "避免正午强光直射，挪至散射光位置，修剪已经焦枯的叶片",
    4: "停止浇水，保证花盆排水通畅；不要仅凭叶片状态大量补水，优先查看根系情况",
    5: "翻看叶片背面，排查小虫、蛛网；情况持续建议查阅园艺资料",
    99: "请拍摄盆栽植株+盆土的清晰照片"
}

NOT_TARGET_KEYWORDS = ["wall","table","food","screenshot","human","animal","screen"]

SCALE_KEYWORDS = [
    (1, ["green leaves","lush","healthy","vibrant green"]),
    (2, ["wilting","drooping leaves","wilted","dry soil"]),
    (3, ["brown tips","burnt","scorch","sunburn","brown spots"]),
    (4, ["wet soil","soggy soil","moist wet soil"]),
    (5, ["black spots","holes on leaf","speckles","webbing","mottled spots"]),
]

WARNING = "⚠️本工具仅爱好者参考，不能替代专业园艺诊断；相同外观可能对应多种成因，请结合盆土、环境综合判断。"
