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
| cloth | `POST /api/v1/good/cloth` | `image_b64` | **否（硬编码直通）** |
| wall | `POST /api/v1/good/goodwall` | `image_b64` | **否（硬编码直通）** |
| oldman_space | `POST /api/v1/good/oldman` | `image_b64` | **否（硬编码直通）** |
| env_monitor | `POST /api/v1/good/env` | `image_b64` | 是 |

> 入参字段不一致（`img_b64` / `image_b64`）是历史遗留，**新服务一律用 `image_b64`**，老的不动。

> 「硬编码直通」= `api.py` 里直接把 `raw_text` 写死成一句描述，不真调模型。改这三个域时别以为模型没返回。

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
