GOODWALL_PROMPT = """Describe the image objectively. Only tell the visual features of the wall surface, do not judge anything else, do not output json or coordinate data."""

GOODWALL_TYPE_MAP = {
    1: "墙面完好，无破损水渍裂纹",
    2: "细微裂纹，发丝小裂缝",
    3: "起皮脱落，墙皮剥落",
    4: "大片水渍、受潮印记",
    99: "图片不是墙面，无效图片"
}

WARNING_TEXT = "仅外观肉眼参考，无法检测墙体内部渗水与结构性隐患。"

KEY_MAP = {
    1: ["intact wall", "no crack", "clean surface"],
    2: ["fine crack", "small crack", "hairline crack"],
    3: ["peeling paint", "flaking", "wall peel off"],
    4: ["water stain", "wet mark", "moisture stain"],
    99: ["not wall", "no wall", "fruit", "cloth", "plant"]
}
