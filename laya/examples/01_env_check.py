"""01 - 安装自检：版本、依赖、设备、环境变量、三种原语的内部表示。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com      # 国内镜像，第一次下载模型时会用到
    /opt/ai-lab/laya/.venv/bin/python 01_env_check.py
本脚本不加载模型，不联网，只看装完之后环境是什么样。
"""
import json
import os
import platform
import sys

import torch
import transformers

import laya
from laya import DEFAULT_MODELS, QTYPE_NAMES, QTYPES, Agent
from laya.common import render_options

print("laya 版本        :", laya.__version__)
print("torch 版本       :", torch.__version__)
print("transformers     :", transformers.__version__)
print("Python           :", sys.version.split()[0], "(" + platform.platform() + ")")
print("torch 编译的架构 :", torch.cuda.get_arch_list())
print("CUDA 是否可用    :", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU              :", torch.cuda.get_device_name(0),
          "compute capability", torch.cuda.get_device_capability(0))
print("当前进程会自动用 :", "cuda" if torch.cuda.is_available() else "cpu",
      "（laya 在没有显式传 device 时按 torch.cuda.is_available() 判断）")

print()
print("离线/镜像相关的环境变量：")
for name in ("HF_ENDPOINT", "HF_HOME", "HF_HUB_CACHE", "HF_HUB_OFFLINE", "HF_TOKEN"):
    value = os.environ.get(name)
    if name == "HF_TOKEN" and value:
        value = "<已设置，长度 %d 的字符串>" % len(value)
    print("  %-16s -> %s" % (name, value if value is not None else "(未设置)"))

print()
print("Router 内置的三个 checkpoint（DEFAULT_MODELS）：")
for key, spec in DEFAULT_MODELS.items():
    print("  %-16s -> %s" % (key, spec))

print()
print("三种原语到内部整型编码的映射（QTYPES，写进模型输入的是 0/1/2）：")
print(" ", QTYPES, " 反向:", QTYPE_NAMES)

print()
print("三种问题定义与它们实际渲染出的选项文本（render_options）：")
question_shapes = {
    "choice": {"type": "choice", "instructions": "Which team should handle this?",
               "criteria": {"billing": "invoices, payments, refunds",
                            "technical": "bugs, outages",
                            "other": "none of the above"}},
    "score": {"type": "score", "instructions": "How urgent is this?",
              "criteria": ["no time pressure", "needs attention soon", "blocking issue"]},
    "noul": {"type": "noul", "instructions": "Does the user ask for a refund?"},
}
for name, qdef in question_shapes.items():
    # Agent._to_internal 是实例方法但不依赖实例状态，这里直接借它看内部结构
    internal = Agent._to_internal(qdef)
    print("  [%s]" % name)
    print("    原始定义   :", json.dumps(qdef, ensure_ascii=False))
    print("    内部 t/ins :", internal["t"], "|", internal["ins"])
    print("    渲染出的选项：")
    for i, text in enumerate(render_options(internal)):
        print("      %d: %s" % (i, text))
