# brain_log 脑力追踪工具
> 配套开发者效能工具，不属于业务domain，无web接口、无模型，纯本地CLI，和add_gut_log平级

## 字段说明（精简版）
- date：日期 YYYY-MM-DD
- block_id：当日任务块编号，01、02...
- category：架构设计 / 写代码 / 调试 / 阅读资料 / 杂事 / 体力工作
- valid_minutes：有效脑力时长（分钟，剔除走神无效时间）
- brain_level：脑力等级1~5
  5：思路连贯，深度推导，几乎不分心
  4：稳定专注，偶尔小停顿
  3：能干活，但容易被打断，深度思考吃力
  2：只能做简单机械操作（复制、改注释）
  1：脑子发沉，很难进入思考
- disturb：干扰因素：无 / 体力疲劳 / 睡眠不足 / 琐事多 / 环境嘈杂

## 使用命令
cd src/tools/brain_log

# 添加一条记录
python brain_log.py add

# 查看汇总
python brain_log.py summary

# 导出csv，可放到表格看趋势
python brain_log.py export

## 规则
1. 单块建议25–60分钟，不一次性录入超长任务块
2. 体力工作单独标记，不计入项目脑力时长，用来观察体力消耗对次日脑力的影响
3. 纯本地存储，不上传，不参与项目接口契约校验
