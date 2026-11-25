from typing import List
from .schema import ExoplanetSiteAssessment, RiskItem, AssessmentResult


def evaluate_by_rules(site: ExoplanetSiteAssessment) -> AssessmentResult:
    risks: List[RiskItem] = []
    veto_triggered = False

    # 加权分数累加
    score_sum = 0.0
    weight_total = 0.0

    feature_list = [
        ("terrain", site.feature_groups.terrain.p_likelihood),
        ("illumination", site.feature_groups.illumination.p_likelihood),
        ("comms_los", site.feature_groups.comms_los.p_likelihood),
        ("radiation_shield", site.feature_groups.radiation_shield.p_likelihood),
        ("geology_science", site.feature_groups.geology_science.p_likelihood),
        # 新增：坑天然出口通行能力
        ("crater_exit", site.feature_groups.crater_exit.p_likelihood),
    ]

    # 开启共存评估才加入
    if site.bayes_config.enable_coexistence_check and site.feature_groups.coexistence_assessment:
        feature_list.append(("coexistence", site.feature_groups.coexistence_assessment.p_likelihood))

    # 空间环境模块不为空就纳入打分
    if site.feature_groups.space_environment:
        feature_list.append(("space_env", site.feature_groups.space_environment.p_likelihood))

    # 基础加权
    for name, plh in feature_list:
        score_sum += plh
        weight_total += 1

    raw_p = score_sum / weight_total if weight_total > 0 else 0.0

    # 不确定性惩罚
    p_site_qualified = raw_p * (1 - site.bayes_config.uncertainty_weight * 0.3)
    p_site_qualified = max(0.0, min(1.0, p_site_qualified))

    # 一票否决判定
    if p_site_qualified < site.bayes_config.veto_threshold:
        veto_triggered = True
        risks.append(RiskItem(
            feature_name="global_score",
            risk_level="critical",
            description=f"综合评分低于否决阈值 {site.bayes_config.veto_threshold}"
        ))

    # 地形风险
    terr = site.feature_groups.terrain
    if terr.slope_max_deg > 12:
        risks.append(RiskItem(feature_name="terrain", risk_level="high", description="最大坡度超过12°，月面车通行困难"))
    if terr.boulder_density_over_30cm > 5:
        risks.append(RiskItem(feature_name="terrain", risk_level="medium", description="大于30cm巨石密度偏高"))

    # ========== 新增坑出口风险判断 ==========
    crater_exit = site.feature_groups.crater_exit
    # p_likelihood越低，出口条件越差
    if crater_exit.p_likelihood < 0.2:
        risks.append(RiskItem(
            feature_name="crater_exit",
            risk_level="high",
            description="环形坑闭合无天然地面出口，撤离离开坑底仅可依靠上升器起飞"
        ))
    elif 0.2 <= crater_exit.p_likelihood < 0.6:
        risks.append(RiskItem(
            feature_name="crater_exit",
            risk_level="medium",
            description="坑壁通道断续，需要工程修整，地面通行成本较高"
        ))
    # >=0.6：天然缓坡缺口，无风险，不追加risk

    # 光照风险
    illum = site.feature_groups.illumination
    if illum.continuous_sun_hours < 120:
        risks.append(RiskItem(feature_name="illumination", risk_level="medium", description="连续日照时长不足，太阳能供电压力大"))

    # 通信
    comm = site.feature_groups.comms_los
    if not comm.has_line_of_sight:
        risks.append(RiskItem(feature_name="comms_los", risk_level="medium", description="缺少对地直接视距通信，需要中继"))

    # 共存评估风险
    coex = site.feature_groups.coexistence_assessment
    if coex and site.bayes_config.enable_coexistence_check:
        if not coex.inter_site_line_of_sight:
            risks.append(RiskItem(feature_name="coexistence_assessment", risk_level="medium", description="站点之间无直接无线电视距"))
        if coex.shared_ejecta_risk > 0.6:
            risks.append(RiskItem(feature_name="coexistence_assessment", risk_level="high", description="同坑撞击溅射碎石风险偏高"))

    # 空间环境风险
    space_env = site.feature_groups.space_environment
    if space_env:
        if space_env.spe_event_prob > 0.6:
            risks.append(RiskItem(feature_name="space_environment", risk_level="high", description="太阳高能粒子事件概率较高"))
        if space_env.ejecta_flux_local > 0.6:
            risks.append(RiskItem(feature_name="space_environment", risk_level="medium", description="本地溅射漂浮物通量偏高"))

    # 简单不确定性标准差估算
    uncertainty_std = site.bayes_config.uncertainty_weight * 0.25

    return AssessmentResult(
        p_site_qualified=round(p_site_qualified, 4),
        uncertainty_std=round(uncertainty_std,4),
        veto_triggered=veto_triggered,
        risk_items=risks
    )
