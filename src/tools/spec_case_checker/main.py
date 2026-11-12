import sys
from pathlib import Path

# 把src加入python路径，方便import业务代码
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extract_truth import get_all_truth
from case_parser import load_cases
from checker import run_check


def print_report(report):
    print("=" * 50)
    print("          真值-测试用例对齐校验报告")
    print("=" * 50)
    for item in report:
        print(f"\n【模块：{item['module']}】")
        print(f"基准合法type_id: {item['valid_type_ids']}")
        print(f"已覆盖type_id: {item['covered_type_ids']}")
        print(f"❌缺失分支type_id: {item['missing_type_ids']}")
        if item["invalid_cases"]:
            print("❌非法用例：")
            for bad in item["invalid_cases"]:
                print(f"  用例名:{bad['case_name']}, expect_type_id={bad['expect_type_id']}, {bad['error']}")


if __name__ == "__main__":
    case_path = Path(__file__).parent / "cases.json"
    truth_data = get_all_truth()
    case_data = load_cases(str(case_path))
    result = run_check(truth_data, case_data)
    print_report(result)
