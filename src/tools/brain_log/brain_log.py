import json
import argparse
from datetime import date, datetime
from pathlib import Path

# 数据文件路径
DATA_FILE = Path(__file__).parent / "brain_log.json"

# 初始化空文件
def init_file():
    if not DATA_FILE.exists():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_records():
    init_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_records(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def add_record():
    records = load_records()
    today = str(date.today())
    print("=== 新增脑力任务块记录 ===")
    block_id = input("任务块编号：").strip()
    category = input("任务类别[架构设计/写代码/调试/阅读资料/杂事/体力工作]：").strip()
    valid_min = input("有效脑力时长(分钟)：").strip()
    brain_level = input("脑力等级1~5：").strip()
    disturb = input("干扰因素(空=无)：").strip()
    disturb = disturb if disturb else "无"

    new_item = {
        "date": today,
        "block_id": block_id,
        "category": category,
        "valid_minutes": int(valid_min),
        "brain_level": int(brain_level),
        "disturb": disturb
    }
    records.append(new_item)
    save_records(records)
    print("✅ 记录保存成功")

def summary():
    records = load_records()
    if not records:
        print("暂无记录")
        return
    # 简单汇总
    total_min = sum(r["valid_minutes"] for r in records)
    avg_level = round(sum(r["brain_level"] for r in records)/len(records),2)
    print(f"\n==== 全部记录汇总 ====")
    print(f"总有效脑力时长：{total_min} 分钟")
    print(f"平均脑力等级：{avg_level}")
    print(f"记录条数：{len(records)}")

def export_csv():
    records = load_records()
    out_path = Path(__file__).parent / "brain_log_export.csv"
    lines = ["date,block_id,category,valid_minutes,brain_level,disturb"]
    for r in records:
        line = f"{r['date']},{r['block_id']},{r['category']},{r['valid_minutes']},{r['brain_level']},{r['disturb']}"
        lines.append(line)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ CSV已导出到 {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="脑力块追踪工具")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("add", help="新增一条记录")
    sub.add_parser("summary", help="查看汇总统计")
    sub.add_parser("export", help="导出CSV文件")
    args = parser.parse_args()
    if args.cmd == "add":
        add_record()
    elif args.cmd == "summary":
        summary()
    elif args.cmd == "export":
        export_csv()
