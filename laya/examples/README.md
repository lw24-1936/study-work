# Laya 示例工程

配套文档：`/opt/study-work/laya/Laya完整教程.md`。这里每个文件都是能直接跑的，输出都贴回了文档里。

## 环境

```bash
# 解释器（独立 venv，已装 laya + torch）
/opt/ai-lab/laya/.venv/bin/python

# 国内下载模型走镜像（第一次运行必须设，之后走本地缓存）
export HF_ENDPOINT=https://hf-mirror.com

# 指定设备（不设则自动：有可用的 CUDA 就用 CUDA，否则 CPU）
export LAYA_DEVICE=cpu      # 或 cuda
```

## 文件清单

| 文件 | 主题 | 是否需要模型 |
|---|---|---|
| `01_env_check.py` | 版本、设备、环境变量、三种原语的内部表示 | 不需要 |
| `02_primitives.py` | choice/score/noul 一次 forward 全解决 | 英文 checkpoint |
| `03_router.py` | 语言检测 + Router 路由决策 + 多语言推理 | 英文 + 多语言 |
| `04_presets_triage.py` | `triage_questions()` 客服工单分诊 + 置信度门控 | 英文 |
| `05_email_triage.py` | `clean_email_body`/`email_state` + 邮件分类 + 钓鱼判定 | 英文 |
| `06_guardrail.py` | `guard_questions()`/`moderation_questions()` 守门与内容安全 | 英文 |
| `07_timing.py` | 延迟与吞吐实测（1/5/10/50/100 个问题，CPU vs GPU） | 英文（或加 `LAYA_SUBFOLDER=multilingual`） |
| `08_token_budget.py` | `head_max_len`/`max_len` 的 token 预算与两种修法 | 英文 |
| `09_pitfall_torch_cu130.py` | GTX 1050 上 cu130 无内核的复现与修复指引 | 不需要 |
| `10_calibration.py` | confidence 的含义、ECE、温度缩放（手写 48 条样本） | 英文 |
| `11_offline_load.py` | 落到本地目录 + `HF_HUB_OFFLINE=1` 断网加载 | 英文 |
| `12_service.py` | FastAPI 服务：启动 preload，`/health` + `/decide` | 英文 + 多语言 |
| `13_batch_labeling.py` | 批量打标：JSONL 输入、断点续跑、吞吐统计 | 英文 |

## 运行顺序建议

先跑 `01` 和 `09`（不联网、秒级），确认环境和设备没问题；再跑 `02`，第一次会把 843 MB 的英文
checkpoint 拉到 `~/.cache/huggingface`；之后按编号顺序跑即可。

`12_service.py` 要另外开终端用 `curl` 验证：

```bash
curl -s localhost:8077/health
curl -s -X POST localhost:8077/decide -H 'Content-Type: application/json' \
  -d '{"state":{"message":"We were charged twice, please refund."}}'
```
