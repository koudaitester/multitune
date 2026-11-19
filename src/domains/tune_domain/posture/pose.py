# src/domains/tune_domain/posture/pose.py
"""几何判定层：mediapipe 关键点 → 体态角度。

为什么不用视觉模型：
Moondream 这类轻量 VL 只能描述语义，给不出几何量。实测同一张侧面照它会说
"side profile position" 又说 "photo is taken from the front"，二选一提问还输出
"no head" 这种幻觉。体态角度必须从坐标算，才可复现、可追溯。

注意：这里算的是**图像平面内的角度**。只有正侧位（身体完全侧对镜头）、全身入镜、
镜头水平时，才近似真实矢状面角度；否则宁可判无效，也不给错误数值。
"""
import base64
import math
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = Path(__file__).parent / "models" / "pose_landmarker_lite.task"

# MediaPipe Pose 33 点定义中本服务用到的部分
EAR = (7, 8)
SHOULDER = (11, 12)
HIP = (23, 24)
KNEE = (25, 26)
ANKLE = (27, 28)

_landmarker = None
_init_lock = threading.Lock()
_detect_lock = threading.Lock()


class PoseError(Exception):
    """图片解码失败等无法继续的情况"""


def _get_landmarker():
    """懒加载。PoseLandmarker 不是线程安全的，创建与推理都需加锁。"""
    global _landmarker
    if _landmarker is None:
        with _init_lock:
            if _landmarker is None:
                if not MODEL_PATH.exists():
                    raise PoseError(f"姿态模型缺失: {MODEL_PATH}")
                base = python.BaseOptions(model_asset_path=str(MODEL_PATH))
                opts = vision.PoseLandmarkerOptions(
                    base_options=base,
                    num_poses=2,  # 用 2 来识别「画面里有几个人」
                    running_mode=vision.RunningMode.IMAGE,
                    min_pose_detection_confidence=0.4,
                )
                _landmarker = vision.PoseLandmarker.create_from_options(opts)
    return _landmarker


def decode_image(image_b64: str) -> np.ndarray:
    """base64 → RGB ndarray"""
    try:
        raw = base64.b64decode(image_b64)
    except Exception as e:
        raise PoseError(f"base64 解码失败: {e}") from e
    arr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if arr is None:
        raise PoseError("图片解码失败，请确认是 jpg / png")
    return cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)


def detect(image_b64: str) -> Tuple[int, int, List]:
    """返回 (宽, 高, 检测到的人体列表)"""
    rgb = decode_image(image_b64)
    h, w = rgb.shape[:2]
    lm = _get_landmarker()
    with _detect_lock:
        res = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    return w, h, (res.pose_landmarks or [])


def _pick(pts, pair: Tuple[int, int]):
    """左右成对的点，取置信度更高的那侧（侧位照里靠近镜头的一侧）"""
    a, b = pair
    return pts[a] if pts[a].visibility >= pts[b].visibility else pts[b]


def is_side_view(pts, w: int) -> bool:
    """双肩在水平方向的间距占画面宽度的比例：侧面时两肩几乎重叠"""
    dx = abs(pts[SHOULDER[0]].x - pts[SHOULDER[1]].x) * w
    return dx < 0.06 * w


def is_full_body(pts) -> bool:
    """膝、踝是否都在画面内且可信。

    注意：侧位照里远离镜头的那条腿常被遮挡、置信度很低，
    所以取「置信度更高的那一侧」来判断，不能要求左右两侧都可见。
    """
    knee = _pick(pts, KNEE)
    ankle = _pick(pts, ANKLE)
    return all(0.0 <= p.y <= 1.0 and p.visibility > 0.5 for p in (knee, ankle))


def _angle_from_vertical(dx: float, dy: float) -> float:
    """两点连线与竖直方向的夹角（度）"""
    if abs(dy) < 1e-6:
        return 90.0
    return math.degrees(math.atan2(abs(dx), abs(dy)))


def compute_metrics(pts, w: int, h: int, full_body: bool) -> Dict[str, Optional[float]]:
    """从关键点算体态角度。侧位照里图像的 x 方向 = 身体前后方向。"""
    ear = _pick(pts, EAR)
    sh = _pick(pts, SHOULDER)
    hip = _pick(pts, HIP)

    metrics: Dict[str, Optional[float]] = {
        # 耳相对肩线前移的程度 —— 头前倾
        "head_forward_deg": round(_angle_from_vertical((sh.x - ear.x) * w, (sh.y - ear.y) * h), 1),
        # 肩相对髋线前移的程度 —— 圆肩 / 含胸
        "shoulder_offset_deg": round(_angle_from_vertical((hip.x - sh.x) * w, (hip.y - sh.y) * h), 1),
        # 髋-膝连线与竖直的夹角 —— 骨盆前倾的粗略代理
        "pelvic_tilt_deg": None,
        # 髋-膝-踝是否共线，偏离即膝超伸
        "knee_deg": None,
    }

    if full_body:
        knee = _pick(pts, KNEE)
        ankle = _pick(pts, ANKLE)
        metrics["pelvic_tilt_deg"] = round(
            _angle_from_vertical((knee.x - hip.x) * w, (knee.y - hip.y) * h), 1
        )
        metrics["knee_deg"] = round(
            _angle_from_vertical((ankle.x - knee.x) * w, (ankle.y - knee.y) * h), 1
        )

    return metrics
