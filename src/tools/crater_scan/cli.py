import argparse
import csv
import json
from pathlib import Path
from rules import batch_score

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)


def load_candidate_csv(path:Path) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # 全部数值字段转float
            item = {}
            for k,v in r.items():
                try:
                    item[k] = float(v)
                except ValueError:
                    item[k] = v
            rows.append(item)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Crater Scan 陨石坑选址打分工具")
    parser.add_argument("--planet", required=True, choices=["moon","mars"], help="目标天体 moon / mars")
    parser.add_argument("--input", required=True, help="候选坑csv路径，放在data目录")
    parser.add_argument("--out", default="result", help="输出文件名前缀")
    args = parser.parse_args()

    input_path = DATA_DIR / args.input
    candidates = load_candidate_csv(input_path)
    result = batch_score(candidates, args.planet)

    out_json = OUT_DIR / f"{args.out}_{args.planet}.json"
    out_csv = OUT_DIR / f"{args.out}_{args.planet}.csv"
    out_detail_csv = OUT_DIR / f"{args.out}_{args.planet}_detail.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 汇总CSV：仅ID、名称、总分
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["crater_id","name","total_score"])
        for row in result:
            writer.writerow([row["crater_id"], row["name"], row["total_score"]])

    # 明细对比CSV：所有指标横向展开，直接做多坑并排对比
    if len(result) > 0:
        sample_details = result[0]["details"]
        headers = ["crater_id","name","total_score"] + list(sample_details.keys())
        with open(out_detail_csv, "w", encoding="utf-8", newline="") as f:
            detail_writer = csv.writer(f)
            detail_writer.writerow(headers)
            for row in result:
                cols = [row["crater_id"], row["name"], row["total_score"]]
                for k in sample_details.keys():
                    cols.append(row["details"][k]["raw_score"])
                detail_writer.writerow(cols)

    print(f"✅ 批量打分完成，共 {len(result)} 个候选坑")
    print(f"📄 JSON完整明细: {out_json}")
    print(f"📄 汇总CSV: {out_csv}")
    print(f"📄 横向对比明细CSV: {out_detail_csv}")


if __name__ == "__main__":
    main()
