import argparse
from schema import EnvRecord
from storage import add_record, load_records, save_records
from plot import plot_temp_humidity, plot_feel_score
import csv
from pathlib import Path


def cmd_add():
    print("=== 添加环境记录 ===")
    temp = input("温度(℃，回车留空): ")
    humidity = input("湿度(%，回车留空): ")
    co2 = input("CO2(ppm，回车留空): ")
    mold_risk = input("霉菌风险 0~5: ")
    resp_feel = input("呼吸体感 1~5: ")
    sleep_feel = input("睡眠体感 1~5: ")
    notes = input("备注: ")

    def opt_float(v):
        return float(v) if v.strip() else None
    def opt_int(v):
        return int(v) if v.strip() else None

    rec = EnvRecord(
        temp=opt_float(temp),
        humidity=opt_float(humidity),
        co2=opt_int(co2),
        mold_risk=int(mold_risk),
        resp_feel=int(resp_feel),
        sleep_feel=int(sleep_feel),
        notes=notes
    )
    add_record(rec)
    print("✅ 记录保存成功")


def cmd_list():
    records = load_records()
    records.sort(key=lambda x: x.timestamp, reverse=True)
    print(f"\n共 {len(records)} 条记录\n")
    for r in records:
        print(f"[{r.timestamp.isoformat()}] T:{r.temp} H:{r.humidity} CO2:{r.co2} "
              f"mold:{r.mold_risk} resp:{r.resp_feel} sleep:{r.sleep_feel} | {r.notes}")


def cmd_plot():
    records = load_records()
    plot_temp_humidity(records)


def cmd_export():
    records = load_records()
    out_path = Path("env_export.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "temp", "humidity", "co2", "mold_risk", "resp_feel", "sleep_feel", "notes"])
        for r in records:
            w.writerow([r.timestamp.isoformat(), r.temp, r.humidity, r.co2, r.mold_risk, r.resp_feel, r.sleep_feel, r.notes])
    print(f"✅ CSV导出完成：{out_path}")


def main():
    parser = argparse.ArgumentParser(description="EnvLog 人居环境日志工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("add", help="新增一条记录")
    sub.add_parser("list", help="列出全部记录，时间倒序")
    sub.add_parser("plot", help="绘制温湿度折线图")
    sub.add_parser("export", help="导出CSV文件")
    sub.add_parser("plot-feel", help="绘制呼吸、睡眠体感和霉菌风险曲线")

    args = parser.parse_args()
    if args.cmd == "add":
        cmd_add()
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "plot":
        cmd_plot()
    elif args.cmd == "export":
        cmd_export()
    elif args.cmd == "plot-feel":
        records = load_records()
        plot_feel_score(records)



if __name__ == "__main__":
    main()
