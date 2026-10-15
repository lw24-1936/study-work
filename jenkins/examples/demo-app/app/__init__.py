"""演示用的最小业务代码：Jenkins 流水线会构建、测试、打包它。"""


def add(a, b):
    return a + b


def divide(a, b):
    if b == 0:
        raise ValueError("divisor must not be zero")
    return a / b


def normalize_scores(values):
    """把分数归一化到 0-1；空列表返回空列表，全等值返回全 0.5。"""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if lo == hi:
        return [0.5 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]
