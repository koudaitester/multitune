"""读取测试用例json"""
import json
from pathlib import Path


def load_cases(case_file_path: str):
    p = Path(case_file_path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    # case结构示例：[{"module":"plant","case_name":"健康植株","expect_type_id":1},...]
    return raw
