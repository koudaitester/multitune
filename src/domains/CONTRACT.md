# 域契约

一页纸。加服务、改跨域调用之前对着看一眼，别凭印象。

## 1. 域与能力

分域口径：**有生命体 → `tune_domain`，无生命体（含介质与空间环境）→ `good_domain`**。

| 域 | 路由 | 入参字段 | 依赖视觉模型 |
|---|---|---|---|
| plant | `POST /api/v1/tune/plant` | `img_b64` | 是 |
| pet | `POST /api/v1/tune/pet` | `img_b64` | 是 |
| fruit | `POST /api/v1/tune/fruit` | `image_b64` | 是 |
| gut | `POST /api/v1/tune/gut` | `image_b64` | 是 |
| posture | `POST /api/v1/tune/posture` | `image_b64` | **否（关键点几何）** |
| cloth | `POST /api/v1/good/cloth` | `image_b64` | **否（硬编码直通）** |
| wall | `POST /api/v1/good/goodwall` | `image_b64` | **否（硬编码直通）** |
| oldman_space | `POST /api/v1/good/oldman` | `image_b64` | **否（硬编码直通）** |
| env_monitor | `POST /api/v1/good/env` | `image_b64` | 是 |
| mold | `POST /api/v1/good/mold` | `image_b64`（可选 `humidity` / `temperature`） | 是 |
| moon | `POST /api/v1/good/moon` | `image_b64`（可选 `view`: `ground`/`region`） | 是 |

> `moon` 是首个**分数含义随入参变化**的服务，也是唯一允许这种变化的地方：
> `view=ground`（默认）判「可落性」，`view=region` 判「区域候选度」，
> 两套分数、两套等级名、两套 prompt，**不可互相比较**。
> 起因是一次实测：一张平坦坑底的大坑远景照，被近场判分器打了 59 分——因为
> 远景里坑壁必然显眼，近场词表把「远处坑壁」当成「脚下坡面」。
> 尺度由调用方声明，不让模型猜：模型对同一张图问「平不平」答「前景巨石 + 背景山脉」，
> 问「有没有坑」答「中央大坑」——两次描述互相矛盾，说明它在顺着问题生成句子。
> region 模式下**刻意不判坡度与通行**，那些量远景给不出。
>
> **两段式操作口径**（不在代码里硬编码，是使用约定）：
> ① 远景/俯瞰先找候选区（有坑、有大范围平坦面），`region ≥ 70`「值得细看」即可**进入备选**；
> ② 对备选点拍**多方向、多维度的近景照**，逐张跑 `ground`，**全部**达到阈值（≥70「可用」）
>    才可定为候选点位——任何一张不达标就不得进入下一轮；
> ③ 多个候选点位横向对比后择优，而不是单点直接定案。
> 这条链的每一环都是「上一环只能缩小范围、不能给结论」，所以近景分数永远不能从远景推导。

> `mold` 是首个带**可选数值入参**的服务：`humidity` 与 `temperature` 不传就完全不加权、不猜默认值。
> 规则表（特征权重 81/41/21 分级、湿度 30/20/10、温度 5、无病灶时诱因封顶 20）来自
> `human_env_api/knowledge/mold_risk_calc.md`，是那个项目里唯一值得搬的知识；原实现的
> 贝叶斯网络与正则软规则属于研究阶段实验，未移植。

> 入参字段不一致（`img_b64` / `image_b64`）是历史遗留，**新服务一律用 `image_b64`**，老的不动。

> 「硬编码直通」= `api.py` 里直接把 `raw_text` 写死成一句描述，不真调模型。改这三个域时别以为模型没返回。

> `posture` 是唯一不调视觉模型的服务：轻量 VL 给不出几何量（实测同一张侧面照
> 会同时说 "side profile position" 和 "photo is taken from the front"，二选一提问
> 还输出 "no head"），所以改用 mediapipe 关键点算**图像平面内的角度**。
> 三条硬约束——**正侧位、单人、全身入镜**——任一不满足就判 `invalid` 且不给角度，
> 这是刻意设计：宁可判无效，也不给错数。全身没拍全时退化为 `reliability=upper_only`，
> 只算上半身。阈值全部实测校准（头前倾 15° / 肩 8° / 骨盆 12° / 膝 8°），
> 改阈值必须用真实照片重新校准，别凭感觉调。

## 2. 域间调用规则

**默认直接 `import service`**，这是最快的路。

只有下面三条**任一满足**才加 `doorway.py` 门面：

1. 入参形态要转换（对方手里是图，service 要的是一段文本，等等）
2. 需要跨域专用参数（如 `write_log=False`，只对调用方有意义）
3. 内部实现预计会重构，需要一个稳定签名挡在前面

**判定门面是否该存在**：如果 doorway 的函数签名和 service 一模一样、参数一一对应，函数体只有一句 `return _service.xxx(...)`，它就是别名，删掉，直接 import service。

## 3. 依赖方向

- `good_domain → tune_domain` 允许
- `tune_domain → good_domain` **禁止**
- 同域内互相调用自由
- `common/` 无业务语义，谁都能用

反向依赖一旦出现就是设计错误，不要用门面去绕，去改编排位置。

## 4. 统一约定

- 所有响应继承 `common/schema_meta.py::EvalMeta`，带 `status`（`ok` / `invalid`）和 `reason`（中文原因）
- 无目标统一 `type_id = 99`，同时 `status = "invalid"`
- 模型调用失败走 **HTTP 500**，不占用 `status`（失败和「没有目标」是两件事）
- 图片入参是裸 base64，不带 `data:image` 前缀

## 5. 边界检查（当前无自动检查）

`domains/` 目前只是目录，没有规则阻止互相穿透。要做的话：脚本扫 `domains/*/` 下的 `import`，出现「跨域 + 非 doorway + 非 schema」就报错。参照 Spring Modulith 的 `verify()`。

## 6. 已知遗留

- `README.md` 严重滞后（只写 plant/pet，路径还是 `/Users/mac/code/PlantTune`）
- `good_domain/api.py` 的 `tags` 仍叫「介质品质域」
- `oldman_space/service.py::validate_entities()` 是空壳，返回值被丢弃
- `gut` 的 `analyze_gut` 内部无条件写 `gut_tune_log.json`，跨域调用前需补 `write_log` 开关
- `moon/region` 对「模型描述本身是错的」没有防御：一张满屏坑群的轨道照被描述成
  "flat and smooth, no visible hills"，于是拿到 70 分「值得细看」。可接受的下限是
  不给「优选候选」，但没有机制识别这种冲突，只能靠人工复核
- `moon/` 里用户原有草稿 `schema.py` / `validator.py` / `service.py` 未接入路由：
  `validator.py` 与 `schema.py` 定义重复且冲突（`MissionProfile` 只允许 mobile_trailer_depot、
  `feature_groups` 为 dict、`result` 必填），`service.py::run_vlm_on_image` 仍是
  `NotImplementedError` 占位。要接「完整结构化评估」那条路（需 DEM / 日照 / 通信数据）再动
