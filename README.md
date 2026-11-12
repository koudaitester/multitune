# PlantTune

> 基于「业务域 + 域内分层」架构的视觉评估脚手架（v0.5 演进版）
> 当前已落地：**tune_domain（活体调校域）** → PlantTune 盆栽 / PetTune 宠物

---

## 一、架构设计

核心一句话：**VL 只做客观描述，业务层做规则判定，Router 只负责编排。**

```
图片 → vision_client(moondream) → 英文客观描述 → 关键词/规则匹配 → 结构化结论
```

- 视觉模型**只输出事实**，禁止诊断、结论、建议（prompt 里硬约束）
- 类型判定（type_id）、文案（desc/advice）全部在 service 层做，无模型幻觉风险
- tag 作为用户补充上下文，只记录、不参与判定
- 新增一个业务 = 复制一套 `rules / schema / service`，不改老代码

### 目录结构

```
PlantTune/
├── main.py                     # 旧版脚手架入口（暂未启用，已废弃）
├── requirements.txt
└── src/
    ├── main.py                 # 【当前入口】挂载 tune_domain
    ├── core/                   # 全局底座，所有域共用
    │   ├── config.py           # pydantic-settings 配置
    │   └── logger.py
    ├── common/                 # 通用能力
    │   └── vision_client.py    # ollama 视觉模型调用
    └── domains/
        └── tune_domain/        # 业务域：活体调校域
            ├── api.py          # 本域统一路由入口（/tune）
            ├── plant/          # 子业务：PlantTune
            │   ├── rules.py    # prompt + type_map + 关键词 + warning
            │   ├── schema.py   # Pydantic 入参/出参
            │   └── service.py  # 判定逻辑
            └── pet/            # 子业务：PetTune
                ├── rules.py
                ├── schema.py
                └── service.py
```

### 分层约定

| 层级 | 职责 | 禁止 |
|---|---|---|
| `core/` | 配置、日志、异常等全局底座 | 不写任何业务逻辑 |
| `common/` | 跨域通用能力（模型调用、图片工具） | 不 import 任何 domain |
| `domains/<域>/api.py` | 路由编排、参数校验、调 service | 不写判定逻辑 |
| `domains/<域>/<业务>/rules.py` | 该业务的全部业务知识（prompt/映射/关键词） | 不放代码逻辑 |
| `domains/<域>/<业务>/service.py` | 纯逻辑判定，输入 raw_text 输出 dict | 不发起网络请求 |
| `domains/<域>/<业务>/schema.py` | Pydantic 模型 | 不堆全局 schema |

> 域与域之间不做 service 互调。真要跨域，通过 common 或再抽一个 domain。

---

## 二、运行

### 环境

```bash
cd /Users/mac/code/PlantTune
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

依赖：`fastapi` / `uvicorn` / `pydantic>=2.0` / `pydantic-settings` / `requests` / `Pillow`

前置：本地 ollama 已启动，并已 pull 视觉模型

```bash
ollama serve
ollama pull moondream
```

### 启动

```bash
cd src
uvicorn main:app --reload
```

- 服务地址：<http://127.0.0.1:8000>
- 接口文档：<http://127.0.0.1:8000/docs>

### 配置（.env）

放在 `src/` 下，不填则使用默认值：

```ini
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_VISION_MODEL=moondream
VISION_TIMEOUT=60
```

---

## 三、接口

### 统一出参结构

```json
{
  "type_id": 1,
  "desc": "现象描述",
  "advice": "处理建议",
  "warning": "安全提示"
}
```

`type_id = 99` 表示「非目标图片」，`null` 表示未命中任何规则。

### 1. PlantTune — `POST /api/v1/tune/plant`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tune/plant \
  -H "Content-Type: application/json" \
  -d '{"img_b64":"<裸base64>","tag":"北阳台，5天未浇水"}'
```

| type_id | 含义 |
|---|---|
| 1 | 状态良好，叶片翠绿 |
| 2 | 萎蔫下垂，疑似缺水 |
| 3 | 晒斑、叶尖焦枯，光照过强 |
| 4 | 盆土潮湿，疑似积水过涝 |
| 5 | 斑点/孔洞，疑似虫害或叶部病害 |
| 99 | 非盆栽图片 |

### 2. PetTune — `POST /api/v1/tune/pet`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tune/pet \
  -H "Content-Type: application/json" \
  -d '{"img_b64":"<裸base64>","tag":"金毛，室内饲养"}'
```

| type_id | 含义 |
|---|---|
| 1 | 皮毛良好，毛发顺滑 |
| 2 | 局部掉毛、毛发稀疏 |
| 3 | 皮肤红斑/斑点 |
| 4 | 体表伤口、破皮 |
| 99 | 非猫狗图片 |

> 入参 `img_b64` 必须是**裸 base64**，不带 `data:image/jpeg;base64,` 前缀。

---

## 四、调试方式

### 插桩测试（推荐，秒级验证规则）

不启 ollama、不传图片，直接喂 raw_text 测 service：

```python
import asyncio
from domains.tune_domain.plant.service import plant_tune_service

async def main():
    cases = [
        "green leaves, lush, healthy",      # → 1
        "wilting, drooping leaves",         # → 2
        "brown tips, burnt, scorch",        # → 3
        "wet soil, soggy soil",             # → 4
        "black spots, webbing",             # → 5
        "wall, table, food",                # → 99
    ]
    for c in cases:
        r = await plant_tune_service(c, tag="test")
        print(r["type_id"], c)

asyncio.run(main())
```

> 调关键词、调文案时只用插桩，不要反复打模型，省时间也省算力。

### api.py 里的插桩开关

`api.py` 当前保留了两行硬编码 raw_text（用于跳过模型直测接口）：

```python
raw_text = await vision_predict(req.img_b64, PLANT_PROMPT)
raw_text = "brown tips"        # ← 插桩行，联调完删掉
```

上线前必须删除这两行，否则接口永远返回固定结果。

### 端到端测试

图片转裸 base64 后填进 curl 的 `img_b64` 字段。

macOS 转换：

```bash
base64 -i photo.jpg | tr -d '\n' > b64.txt
```

---

## 五、新增业务的步骤

以在 `tune_domain` 下新增 `xxx` 为例（4 步，不动任何老代码）：

1. **建目录**：`src/domains/tune_domain/xxx/`
2. **复制三件套**：从 `plant/` 拷 `rules.py`、`schema.py`、`service.py`
3. **改业务知识**：`rules.py` 里重写 `PROMPT`、`TYPE_MAP`、`ADVICE_MAP`、`SCALE_KEYWORDS`、`WARNING`
4. **挂路由**：`tune_domain/api.py` 里加一个 `@router.post("/xxx")`

新增一个**全新业务域**（比如 GoodWater 介质品质域）：

1. `src/domains/good_domain/` 下按同样结构建域
2. `good_domain/api.py` 定义自己的 `APIRouter(prefix="/good")`
3. `src/main.py` 加一行 `app.include_router(good_router, prefix="/api/v1")`

---

## 六、演进路线

| 阶段 | 形态 | 触发条件 |
|---|---|---|
| 当前 | 域共用 `api.py` | 每域接口 ≤ 5 个 |
| 下潜 | 每个子业务自带 `api.py`，域级 `api.py` 只做 router 聚合 | 单个子业务接口变多 |
| 拆分 | 每个 domain 独立抽成服务，`core/common` 做成共享包 | 需要独立部署/扩容 |
