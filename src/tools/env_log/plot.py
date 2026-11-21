import matplotlib.pyplot as plt
from typing import List
from schema import EnvRecord


def plot_temp_humidity(records: List[EnvRecord], save_path="env_plot.png"):
    recs = sorted(records, key=lambda x: x.timestamp)
    temps = [r.temp for r in recs if r.temp is not None]
    hums = [r.humidity for r in recs if r.humidity is not None]
    t_times = [r.timestamp for r in recs if r.temp is not None]
    h_times = [r.timestamp for r in recs if r.humidity is not None]

    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.set_xlabel("time")
    ax1.set_ylabel("Temperature ℃", color="#d62728")
    line1 = ax1.plot(t_times, temps, color="#d62728", marker="o", label="Temperature")
    ax1.tick_params(axis='y', labelcolor="#d62728")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Humidity %", color="#1f77b4")
    line2 = ax2.plot(h_times, hums, color="#1f77b4", marker="s", label="Humidity")
    ax2.tick_params(axis='y', labelcolor="#1f77b4")

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left")

    fig.autofmt_xdate()
    fig.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"温湿度图已保存到 {save_path}")


def plot_feel_score(records: List[EnvRecord], save_path="feel_plot.png"):
    recs = sorted(records, key=lambda x: x.timestamp)
    times = [r.timestamp for r in recs]
    resp = [r.resp_feel for r in recs]
    sleep = [r.sleep_feel for r in recs]
    mold = [r.mold_risk for r in recs]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times, resp, color="#2ca02c", marker="o", label="Breath")
    ax.plot(times, sleep, color="#9467bd", marker="s", label="Sleep")
    ax.plot(times, mold, color="#ff7f0e", marker="^", label="Mold_Risk")
    ax.set_xlabel("time")
    ax.set_ylabel("Score 0~5")
    ax.set_ylim(0, 5.2)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"体感分数图已保存到 {save_path}")
