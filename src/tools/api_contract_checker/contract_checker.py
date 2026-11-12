"""
极简API契约校验工具
只校验 json.dump / json.load
契约规则：
json.dump(obj, fp, ...) 必须至少2个位置参数：数据对象，文件句柄fp
json.load(fp, ...)     必须至少1个位置参数：文件句柄fp
"""
import ast
from pathlib import Path
from typing import List, Dict


class JsonApiContractChecker(ast.NodeVisitor):
    def __init__(self):
        self.violations: List[Dict] = []

    def visit_Call(self, node: ast.Call):
        # 匹配 json.dump 和 json.load
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "json":
                func_name = node.func.attr
                arg_count = len(node.args)
                line_no = node.lineno

                if func_name == "dump":
                    # 契约：json.dump 需要至少 2个位置参数 obj, fp
                    if arg_count < 2:
                        self.violations.append({
                            "line": line_no,
                            "func": "json.dump",
                            "error": f"契约违规：至少需要2个位置参数，当前传入{arg_count}个",
                            "hint": "json.dump(data, fp, ...)，第二个参数必须是文件对象fp"
                        })
                elif func_name == "load":
                    # 契约：json.load 需要至少1个位置参数 fp
                    if arg_count < 1:
                        self.violations.append({
                            "line": line_no,
                            "func": "json.load",
                            "error": f"契约违规：至少需要1个位置参数，当前传入{arg_count}个",
                            "hint": "json.load(fp)"
                        })
        self.generic_visit(node)


def scan_file(file_path: str):
    p = Path(file_path)
    src = p.read_text(encoding="utf-8")
    tree = ast.parse(src)
    checker = JsonApiContractChecker()
    checker.visit(tree)
    return checker.violations


if __name__ == "__main__":
    # ========== 修改这里，填你要扫描的代码文件 ==========
    target_file = "gen_case_template.py"
    # ===================================================
    print(f"🔍 开始扫描文件: {target_file}")
    issues = scan_file(target_file)
    if not issues:
        print("✅ 未发现json API契约违规")
    else:
        print("❌ 检测到API契约违规：")
        for item in issues:
            print(f"行号{item['line']} | {item['func']} | {item['error']}")
            print(f"    💡提示：{item['hint']}\n")
