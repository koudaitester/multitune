"""
gen_case_template.py
读取rules生成case模板，自动追加到cases.json，自带module+type去重，兼容空json文件
"""
import json
import importlib.util
from pathlib import Path
from typing import List, Dict


def load_rules(rules_file_path: str) -> Dict:
    """动态导入rules.py，读取*_TYPE_MAP"""
    path = Path(rules_file_path)
    spec = importlib.util.spec_from_file_location("rules", path)
    rules_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rules_module)

    type_map = None
    for attr in dir(rules_module):
        if attr.endswith("TYPE_MAP"):
            type_map = getattr(rules_module, attr)
            break
    if not type_map:
        raise RuntimeError("rules.py 找不到 *TYPE_MAP")
    return type_map


def generate_cases(type_map: Dict, module_name: str) -> List[Dict]:
    case_list = []
    for tid in type_map.keys():
        case_list.append({
            "module": module_name,
            "case_name": "",
            "expect_type_id": int(tid)
        })
    return case_list


def append_cases(case_path: str, new_cases: List[Dict]):
    p = Path(case_path)
    old_data = []
    if p.exists():
        raw = p.read_text(encoding="utf-8").strip()
        if raw:  # 非空才解析
            with open(p, "r", encoding="utf-8") as f:
                old_data = json.load(f)
        else:
            print(f"⚠️ {case_path} 文件为空，初始化为空数组")

    # 去重：(模块名，预期type_id)作为唯一key
    exist_set = set()
    for item in old_data:
        exist_set.add((item["module"], item["expect_type_id"]))

    add_list = []
    for c in new_cases:
        key = (c["module"], c["expect_type_id"])
        if key not in exist_set:
            add_list.append(c)

    old_data.extend(add_list)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(old_data, f, ensure_ascii=False, indent=2)
    return add_list


if __name__ == "__main__":
    # ========== 在这里修改参数 ==========
    RULES_PATH = "domains/good_domain/wall/rules.py"
    MODULE_NAME = "wall"
    CASE_JSON_PATH = "tools/spec_case_checker/cases.json"
    # ====================================

    print(f"🔍 正在加载rules: {RULES_PATH}")
    type_map_data = load_rules(RULES_PATH)
    print(f"✅ 读取type_map: {type_map_data}")

    new_case_templates = generate_cases(type_map_data, MODULE_NAME)
    print("\n==== 待写入的case模板 ====")
    print(json.dumps(new_case_templates, indent=2, ensure_ascii=False))

    added = append_cases(CASE_JSON_PATH, new_case_templates)
    print(f"\n✅ 完成！本次新增 {len(added)} 条case写入 {CASE_JSON_PATH}")
    if len(added) == 0:
        print("ℹ️  所有case已经存在，本次无新增，不会重复写入")
