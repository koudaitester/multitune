import json
from datetime import datetime
from pathlib import Path

LOG_PATH = "tools/add_gut_log/gut_tune_log.json"

def add_log_entry(image_filename: str, human_label: str, moondream_raw: str, notes: str):
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "image_filename": image_filename,
        "human_label": human_label,
        "moondream_raw": moondream_raw,
        "prompt_version": "golden_3stage_v1",
        "notes": notes
    }
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_data = json.load(f)
    except FileNotFoundError:
        log_data = []
    log_data.append(new_entry)
    with open(LOG_PATH, "w", encoding="utf-8") as f:

        json.dump(log_data, f, indent=2, ensure_ascii=False)
    print("✅ 日志条目已写入")

# ============ 使用示例 ============
# 填入本次样本信息，直接调用函数
# add_log_entry(
#     image_filename="sample_002.jpg",
#     human_label="Bristol Type4，光滑香肠状，几乎无裂纹",
#     moondream_raw="", # 跑模型后把raw output填在这里
#     notes="干扰项：马桶白色背景、积水反光、有薄纸巾粘连"
# )
