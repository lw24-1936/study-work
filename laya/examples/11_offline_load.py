"""11 - 离线/本地加载：把 checkpoint 落到指定目录，之后完全断网也能跑。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com
    /opt/ai-lab/laya/.venv/bin/python 11_offline_load.py

第一次运行把英文 checkpoint 存到 /opt/ai-lab/laya/models/laya-english（0.85 GB）；
脚本末尾会用 HF_HUB_OFFLINE=1 起一个子进程，证明本地加载确实不碰网络。
huggingface_hub 的环境变量是 import 时读取的，所以「断网验证」必须新起进程，
不能在同一个进程里改环境变量。
"""
import os
import subprocess
import sys
import time

LOCAL_DIR = os.environ.get("LAYA_LOCAL_DIR", "/opt/ai-lab/laya/models/laya-english")

# ---------------------------------------------------------------------------
# 子进程模式：模拟一台完全不联网的机器
# huggingface_hub 的 HF_HUB_OFFLINE 在 import 时读取，所以必须新进程 + 提前设置
# ---------------------------------------------------------------------------
if "--offline-child" in sys.argv:
    os.environ["HF_HUB_OFFLINE"] = "1"
    import laya as _laya

    t0 = time.time()
    _agent = _laya.load(LOCAL_DIR, device="cpu")
    _res = _agent.predict(
        {"message": "duplicate charge, please refund"},
        {"intent": {"type": "choice", "instructions": "What does the customer want?",
                    "criteria": {"refund": "money back", "other": "none of the others"}}})
    print("  子进程（HF_HUB_OFFLINE=1，device=cpu）加载 + 推理 %.1f s -> %s"
          % (time.time() - t0, _res["answers"]["intent"]["choice"]))
    raise SystemExit(0)

# ---------------------------------------------------------------------------
# 父进程：下载 / 落盘 / 本地加载
# ---------------------------------------------------------------------------
from huggingface_hub import snapshot_download

# 1) 只下载 root 的这一份 checkpoint（不含 multilingual/、typed-decisions/ 两个子目录）
#    allow_patterns 用 fnmatch 匹配完整路径，"*" 会跨越 "/"，
#    所以这里写精确文件名，而不是 "*.safetensors"——后者会把两个子目录的权重一起拉下来。
PATTERNS = ["model.safetensors", "rl_agent_config.json", "rl_common.py", "rl_agent_api.py",
            "email_utils.py", "tokenizer/*", "encoder/*"]
os.makedirs(os.path.dirname(LOCAL_DIR), exist_ok=True)

t0 = time.time()
cache_path = snapshot_download("convaiinnovations/laya", allow_patterns=PATTERNS)
print("HF 缓存目录：", cache_path)
print("缓存命中/下载耗时：%.1f s" % (time.time() - t0))

# 2) 复制成一份自带目录（离线部署时直接把这个目录拷走即可）
if not os.path.exists(os.path.join(LOCAL_DIR, "model.safetensors")):
    t0 = time.time()
    snapshot_download("convaiinnovations/laya", allow_patterns=PATTERNS, local_dir=LOCAL_DIR)
    print("落到本地目录 %s，耗时 %.1f s" % (LOCAL_DIR, time.time() - t0))
else:
    print("本地目录已存在：", LOCAL_DIR)

print()
print("本地目录里的权重与配置（.cache/ 是下载元数据，可删）：")
total = 0
for root, _dirs, files in os.walk(LOCAL_DIR):
    if ".cache" in root:
        continue
    for f in sorted(files):
        p = os.path.join(root, f)
        size = os.path.getsize(p)
        total += size
        print("  %8.2f MB  %s" % (size / 1e6, os.path.relpath(p, LOCAL_DIR)))
print("  合计 %.2f GB" % (total / 1e9))
print()

# 3) 用本地路径加载：这条路径不经过 huggingface_hub，完全离线
import laya

t0 = time.time()
agent = laya.load(LOCAL_DIR, device=os.environ.get("LAYA_DEVICE") or None)
print("从本地目录加载完成：device=%s，耗时 %.1f s" % (agent.device, time.time() - t0))

res = agent.predict(
    {"message": "The API returns 502 on the export endpoint since yesterday."},
    {"intent": {"type": "choice", "instructions": "What does the customer want?",
                "criteria": {"technical_help": "a bug or outage",
                             "billing_question": "a question about an invoice",
                             "other": "none of the others"}}},
)
print("离线推理结果：", res["answers"]["intent"]["choice"],
      res["answers"]["intent"]["probabilities"])
print()

print("=== 断网验证：新起一个进程，打开 HF_HUB_OFFLINE=1 再加载一次 ===")
subprocess.run([sys.executable, __file__, "--offline-child"], check=True)
