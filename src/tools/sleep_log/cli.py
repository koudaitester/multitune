# tools/sleep_log/cli.py
import json
from pathlib import Path
from collections import Counter

JSON_FILE = Path(__file__).parent / "sleep.json"

def load_all_records():
    if not JSON_FILE.exists():
        return []
    with open(JSON_FILE, "r", encoding="utf-8") as fp:
        return json.load(fp)

def save_records(records):
    with open(JSON_FILE, "w", encoding="utf-8") as fp:
        json.dump(records, fp, ensure_ascii=False, indent=2)

def factor_stats(records):
    main_list = []
    secondary_list = []
    perception_list = []
    for r in records:
        main_list.append(r["main_factor"]["name"])
        secondary_list.extend([item["name"] for item in r.get("secondary_factors", [])])
        perception_list.extend([item["name"] for item in r.get("perception_factors", [])])
    return {
        "main": Counter(main_list),
        "secondary": Counter(secondary_list),
        "perception": Counter(perception_list),
    }

def render_markdown(records, stats) -> str:
    lines = ["# Sleep & Body Observation Summary\n"]
    lines.append(f"Total records: {len(records)}\n")
    lines.append("## Factor Statistics\n")
    lines.append("### Main Factors")
    for name, cnt in stats["main"].most_common():
        lines.append(f"- {name}: {cnt}")
    lines.append("\n### Secondary Factors")
    for name, cnt in stats["secondary"].most_common():
        lines.append(f"- {name}: {cnt}")
    lines.append("\n### Perception Factors")
    for name, cnt in stats["perception"].most_common():
        lines.append(f"- {name}: {cnt}")

    lines.append("\n## Record List\n")
    for rec in records:
        lines.append(f"### {rec['record_date']} | {rec['title']}")
        lines.append(f"> Summary: {rec['summary']}\n")
    return "\n".join(lines)


def interactive_add():
    """交互式录入，命令行逐个提问采集观测记录"""
    print("==== 新增人体观测记录 ====")
    rec = {}
    rec["record_date"] = input("记录日期(YYYY-MM-DD): ").strip()
    rec["title"] = input("标题: ").strip()

    print("\n【主因素】")
    main_name = input("主因素名称: ").strip()
    main_mech = input("主因素机理: ").strip()
    rec["main_factor"] = {"name": main_name, "mechanism": main_mech}

    # 次要因素，可多条
    secondary = []
    while True:
        inp = input("\n增加次要因素？y继续 / n跳过: ").strip().lower()
        if inp != "y":
            break
        s_name = input("次要因素名称: ").strip()
        s_mech = input("次要因素机理: ").strip()
        secondary.append({"name": s_name, "mechanism": s_mech})
    rec["secondary_factors"] = secondary

    # 感知因素，可多条
    perception = []
    while True:
        inp = input("\n增加感知因素？y继续 / n跳过: ").strip().lower()
        if inp != "y":
            break
        p_name = input("感知因素名称: ").strip()
        p_mech = input("感知因素机理: ").strip()
        perception.append({"name": p_name, "mechanism": p_mech})
    rec["perception_factors"] = perception

    print("\n【后续观测post_observation，可选】")
    po_time = input("post观测时间(直接回车留空): ").strip()
    po_content = input("post观测内容(直接回车留空): ").strip()
    if po_time and po_content:
        rec["post_observation"] = {"time": po_time, "content": po_content}

    rec["summary"] = input("\n总结summary: ").strip()

    # 写入json并按日期排序
    records = load_all_records()
    records.append(rec)
    records.sort(key=lambda x: x["record_date"])
    save_records(records)
    print("\n✅ 记录已保存到 sleep.json")


def show_report():
    records = load_all_records()
    stats = factor_stats(records)
    md = render_markdown(records, stats)
    print("\n" + md)


def print_help():
    print("""
指令：
  add      交互式新增观测记录
  report   查看汇总统计报表
  help     打印帮助
""")


def run():
    while True:
        cmd = input("\n请输入指令(add/report/help/exit): ").strip().lower()
        if cmd == "add":
            interactive_add()
        elif cmd == "report":
            show_report()
        elif cmd == "help":
            print_help()
        elif cmd == "exit":
            print("退出cli")
            break
        else:
            print("无效指令，输入help查看支持命令")


if __name__ == "__main__":
    run()
