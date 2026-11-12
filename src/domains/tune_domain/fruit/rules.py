FRUIT_PROMPT = """Describe the image objectively. Only tell the visual features of the fruit, do not judge disease, do not output json or coordinate data."""

FRUIT_TYPE_MAP = {
    1: "未成熟，颜色偏青硬实",
    2: "最佳成熟度，色泽饱满适合立即食用",
    3: "局部腐坏，小面积斑点/软烂",
    4: "大面积腐烂，发霉流水，不建议食用",
    99: "图片不是果蔬，无效图片"
}

WARNING_TEXT = "仅外观参考，不能作为食品安全判定唯一依据。"

KEY_MAP = {
    1: ["unripe", "green", "hard", "not mature"],
    2: ["ripe", "full color", "fresh", "ready to eat"],
    3: ["small spot", "partial rot", "soft spot"],
    4: ["mold", "rotten", "decay", "mushy", "wet"],
    99: ["not fruit", "no fruit", "book", "wall", "human"]
}
