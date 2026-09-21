"""09 - 踩坑复现：GTX 1050 上 torch 装成 cu130 时，模型跑不动。

症状：torch.cuda.is_available() 是 True，但一执行矩阵运算就抛
      AcceleratorError: CUDA error: no kernel image is available for execution on the device。
原因：PyPI 上的 torch 默认是 CUDA 13 构建（sm_75 起步），Pascal 架构的 GTX 1050 是 sm_61，
      没有对应内核。
跑法：/opt/ai-lab/laya/.venv/bin/python 09_pitfall_torch_cu130.py
"""
import torch

print("torch 版本        :", torch.__version__)
print("这版 torch 的架构 :", torch.cuda.get_arch_list())
print("CUDA 是否可用     :", torch.cuda.is_available())
print("显卡              :", torch.cuda.get_device_name(0))
cap = torch.cuda.get_device_capability(0)
print("compute capability: sm_%d%d" % cap)
print()

if not torch.cuda.is_available():
    print("这台机器没有可用的 CUDA 设备，本示例结束。")
    raise SystemExit(0)

print("尝试在 GPU 上跑一个 512x512 矩阵乘法：")
try:
    a = torch.randn(512, 512, device="cuda")
    b = a @ a
    torch.cuda.synchronize()
    print("  成功，结果求和 =", float(b.sum()))
    print("  => 这版 torch 有 sm_%d%d 的内核，可以放心把 device 设成 cuda。" % cap)
except Exception as exc:
    print("  失败：%s: %s" % (type(exc).__name__, str(exc).splitlines()[0]))
    print()
    print("修复方式（按显卡架构选一条）：")
    print("  Pascal/Volta/Turing 老卡（sm_50 ~ sm_75）：")
    print("    uv pip install --python /opt/ai-lab/laya/.venv/bin/python \\")
    print("      --index https://download.pytorch.org/whl/cu126 'torch==2.14.0+cu126'")
    print("  只想要 CPU：")
    print("    uv pip install --python /opt/ai-lab/laya/.venv/bin/python \\")
    print("      --index https://download.pytorch.org/whl/cpu 'torch==2.14.0+cpu'")
    print("  装完用同一个脚本复验，直到出现「成功」。")
