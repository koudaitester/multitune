def run_check(truth_list, cases):
    report = []
    for truth in truth_list:
        mod_name = truth["module"]
        valid_ids = set(truth["valid_type_ids"])
        case_ids = []
        bad_cases = []

        for case in cases:
            if case.get("module") != mod_name:
                continue
            tid = case["expect_type_id"]
            case_ids.append(tid)
            if tid not in valid_ids:
                bad_cases.append({
                    "case_name": case["case_name"],
                    "expect_type_id": tid,
                    "error": "type_id不在基准枚举内"
                })
        covered = set(case_ids) & valid_ids
        missing = valid_ids - covered
        report.append({
            "module": mod_name,
            "valid_type_ids": sorted(valid_ids),
            "covered_type_ids": sorted(covered),
            "missing_type_ids": sorted(missing),
            "invalid_cases": bad_cases
        })
    return report
