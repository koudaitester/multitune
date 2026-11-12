PET_PROMPT = """Describe this cat/dog simply and objectively.
Only visual facts: fur condition, skin spots, wounds, hair loss, dirty coat.
Do NOT give diagnosis, conclusion or medical advice.
No json, no bounding boxes, only plain english text.
"""

PET_TYPE_MAP = {
    1: "皮毛状态良好，毛发顺滑",
    2: "局部掉毛、毛发稀疏",
    3: "皮肤红斑/斑点",
    4: "体表伤口、破皮",
    99: "图片不是猫狗，请拍摄宠物清晰特写"
}

PET_ADVICE_MAP = {
    1: "保持常规洗护，持续观察皮毛状态",
    2: "留意是否频繁抓挠；排查环境过敏源，持续掉毛建议就医",
    3: "观察宠物抓挠行为；斑点扩大请及时带去宠物医院",
    4: "保持伤口清洁，尽快带去宠物医院处理",
    99: "请拍摄猫狗主体清晰照片，尽量包含皮毛皮肤区域"
}

PET_NOT_TARGET_KEYWORDS = ["plant","flower","table","food","screenshot","human","screen"]

PET_SCALE_KEYWORDS = [
    (1, ["smooth fur","shiny coat","healthy fur"]),
    (2, ["hair loss","bald patch","thin fur"]),
    (3, ["red spot","skin rash","skin discolor"]),
    (4, ["wound","cut","scratch","bleeding"]),
]

PET_WARNING = "⚠️本工具仅爱好者外观参考，不能替代执业兽医诊断；外观异常有多种成因，持续异常请带去宠物医院。"
