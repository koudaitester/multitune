CLOTH_PROMPT = """Describe the image objectively. Only tell the visual features of the clothing, do not judge anything else, do not output json or coordinate data."""

CLOTH_TYPE_MAP = {
    1: "衣物干净，无明显污渍破损",
    2: "局部污渍，小面积脏点",
    3: "大面积脏污，多处污渍",
    4: "布料破损、破洞撕裂",
    99: "图片不是衣物，无效图片"
}

WARNING_TEXT = "仅外观肉眼参考，无法识别深层油渍与微观细菌。"

KEY_MAP = {
    1: ["clean", "no stain", "intact"],
    2: ["small stain", "spot", "local dirt"],
    3: ["large stain", "many spots", "dirty all over"],
    4: ["hole", "tear", "ripped", "broken fabric"],
    99: ["not clothing", "no cloth", "wall", "fruit", "plant"]
}
