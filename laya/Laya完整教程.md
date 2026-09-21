---
title: Laya 完整教程：非自回归决策模型的安装、路由、校准与生产使用
created: 2026-09-21
updated: 2026-09-21
type: concept
tags: [laya, system-one, decision-model, non-autoregressive, llm, huggingface, torch, python, router, calibration, self-hosted]
---

# Laya 完整教程：非自回归决策模型的安装、路由、校准与生产使用

整理日期：2026-09-21

> 状态：已完成

Laya 是 Convai Innovations 开源的 System 1 决策模型：它不生成文本，只回答你事先定义好的「带类型的选择题」。你给它一段 state（文本 / JSON / 对话轮次），再给它一组 questions（是/否、单选、打分），它在**一次前向**里返回每个问题的答案与概率分布，代码直接分支。权重是 Apache 2.0 开源的，可以完全自托管——没有 API Key、没有按 token 计费、没有出网请求。

本文按「概念 → 安装 → 原语 → 路由 → 校准 → token 预算 → 预设 → 性能 → 服务化 → 批量 → 微调 → 对比」的顺序组织，14 个示例全部在本机真实执行过，输出逐处回填。

实测环境（所有命令与输出都出自这台机器）：

```text
系统：Ubuntu 24.04（内核 7.0.0-28-generic）
CPU：8 核            内存：19 GB
GPU：NVIDIA GeForce GTX 1050（4 GB 显存，compute capability 6.1，驱动 580.173.02）
Python：3.12.3       uv：0.12.5
laya：0.3.4          torch：2.14.0+cu126     transformers：5.17.0
fastapi：0.141.1     uvicorn：0.53.0
venv：/opt/ai-lab/laya/.venv
模型缓存：/root/.cache/huggingface/hub/models--convaiinnovations--laya（2.37 GB，三个 checkpoint）
示例代码：/opt/study-work/laya/examples/（14 个可运行文件）
网络：pypi 走清华镜像；模型走 https://hf-mirror.com（huggingface.co 直连超时）
```

关于本文的输出标注：

```text
本文的 Laya 全部是本地权重，所有「答案、概率、路由原因、显存、延迟」都是本机真实的
模型输出与真实测量值，没有 stub、没有编造。凡引用官方 README / BENCHMARKS.md 的数字，
都会显式写明「官方数据」，与本机实测分开。
```

## 目录

- [1. Laya 是什么](#1-laya-是什么)
- [2. 安装](#2-安装)
- [3. 快速上手](#3-快速上手)
- [4. 三种决策原语](#4-三种决策原语)
- [5. Router：三个 checkpoint 的路由](#5-router三个-checkpoint-的路由)
- [6. 置信度与校准](#6-置信度与校准)
- [7. token 预算与高基数选项](#7-token-预算与高基数选项)
- [8. 内置工作流预设](#8-内置工作流预设)
- [9. 性能、显存与硬件](#9-性能显存与硬件)
- [10. 部署：包成 HTTP 服务](#10-部署包成-http-服务)
- [11. 批量打标](#11-批量打标)
- [12. 微调](#12-微调)
- [13. 与 TypeSafe Jev、通用 LLM 的对比](#13-与-typesafe-jev通用-llm-的对比)
- [14. 常见问题与排查](#14-常见问题与排查)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)
- [相关文档](#相关文档)

## 1. Laya 是什么

### 1.1 一句话

Laya 是一个「有判断力的 if」。普通 `if` 只能判断代码算得出来的条件（`order.total > 100`），判断不了「这条客服消息在骂人吗」「这段报错属于哪个模块」「这封邮件是钓鱼吗」。Laya 补的就是这一类判断，而且返回的是**带概率分布的枚举值**，不是一段自然语言。

```text
输入：state（要评估的内容，str / dict / list）+ questions（你命名的、带类型的问题）
输出：answers（同名的答案：枚举值 / 分数 / 0~1 的概率）+ usage（输入 token 数）

代码负责：阈值、分支、重试、副作用
模型负责：把非结构化文本映射成结构化的枚举与概率
```

### 1.2 和通用 LLM 的差别

| 维度 | 通用 LLM | Laya（System 1 决策模型） |
|---|---|---|
| 生成方式 | 自回归，逐 token 生成 | 非自回归，一次前向出全部答案 |
| 输出形态 | 自然语言 token 流，要解析 | 固定结构：choice / score / noul + 概率 |
| 输出空间 | 开放，可能编造你没定义的选项 | 闭合，只能在你给的选项/等级里选 |
| 延迟 | 秒级，随输出长度增长 | 本机 GPU 实测 84 ms（1 个问题）、45 ms/问题（50 个批量） |
| 出错方式 | 幻觉、格式漂移、JSON 截断 | 不编造选项值；但可能选错选项（概率低不等于错） |
| 不确定性 | 通常没有可用表达 | 每个答案带 probabilities 与 confidence |
| 成本 | 按 token 计费 | 自托管，$0（Apache 2.0 权重） |
| 适合 | 写作、代码、多轮推理、开放问答 | 分类、路由、打分、是/否判定、guardrail |
| 不适合 | —— | 生成文案、写代码、给理由、多轮对话 |

一句话选型：**要「一段文字」用 LLM，要「一个可分支的判定」用 Laya**。两者常组合使用：Laya 做前置路由与守门（本机实测 84 ms 一次前向、100 个问题 4.7 s），把真正需要推理的请求转发给 LLM，把不确定的转人工。

### 1.3 三个 checkpoint

Laya 一个仓库里打包了三份权重，只下载你要用的那份：

| | encoder | 参数量 | 上下文 | 用途 |
|---|---|---|---|---|
| `laya`（root） | ModernBERT-large | 421M | 512 | 英文 |
| `laya-multilingual` | mmBERT-base | 322M | 1024 | 100+ 语言，速度快一倍 |
| `laya-typed-decisions` | ModernBERT-large | 421M | 1024 | 四个 typed-decisions 工作流（在基准训练集上微调过） |

三份合计 1.165B 参数，仓库里对应 2.37 GB 权重（本机实测下载体积：root 842.61 MB + multilingual 643.84 MB + typed-decisions 842.61 MB）。

```python
agent          = laya.load("convaiinnovations/laya")                              # 英文
agent_ml       = laya.load("convaiinnovations/laya", subfolder="multilingual")    # 多语言
agent_td       = laya.load("convaiinnovations/laya", subfolder="typed-decisions") # 微调过的那份
```

`subfolder=` 只下载对应的子目录，不会把三份一起拖下来（源码里映射成 `snapshot_download(..., allow_patterns=["multilingual/*"])`）。Router 还认一批别名：`en`/`default` → english，`multi`/`ml` → multilingual，`typed`/`typed_decisions`/`decisions` → typed-decisions。

### 1.4 背景与名字

- System 1 / System 2 借自《思考，快与慢》：System 1 是快速直觉判断，System 2 是慢速推理。Laya 定位在「快判断」这一层。
- `laya`（लय）是梵语，意为「消融」，作者的 logo 寓意是「一段连续状态坍缩成一个类型化的决定」——正好是模型在做的事。
- 训练方法叫 RLCD（Reinforcement Learning for Calibrated Decisions）：奖励函数用的是**严格 proper 的评分规则**（对数分数 + 球面分数 + 有序 RPS），目标是让输出的概率本身可信，而不是让文字更像人话。源码里对应的函数是 `laya.common.proper_reward`。
- 权重 Apache 2.0；官方还给了 HuggingFace Space 在线 demo 和一整套 benchmark 脚本与原始结果（`research/` 目录）。
- 本文档的姊妹篇是同一时间整理的 [TypeSafe Jev 完整教程](../typesafe-jev/TypeSafe-Jev完整教程.md)：Jev 是托管闭源 API，Laya 是开源可自托管，两者常被放在一起比较（见第 13 章）。

### 1.5 「非自回归」到底意味着什么

自回归模型（GPT 类）每生成一个 token 都要跑一遍完整前向，所以「输出 200 个 token」= 200 次前向。Laya 把决策做成**对若干个选项位置打分**：序列里每个选项前面放一个 `[MASK]` 位置标记，模型一次前向算出所有标记位置的 logits，再 softmax 成概率。源码里的关键三行：

```python
# laya/common.py —— DecisionModel.forward 的后半段
idx = marker_pos.clamp(min=0)[:, :, None].expand(-1, -1, h.size(-1))
m = torch.gather(h, 1, idx)              # 取出每个选项标记位置的隐状态
logits = self.scorer(m).squeeze(-1).float()   # 每个选项一个分数
```

所以「问 1 个问题」和「问 100 个问题」只差一次前向的序列长度，不差前向次数——本机实测 1 个问题 84 ms、100 个问题 4.7 s（47.5 ms/问题，见第 9 章）。这也是它敢标「33 ms」的原因。

## 2. 安装

### 2.1 前置条件

```text
1. Python >= 3.8（实际建议 3.10+，本文用 3.12.3）
2. 磁盘：venv 约 6 GB（含 CUDA 版 torch 的依赖）+ 模型 0.85 GB / 份（三份 2.37 GB）
3. GPU 可选：CPU 也能跑，只是慢十几倍；显存要求见 2.4 与第 9 章
4. 网络：能访问 pypi（国内建议用镜像）与 HuggingFace（国内用 hf-mirror.com）
```

依赖树（PyPI 上 laya 0.3.4 的 `requires_dist`）：

```text
torch>=2.0.0
transformers>=4.45.0
safetensors>=0.4.0
huggingface_hub>=0.20.0
numpy>=1.20.0
```

注意这里面**没有** fastapi/uvicorn——那是本文第 10 章服务化时另外装的。

### 2.2 安装命令

官方只有一行：

```bash
pip install laya
```

实际项目里建议独立 venv，别污染系统环境（本文的做法）：

```bash
mkdir -p /opt/ai-lab/laya && cd /opt/ai-lab/laya
uv venv --python 3.12 .venv

# 国内把 pypi 换成清华镜像（本机实测 2~3 MB/s）
uv pip install --python /opt/ai-lab/laya/.venv/bin/python \
  --index-url https://pypi.tuna.tsinghua.edu.cn/simple laya
```

用 pip 的等价写法：

```bash
python3 -m venv /opt/ai-lab/laya/.venv
/opt/ai-lab/laya/.venv/bin/pip install laya \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2.3 本机安装实测

```text
$ cd /opt/ai-lab/laya && uv venv --python 3.12 .venv
Using CPython 3.12.3 interpreter at: /usr/bin/python3.12
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate

$ uv pip install --python /opt/ai-lab/laya/.venv/bin/python \
      --index-url https://pypi.tuna.tsinghua.edu.cn/simple laya
Downloaded triton
Downloaded nvidia-cublas
Downloaded torch
Downloaded nvidia-cudnn-cu13
Prepared 52 packages in 3m 10s
Installed 54 packages in 3.69s
 + annotated-doc==0.0.5
 + anyio==4.15.1
 + certifi==2026.7.22
 + click==8.5.0
 + cuda-bindings==13.4.2
 + cuda-pathfinder==1.8.2
 + cuda-toolkit==13.0.3.0
 + filelock==4.0.1
 + fsspec==2026.9.0
 + h11==0.16.0
 + hf-xet==1.6.0
 + httpcore==1.0.9
 + httpx==0.28.1
 + huggingface-hub==1.32.0
 + idna==3.10
 + jinja2==3.1.6
 + laya==0.3.4
 + markdown-it-py==4.2.0
 + markupsafe==3.0.3
 + mdurl==0.1.2
 + mpmath==1.3.0
 + networkx==3.6.1
 + numpy==2.5.3
 + nvidia-cublas==13.1.1.3
 + nvidia-cuda-cupti==13.0.85
 + nvidia-cuda-nvrtc==13.0.88
 + nvidia-cuda-runtime==13.0.96
 + nvidia-cudnn-cu13==9.24.0.43
 + nvidia-cufft==12.0.0.61
 + nvidia-cufile==1.15.1.6
 + nvidia-curand==10.4.0.35
 + nvidia-cusolver==12.0.4.66
 + nvidia-cusparse==12.6.3.3
 + nvidia-cusparselt-cu13==0.8.1
 + nvidia-nccl-cu13==2.30.7
 + nvidia-nvjitlink==13.4.92
 + nvidia-nvshmem-cu13==3.4.5
 + nvidia-nvtx==13.0.85
 + packaging==26.3
 + pygments==2.21.0
 + pyyaml==6.0.3
 + regex==2026.9.10
 + rich==15.0.0
 + safetensors==0.8.0
 + setuptools==84.0.0
 + shellingham==1.5.4
 + sympy==1.14.0
 + tokenizers==0.23.2
 + torch==2.14.0
 + tqdm==4.70.1
 + transformers==5.17.0
 + triton==3.8.0
 + typer==0.27.2
 + typing-extensions==4.16.0
```

几点值得注意：

```text
torch                 默认装的是 CUDA 13 构建（2.14.0+cu130），老显卡要换，见 2.4
transformers          装到了 5.17.0，laya 0.3.4 在这版上正常工作（本机验证）
huggingface_hub       1.32.0，带 hf-xet（Xet 传输协议），国内镜像不支持，见 2.5
numpy                 2.5.3，laya 只用了基础 API，没有 1.x/2.x 兼容问题
网络耗时              Prepared 52 packages 用了 3 分 10 秒（约 4 GB 依赖，走清华镜像）
```

### 2.4 torch 与显卡架构怎么选（本机真踩过）

`pip install laya` 拉的是 PyPI 上的默认 torch，现在是 **CUDA 13 构建**。CUDA 13 的 PyTorch 只编译 sm_75 及以上的内核，本机的 GTX 1050 是 **sm_61（Pascal）**，于是出现一种很难一眼看懂的失败：

```text
$ /opt/ai-lab/laya/.venv/bin/python probe_torch.py
/opt/ai-lab/laya/.venv/lib/python3.12/site-packages/torch/cuda/__init__.py:484: UserWarning: Found GPU0 NVIDIA GeForce GTX 1050 which is of compute capability (CC) 6.1.
The following list shows the CCs this version of PyTorch was built for and the hardware CCs it supports:
- 7.5 which supports hardware CC >=7.5,<8.0
...
Your installed torch==2.14.0+cu130 does not include kernels for this GPU. Reinstall the same version against a CUDA build that does, e.g.:
  For CUDA 12.6 use pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cu126
torch 2.14.0+cu130
cuda available True
arch list ['sm_75', 'sm_80', 'sm_86', 'sm_90', 'sm_100', 'sm_120']
device NVIDIA GeForce GTX 1050 cap (6, 1)
GPU FAIL: AcceleratorError CUDA error: no kernel image is available for execution on the device
Search for `cudaErrorNoKernelImageForDevice' in https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__TYPES.html for more information.
```

要点：`torch.cuda.is_available()` **返回 True**，所以代码不会走 CPU 分支，但一执行算子就抛 `no kernel image`。这就是「看着有 GPU，其实用不了」。

修复（换成同一版本的 cu126 构建，架构列表覆盖 sm_50~sm_90）：

```bash
uv pip install --python /opt/ai-lab/laya/.venv/bin/python \
  --index https://download.pytorch.org/whl/cu126 \
  --default-index https://pypi.tuna.tsinghua.edu.cn/simple \
  'torch==2.14.0+cu126'
```

修复后的复验（本机真实输出）：

```text
$ /opt/ai-lab/laya/.venv/bin/python probe_torch.py
torch 2.14.0+cu126
cuda available True
arch list ['sm_50', 'sm_60', 'sm_70', 'sm_75', 'sm_80', 'sm_86', 'sm_90']
device NVIDIA GeForce GTX 1050 cap (6, 1)
gpu matmul ok -7067.0947265625
```

怎么给别的卡选：

```text
Blackwell / RTX 50 系 (sm_120)   : PyPI 默认的 cu130 就行（laya 源码里也提示装 nightly cu128）
Ampere / Ada (sm_80/86/89)       : cu130 或 cu126 都行
Turing (sm_75)                   : cu130 还能用；更稳的选择是 cu126
Pascal / Volta (sm_60/61/70)     : 必须 cu126（或更早），cu130 没有内核
只有 CPU                          : torch 用 CPU 版即可（--index https://download.pytorch.org/whl/cpu）
```

只想跑 CPU 的话，装 CPU 版 torch 能把 venv 从 6 GB 压到 1 GB 左右，代价是每次决策从几十毫秒变成几百毫秒到一秒（本机实测见第 9 章）。

### 2.5 模型下载与国内镜像

权重在 HuggingFace 上（`convaiinnovations/laya`）。国内直连 huggingface.co 基本不通（本机实测 resolve 请求 50 秒超时），用镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1        # 关键，原因见下
```

`HF_HUB_DISABLE_XET=1` 是必须的：huggingface_hub 1.x 默认开启 Xet 传输协议（`hf-xet` 包），而 hf-mirror 不支持 Xet 的 CAS 端点，会在下载中途报 401：

```text
RuntimeError: Task error: File reconstruction error: CAS Client Error: Request error:
HTTP status client error (401 Unauthorized),
domain: https://cas-server.xethub.hf.cloud/v2/reconstructions/b944...
```

关掉 Xet 后走普通 HTTP，缓存里已下载的字节会复用，只补没下完的部分。

把三份权重一次性拉全（本文用的脚本，等价于分别 `laya.load` 三次）：

```python
import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ["HF_HUB_DISABLE_XET"] = "1"
from huggingface_hub import snapshot_download

REPO = "convaiinnovations/laya"
PLANS = {
    "english(root)":   ["*.json", "*.safetensors", "tokenizer/*", "encoder/*", "*.py"],
    "multilingual":    ["multilingual/*"],
    "typed-decisions": ["typed-decisions/*"],
}
for name, patterns in PLANS.items():
    print(name, snapshot_download(REPO, allow_patterns=patterns, max_workers=4))
```

下载完的体积（本机实测，与 HF API 记录的字节数逐个核对一致）：

```text
   842.61 MB  model.safetensors                     # 英文 ModernBERT-large
     3.58 MB  tokenizer/tokenizer.json
     0.00 MB  tokenizer/tokenizer_config.json
     0.00 MB  rl_agent_config.json
     0.00 MB  encoder/config.json
   643.84 MB  multilingual/model.safetensors        # 多语言 mmBERT-base
    34.36 MB  multilingual/tokenizer/tokenizer.json
   842.61 MB  typed-decisions/model.safetensors     # typed-decisions
     3.58 MB  typed-decisions/tokenizer/tokenizer.json
   合计 2.37 GB
```

一个容易踩的坑：`allow_patterns` 是 fnmatch 匹配**完整路径**，`*` 会跨过 `/`。所以 `"*.safetensors"` 会把 `multilingual/model.safetensors` 和 `typed-decisions/model.safetensors` 一起选中；只想拉 root 那份要写精确文件名（`model.safetensors`、`tokenizer/*`、`encoder/*` ……）。第 11 章的示例 `11_offline_load.py` 用精确模式把 root 单份落到本地目录，实测 0.85 GB。

### 2.6 首次加载要多久

权重文件在本地之后，`laya.load()` 仍要：读 `rl_agent_config.json` → 建 tokenizer → 用 `encoder/config.json` 建 encoder（`AutoModel.from_config`，此时是随机权重）→ 读 843 MB safetensors → 逐参数校验形状 → `load_state_dict` → 搬到设备并转 eval。本机实测冷加载耗时在 25~90 秒之间浮动（磁盘缓存热了之后 25~30 秒），这是正常的，不是卡死。

```text
从本地目录加载完成：device=cuda，耗时 26.3 s      # 缓存热
从本地目录加载完成：device=cuda，耗时 44.9 s      # 缓存冷
load 完成：device=cuda  laya 的 autocast dtype=torch.float16  耗时 27.1 s
```

## 3. 快速上手

### 3.1 Router 模式（推荐入口）

Router 是官方推荐的入口：它对任何语言、任何 schema 的 state 自动检测文字系统与语言，然后分发到最合适的 checkpoint。

```python
import laya
from laya import Router

router = Router(preload=True)      # 预加载三个 checkpoint，路由开销只剩检测（<1 ms）

state = {
    "from": "user@acme.com",
    "subject": "Duplicate charge on invoice #4411",
    "body": "Hi, we were billed twice for March. Please refund the duplicate today or we will cancel our plan."
}
questions = {
    "department": {
        "type": "choice",
        "instructions": "Which department should handle this request?",
        "criteria": {
            "billing": "invoices, payments, refunds",
            "technical": "bugs, outages, system errors",
            "sales": "pricing, new contracts",
            "other": "everything else",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this request?",
        "criteria": ["not urgent", "soon", "critical deadline or blocking issue"],
    },
    "churn_risk": {"type": "noul", "instructions": "Does the user threaten to cancel or leave?"},
    "refund_requested": {"type": "noul", "instructions": "Does the user explicitly request a refund?"},
}

res = router.predict(state, questions)
print(res["answers"]["department"]["choice"])    # billing
print(res["routing"]["model"])                   # english
```

本机真实运行结果（`examples/02_primitives.py`，英文那份 checkpoint，device=cuda）：

```text
加载完成，device=cuda，耗时 83.8 s
模型配置 rl_agent_config.json: {"encoder": "answerdotai/ModernBERT-large", "head_layers": 2,
 "max_len": 512, "head_max_len": 192, "max_prefixes": 6, "cost_wrong_act": 3.0,
 "amp_dtype": "bf16", "model_name": "rl-agent",
 "temperature": [1.6369030475616455, 1.2514300346374512, 1.983399510383606],
 "temperature_by_options": {"choice:3-5": 1.7601518630981445, "choice:6-10": 1.0000158548355103,
   "score:3-5": 1.2514300346374512, "noul:2": 1.983399510383606,
   "choice:11+": 0.10058280825614929, "choice:2": 1.9063563346862793},
 "training": {"updates": 7313, "epochs_completed": 1, "hours": 1.96, "world_size": 1,
   "fine_tuned_from_checkpoint": true}}

一次 forward 同时回答 4 个问题，用时 30598.1 ms，输入 372 tokens

department.choice        = billing
department.probabilities = {'billing': 0.9804, 'technical': 0.0077, 'sales': 0.0057, 'other': 0.0062}
department.confidence    = 0.9151
urgency.score            = 1.4356 / 2.0
urgency.probabilities    = {'0': 0.1149, '1': 0.3346, '2': 0.5505}
churn_risk.noul          = 0.2771
refund_requested.noul    = 0.3187
```

两点必须说清楚：

```text
1. 那次 30598 ms 是「进程里第一次前向」的一次性开销（CUDA 上下文 + 内核首次加载），
   同一个进程后续调用是 84~220 ms 量级，见第 9 章。排查性能时别拿第一次的数字。
2. churn_risk=0.2771 是真实的失败案例：文本里明明写着 "we will cancel our plan"，
   英文 checkpoint 零样本下判低了。官方 README 也承认：base checkpoint 在
   typed-decisions 上接近随机水平，能力来自微调（见第 12 章）。
```

### 3.2 单模型模式（直连 SDK）

只服务一种语言、或者已经知道该用哪份权重时，直接 `laya.load` 更省内存：

```python
import laya

agent = laya.load("convaiinnovations/laya")                            # 英文 root
agent_ml = laya.load("convaiinnovations/laya", subfolder="multilingual")   # 100+ 语言
agent_td = laya.load("convaiinnovations/laya", subfolder="typed-decisions")

result = agent.predict(state, questions)      # 一次前向回答全部问题
answers = result["answers"]
print(answers["department"]["choice"], answers["department"]["confidence"])
```

`laya.load` 的完整签名：

```python
laya.load(model_id_or_path="convaiinnovations/laya", device=None, token=None, subfolder=None)
```

```text
model_id_or_path  仓库 id 或本地目录路径（本地路径要求目录里有 rl_agent_config.json 与 model.safetensors）
device            "cpu" / "cuda" / "mps"，不传则自动：有可用 CUDA 就用 CUDA，其次 MPS，最后 CPU
token             HF 私有仓库 token，不传则读 HF_TOKEN 环境变量
subfolder         仓库内的 checkpoint 子目录（multilingual / typed-decisions）
```

### 3.3 返回值结构

`predict` 的返回（本机真实输出，去掉中间省略）：

```json
{
  "model": "laya-rl-agent",
  "answers": {
    "department": {
      "type": "choice",
      "choice": "billing",
      "probabilities": {"billing": 0.9804, "technical": 0.0077, "sales": 0.0057, "other": 0.0062},
      "confidence": 0.9151,
      "action": {"act_probability": 1.0}
    },
    "urgency": {
      "type": "score",
      "score": 1.4356,
      "legend": {"0": "not urgent", "1": "soon", "2": "critical deadline or blocking issue"},
      "probabilities": {"0": 0.1149, "1": 0.3346, "2": 0.5505},
      "confidence": 0.1411,
      "action": {"act_probability": 1.0}
    },
    "churn_risk": {"type": "noul", "noul": 0.2771, "confidence": 0.7229, "action": {"act_probability": 1.0}},
    "refund_requested": {"type": "noul", "noul": 0.3187, "confidence": 0.6813, "action": {"act_probability": 1.0}}
  },
  "usage": {"input_tokens": 372, "output_tokens": 0}
}
```

字段含义：

| 字段 | 含义 |
|---|---|
| `model` | 固定 `"laya-rl-agent"`（模型名，不是 checkpoint 名） |
| `answers.<id>.type` | 回显你定义的原语类型 |
| `choice` | 概率最高的选项名 |
| `probabilities` | 全部选项的概率（已按 checkpoint 自带温度缩放） |
| `score` | 位置值 = Σ(级号 × 该级概率)，可以落在两级之间 |
| `legend` | score 专用：级号 → 该级描述（键是字符串） |
| `noul` | 是/否里「真」的概率，0~1 |
| `confidence` | 归一化熵，不是「答对的概率」，见第 6 章 |
| `action.act_probability` | 模型另一个头（act_head）的输出，做「要不要执行动作」的辅助判断；官方 README 没有展开讲，本机实测恒为 1.0 量级，生产上先别依赖它 |
| `usage.input_tokens` | 这一批问题合起来消耗的 token 数（一次前向的序列总长） |
| `routing` | **只有 Router 模式有**：`{model, repo, reason, detection, workflow}` |

`output_tokens` 恒为 0——它不生成文本，这是最直观的「非自回归」证据。

## 4. 三种决策原语

原语只有三个，所有问题都从这三个里组合出来。

| 原语 | 问什么 | criteria 形式 | 答案字段 |
|---|---|---|---|
| `choice` | 从无序选项里选一个 | dict：`{选项名: 描述}`，描述可为 `None` | `choice`、`probabilities`、`confidence` |
| `score` | 在有序等级上打分 | **有序** list，2 项起 | `score`、`legend`、`probabilities`、`confidence` |
| `noul` | 是 / 否 | 可选 dict：`{true, false}` 各写一句界定 | `noul`、`confidence` |

选型口诀：

```text
有序 → score（紧急程度、愤怒程度、严重程度）
无序的类别 → choice（哪个部门、哪种意图、哪类商品）
是 / 否 → noul（是否要求退款、是否含凭证、是否越狱）
```

### 4.1 三种原语渲染成什么文本

选项不是直接扔给模型的，会先经过 `render_options` 变成固定格式的句子。本机真实输出（`examples/01_env_check.py`）：

```text
三种问题定义与它们实际渲染出的选项文本（render_options）：
  [choice]
    原始定义   : {"type": "choice", "instructions": "Which team should handle this?", "criteria": {"billing": "invoices, payments, refunds", "technical": "bugs, outages", "other": "none of the above"}}
    内部 t/ins : choice | Which team should handle this?
    渲染出的选项：
      0: billing: invoices, payments, refunds
      1: technical: bugs, outages
      2: other: none of the above
  [score]
    原始定义   : {"type": "score", "instructions": "How urgent is this?", "criteria": ["no time pressure", "needs attention soon", "blocking issue"]}
    内部 t/ins : score | How urgent is this?
    渲染出的选项：
      0: level 0: no time pressure
      1: level 1: needs attention soon
      2: level 2: blocking issue
  [noul]
    原始定义   : {"type": "noul", "instructions": "Does the user ask for a refund?"}
    内部 t/ins : noul | Does the user ask for a refund?
    渲染出的选项：
      0: false: no, the statement does not hold
      1: true: yes, the statement holds
```

读出来的三条规则：

```text
1. choice 的选项渲染成 "选项名: 描述"；描述为 None/空串时只留选项名（预设里的 topic 就用了 None）。
2. score 的选项渲染成 "level N: 描述"，级号是模型能看到的文本——但每一级是独立评估的，
   模型看不到「上一级/下一级」，所以描述必须写清场景，不能写「比上一级更严重」。
3. noul 固定两项：[false, true]，没写 criteria 时用默认的 "no, the statement does not hold" /
   "yes, the statement holds"。所以 instructions 建议写成陈述句，数值含义 = 「这句话为真的概率」。
```

描述可以不是字符串：dict/list/数字会被 render 成紧凑 JSON（源码 `render_criterion`），所以你可以给选项配结构化说明，比如 `{"what": ..., "not_for": ..., "examples": [...]}`，这些字段名不是 API 的一部分，随便起名，但会被模型看到——起名要自解释。

### 4.2 一次问多个问题

**这是最重要的一条使用习惯**：把同一段 state 上所有想问的问题放进同一个 dict、一次调用问完，而不是一个个问。本机实测（`examples/07_timing.py`，device=cuda）：

```text
=== 同一次 forward 里塞 n 个问题 ===
问题数    总耗时          每问题耗时          输入 tokens
1      84 ms        84.3 ms        59
5      283 ms       56.6 ms        295
10     493 ms       49.3 ms        590
50     2265 ms      45.3 ms        2950
```

序列长度是 59 + 59×(n-1) 的比例关系（每个问题自己一段 head + 选项），所以摊薄之后每个问题只花 45~50 ms。把它拆成 4 次单独调用，本机同一台机器上量到的是 4×200 ms 量级。

一个细节：假设 n=4 个问题 372 tokens（`02_primitives.py`），而 50 个问题 2950 tokens——**问题之间共享同一份 state 文本**，state 只编码一份。

### 4.3 state 怎么写

state 可以是三种类型，模型看到的是它们的文本化结果：

| state 类型 | 序列化方式 | 建议 |
|---|---|---|
| `str` | 原样 | 只有一段正文时最简单 |
| `dict` | `json.dumps(..., ensure_ascii=False)`（键名也进序列） | 邮件/工单/JSON 文档，最常用 |
| `list` | 同样 JSON 化，适合对话轮次 | 多轮对话 |

```python
agent.predict({"body": "duplicate charge"}, questions)          # dict，推荐
agent.predict("duplicate charge", questions)                    # str
agent.predict([{"role": "user", "text": "..."}], questions)     # list
```

两个实践要点：

```text
1. 键名也会进序列，所以命名要有信息量（{"customer_message": ...} 比 {"a": ...} 好）。
2. state 只保留判定需要的内容。邮件场景官方专门给了 clean_email_body 去引用/签名/免责声明
   （第 8 章），一是省 token，二是去噪声——本机实测 506 字符的邮件清洗后只剩 104 字符。
```

### 4.4 内部机制：序列怎么拼

`laya.common.build_sequence` 把一条输入拼成：

```text
[CLS] "choice question: <instructions>" [SEP] [MASK]opt0 [MASK]opt1 ... [SEP] state [SEP]
                              ↑ head（受 head_max_len 限制）        ↑ 每个选项一个 MASK 标记
```

源码里的几个实现细节值得知道，因为它们解释了实际行为：

```text
1. 每个选项最多保留 48 个 token（tok(...)[:48]）。
2. head 预算不够时（head_max_len - 选项总长 < 16），每个选项被截断到
   max(4, (head_max_len - 16) // 选项数) 个 token —— 选项越多，每个选项留下的越少。
   这是高基数选择题精度崩掉的根因，见第 7 章。
3. state 部分超过 (max_len - head 长度) 时按 truncate_left=False 截断：保留前一段、砍掉尾部。
4. 一次前向里 n 个问题各自拼一条序列，collate 成 batch 一次算完。
```

一个真实例子说明第 3 点的影响：state 写 500 遍 "duplicate charge refund"（11999 字符 ≈ 1503 tokens），实际只送进去 512 tokens——**如果关键诉求写在最后（"请立即退款"），它是被砍掉的那部分**。解决办法只有自己在传进来之前先把 state 截短、或者把关键内容前置。

## 5. Router：三个 checkpoint 的路由

### 5.1 为什么需要路由

官方在共享基准（17,416 个问题，单卡 T4，每个模型回答同一批问题）上量到（**官方数据**）：

| 基准 / 任务 | 英文 `laya` | `laya-multilingual` | Router 路由后 |
|---|---|---|---|
| MASSIVE intent，英文 | **0.783** | 0.657 | **0.783** |
| MASSIVE intent，其余 13 种语言 | 0.306 | **0.451** | **0.451** |
| XNLI，英文 | **0.860** | 0.843 | **0.860** |
| XNLI，其余 14 种语言 | 0.521 | **0.731** | **0.731** |
| 可用语言数（> 3 倍随机） | 23 / 51 | 45 / 51 | **45 / 51** |
| 单问题延迟（T4） | 39.5 ms | **32.8 ms** | **32.8 ms** |
| 10 问题批量延迟（T4） | 158.6 ms | **72.3 ms** | **72.3 ms** |

关键结论不是「多语言版更强」，而是：**英文 checkpoint 在非拉丁文字上不是缓慢退化，是直接崩掉**——高棉语（Khmer）准确率 **0.000、置信度 0.952**。模型在完全答错的时候依然自信，所以「用置信度门控兜底」这条路走不通，必须在前向之前就把路由决定做掉。这正是 Router 存在的理由。

### 5.2 语言与文字系统检测

`laya.lang` 是一个**零依赖的纯 Python 检测器**（只 import 了 `re`），本机实测耗时（`examples/03_router.py`）：

```text
=== 1. 纯 Python 的语言/文字系统检测（<1 ms，不加载模型，不跑前向） ===
  英文     script=latin        language=en     is_english=True  非拉丁占比=0.00  detect_script 耗时 7 us
  德文     script=latin        language=de     is_english=False 非拉丁占比=0.00  detect_script 耗时 5 us
  法文     script=latin        language=fr     is_english=False 非拉丁占比=0.00  detect_script 耗时 5 us
  印地文    script=devanagari   language=None   is_english=False 非拉丁占比=1.00  detect_script 耗时 50 us
  中文     script=han          language=None   is_english=False 非拉丁占比=1.00  detect_script 耗时 118 us
  韩文     script=hangul       language=None   is_english=False 非拉丁占比=1.00  detect_script 耗时 128 us
  泰文     script=thai         language=None   is_english=False 非拉丁占比=1.00  detect_script 耗时 173 us
  停用词启发式（guess_latin_language）单独调用： de / False
```

它是怎么判断的（源码 `lang.py`）：

```text
文字系统（script）：把每个字母按 Unicode 区间归类（greek/cyrillic/hebrew/arabic/devanagari/
  bengali/gurmukhi/gujarati/oriya/tamil/telugu/kannada/malayalam/sinhala/thai/lao/tibetan/
  myanmar/georgian/ethiopic/khmer/hangul/kana/han 共 25 组区间），取占比最大的那个。
  带音标的拉丁扩展（U+1E00–U+1EFF）也算 latin。没有字母 → unknown。这一步是精确判断，不猜。
语言（language）：只对拉丁文字做，而且是「尽力而为」的启发式——统计 7 种语言
  （en/fr/de/es/pt/it/nl）的函数词命中数，要求非英语语言以「至少 2 票、且比英语多 2 票」
  的余量胜出；词数少于 4 个时直接返回 None。所以短文本、混合文本通常判不出来，
  这时会落到默认的英文 checkpoint。官方源码注释也直说了：知道语言就显式传 lang=。
```

### 5.3 路由优先级与 reason

判定顺序（源码注释原文：`explicit model > explicit task > detected workflow (opt-in) > explicit lang > detected script/language > default`）。本机真实输出：

```text
=== 2. route()：只做决策，不加载、不推理 ===
  router.loaded = []  (空列表 = 还没加载任何 checkpoint)
  英文工单             -> model=english       repo=convaiinnovations/laya
                      reason=English Latin text
  德文工单             -> model=multilingual  repo=convaiinnovations/laya/multilingual
                      reason=Latin script but language looks like 'de', not English
  印地文工单            -> model=multilingual  repo=convaiinnovations/laya/multilingual
                      reason=non-Latin script (devanagari, 100% of letters); the English checkpoint cannot read it
  中文工单             -> model=multilingual  repo=convaiinnovations/laya/multilingual
                      reason=non-Latin script (han, 100% of letters); the English checkpoint cannot read it
  只有数字没有字母         -> model=english       repo=convaiinnovations/laya
                      reason=no letters detected in state; using default (english)
  显式指定： explicit model='typed-decisions'
  显式指定语言： explicit lang='de'
```

`reason` 是一句人能读懂的解释，会随结果一起返回（`res["routing"]["reason"]`）。线上排查「为什么这条走了多语言模型」时非常有用，建议直接记进日志。

`route()` 不加载模型、不跑前向，只做检测，所以可以单独拿来当「这批数据该用哪份权重」的统计工具：

```python
from laya import Router
router = Router()
decision = router.route({"body": "Der Kunde wurde zweimal belastet"}, questions)
print(decision.reason)   # Latin script but language looks like 'de', not English
print(dict(decision))    # {'model': ..., 'repo': ..., 'reason': ..., 'detection': {...}, 'workflow': None}
```

`typed-decisions` 默认**不会**被自动选中（它只在那四个特定工作流上微调过），除非显式 `model="typed-decisions"`、`task="typed_decisions"`，或者打开 `auto_task_detection=True` 且问题 id 集合恰好等于四个工作流签名之一（`customer_service` / `invoice_processing` / `security_incidents` / `agent_trace_observability`，要求 id 集合完全相等，避免误命中）。

### 5.4 显存管理与生命周期

```python
router = Router()                           # 懒加载：用哪个加载哪个
router = Router(max_loaded=2)               # 最多常驻 2 份，LRU 淘汰
router.preload(["english", "multilingual"]) # 启动时把这两份都建好
router.attach("english", existing_agent)    # 复用进程里已有的 Agent，避免重复占显存
router.unload("english")                    # 释放一份
router.unload()                             # 释放全部
router.loaded                               # ['english', 'multilingual']
```

懒加载的代价很大：`max_loaded=1` 时，语言交替的流量会在**每次请求**重建模型。官方在 CPU 上量到中位 7.4 秒、T4 上 10.3 秒的重建时间。本机实测一次完整的 `preload`：

```text
  preload 两个 checkpoint 用时 64.6 s，常驻：['english', 'multilingual']
```

所以生产环境只有两种正确姿势：`preload()` 常驻（内存/显存够），或者按语言把流量分片、每个分片只服务一份权重。别让 Router 单份懒加载去接多语言流量。

### 5.5 一个必须知道的坑：`Router(preload=[...])`

官方 README 里同时出现了两种写法：

```python
router = Router(preload=True)                     # 官方推荐写法
router.preload(["english", "multilingual"])       # 官方也给了方法调用写法
```

但把列表直接传给构造函数——`Router(preload=["english"])`——它**不会**只加载 english。看源码：

```python
def __init__(self, ..., preload: bool = False, ...):
    ...
    if preload:            # 只判断真假，传列表永远为真
        self.preload()     # 无参调用 → names=None → 加载 DEFAULT_MODELS 里的全部三份
```

本机复现（`diag_mem.py router`）：

```text
  preload 用时 310.0 s loaded=['english', 'multilingual', 'typed-decisions']
  [preload 之后] allocated=2.99 GB reserved=4.16 GB
  [第一次前向之后] allocated=3.00 GB reserved=4.16 GB

[laya] Warning: could not place the model on cuda, so it is running on CPU.
  Reason: CUDA out of memory. Tried to allocate 22.00 MiB. GPU 0 has a total capacity of 3.94 GiB
  of which 19.88 MiB is free. ...
```

后果：4 GB 显存的卡直接 OOM，laya 把模型退回 CPU（推理还能跑，只是慢十几倍），而 `router.loaded` 会告诉你三份都在。正确写法是两步：

```python
router = Router(device=None)          # 不要在这里传列表
router.preload(["english"])           # 只加载你要服务的那几份
```

本文的 04/05/06/12/13 五个示例最初都踩了这个坑，现已全部改成两步写法。

## 6. 置信度与校准

### 6.1 confidence 到底是什么

它**不是**「答对的概率」，而是**归一化熵**：分布越集中越高。源码：

```python
def confidence_from_probs(p, k):
    """Normalized Shannon entropy confidence: 1 - H(p) / log(k)."""
    if k < 2:
        return 1.0
    p = p[:k]
    ent = -(p * np.log(np.clip(p, 1e-12, 1.0))).sum()
    return float(np.clip(1.0 - ent / math.log(k), 0.0, 1.0))
```

推论（很重要）：

```text
1. confidence 高 = 分布尖，不代表对。本机实测里 refund → cancellation 的错误样本
   confidence 高达 0.999（见 6.3 的逐条表）。
2. 选项少的题天然容易「看起来自信」：2 个选项时全押一边就接近 1.0。
   跨题目比较 confidence 没意义，只能在同一题型的分布里比。
3. noul 的 confidence 是 max(p_true, 1-p_true)，所以「强烈的否」也是高 confidence，
   方向要看 noul 值本身。
4. score 的 confidence 低不代表答案差：三级题概率摊成 {0.11, 0.33, 0.55} 时
   confidence 只有 0.141（本机真实输出），但 score=1.4356 这个位置值仍然有信息量。
```

### 6.2 温度：概率已经被收拾过一轮

checkpoint 里带着两套温度参数，`system_one` 在 softmax 之前会除一下（`z = logits / t_scale`）：

```python
# 英文 checkpoint（本机真实读出）
agent.temperature = [1.6369030475616455, 1.2514300346374512, 1.983399510383606]   # 按 [choice, score, noul]
agent.temperature_by_options = {
    'choice:3-5': 1.7601518630981445, 'choice:6-10': 1.0000158548355103,
    'score:3-5': 1.2514300346374512,  'noul:2': 1.983399510383606,
    'choice:11+': 0.10058280825614929, 'choice:2': 1.9063563346862793,
}
```

取值规则：先按 `(原语, 选项数)` 分桶（2 / 3-5 / 6-10 / 11+）查 `temperature_by_options`，查不到就用按原语的 `temperature`。注意 `choice:11+` 是 **0.10**——这个小于 1 的锐化温度是给高基数选择题准备的，与 `choice:6-10` 的 1.0 差了一个数量级。

所以：**你拿到的 probabilities 已经是校准过的**，不要以为它是原始 logits 的 softmax。

### 6.3 自己再校准一次：本机实测

官方 README 说两个 checkpoint 出厂都过度自信：在 held-out 数据上按 `(问题类型, 选项数)` 分桶拟合温度后，平均 ECE 从 **0.466 → 0.081**（英文）、**0.314 → 0.106**（多语言），并特别提示 `laya-multilingual` **完全没有**附带拟合温度，用它的概率之前必须自己拟合。

本文用一个手写的 48 条带标签样本（六类客服意图，`examples/10_calibration.py`）走了一遍完整流程。**注意：48 条是本文作者手写的、只用于演示方法，不代表 Laya 的真实精度。** 本机真实输出：

```text
checkpoint 自带的温度参数 agent.temperature = [1.6369030475616455, 1.2514300346374512, 1.983399510383606]

训练集 24 条 / 测试集 24 条

=== 校准前（官方发布的温度参数） ===
  训练集  accuracy=0.625  mean confidence=0.828  ECE=0.2444
  测试集  accuracy=0.708  mean confidence=0.759  ECE=0.1605

=== 在训练集上网格搜索温度（目标：ECE 最小） ===
  T=0.50  训练集 ECE=0.3357
  T=0.75  训练集 ECE=0.2815
  T=1.00  训练集 ECE=0.2444
  T=1.50  训练集 ECE=0.2456
  T=2.00  训练集 ECE=0.1733
  T=2.50  训练集 ECE=0.2099
  T=3.00  训练集 ECE=0.1462
  T=4.00  训练集 ECE=0.2847
  T=5.00  训练集 ECE=0.2152
  T=6.00  训练集 ECE=0.2433
  选出 T = 3.00

=== 在测试集上验证（温度只在训练集上拟合过） ===
  校准前 T=1.0        accuracy=0.708  mean confidence=0.759  ECE=0.1605
  校准后 T=3.00       accuracy=0.708  mean confidence=0.476  ECE=0.3087

=== 逐条看校准前后的置信度 ===
真实标签       预测                 对错       置信度 校准前 -> 校准后
refund     refund             对        0.836 -> 0.471
refund     refund             对        0.647 -> 0.388
refund     cancellation       错        0.999 -> 0.806
refund     refund             对        0.996 -> 0.738
technical_help technical_help     对        0.982 -> 0.599
technical_help technical_help     对        0.843 -> 0.451
technical_help technical_help     对        0.711 -> 0.405
technical_help other              错        0.560 -> 0.306
billing_question billing_question   对        0.479 -> 0.272
billing_question billing_question   对        0.877 -> 0.446
```

结论：**在 24 条上拟合出来的 T=3.00 拿到测试集上，把 ECE 从 0.1605 变成了 0.3087——反而更差。** 这是小样本拟合温度的典型过拟合，也是本文想强调的一课：官方那个 0.466 → 0.081 是在几千条 held-out 数据上、按 `(问题类型, 选项数)` 分桶分别拟合的；样本量不够就别自己拟合温度。

### 6.4 更实用的做法：不信任概率数值，直接量阈值

比起相信「0.9 就是 90% 正确」，更靠谱的是在自己的带标签数据上量一张阈值表。本机真实输出（同一个 24 条测试集）：

```text
=== 更实用的做法：不信任概率数值，直接量阈值 ===
门槛         放行数      其中对的       精确率        人工兜底数
0.50       21       15         0.714      3
0.70       14       11         0.786      10
0.85       9        7          0.778      15
0.95       6        5          0.833      18
```

读法：门槛越高，自动化那一部分的精确率越高、送人工的越多。0.85 门槛下，9 条被自动处理、其中 7 条正确（精确率 0.778）、15 条进人工队列。**这些数字来自 24 条样本，量级仅供参考，正式评估至少几百到几千条。**

工程上的三条结论：

```text
1. 阈值必须按业务量出来，不能照抄别人的 0.85。
2. confidence 是分布的形状、不是绝对准确率，同一阈值在不同题型含义不同，
   所以阈值应该按 (题型, 选项数) 分桶设置，跟 checkpoint 自己的温度分桶对齐。
3. 混合路由（英文走 english、其他走 multilingual）会让阈值口径不一致，量阈值要分模型量。
```

## 7. token 预算与高基数选项

### 7.1 两段预算

```text
head_max_len  留给「问题类型 + 指令 + 所有选项」的 token 预算
              english: 192 ，multilingual / typed-decisions: 256
max_len       整条序列上限：english 512，另两份 1024
              留给 state 的 = max_len - head 实际长度
```

多语言/typed-decisions 用的 mmBERT-base 编码器本身支持 8192（RoPE），所以 max_len 可以往上调，只是要自己改 `agent.cfg`。

### 7.2 选项越多，每个选项留下的越少

本机真实输出（`examples/08_token_budget.py`，英文默认配置）：

```text
=== 选项数与 head 预算（head_max_len=192） ===
选项数      选项原始占用           剩余给指令          每选项保留 token
4        28               164            44
10       70               122            17
30       210              -18            5
50       350              -158           4
77       539              -347           4
120      840              -648           4
```

机制（源码 `build_sequence`）：每个选项先按 48 token 截断；如果所有选项加起来把 head 预算吃到只剩不到 16 token，就统一把每个选项截到 `max(4, (head_max_len - 16) // 选项数)`——**下限是 4 个 token**。所以 50 个以上选项时，每个选项只有 4 个 token 的可见长度。

真实选项被截成什么样（本机输出）：

```text
=== 截断后模型实际看到的选项文本（77 个选项，每选项只留 4 个 token） ===
  原选项 intent_00: intent 00 -> 截断后保留 '[MASK] intent_00'
  ...
  换成真实的长标签更能看出问题：
    billing: invoices, payments, refunds and duplicate charges   -> 4 个 token 后只剩 '[MASK] billing: invo'
    technical: bugs, outages, integrations and system errors     -> 4 个 token 后只剩 '[MASK] technical: bugs'
    sales: pricing, demos, new purchases and contract renewals   -> 4 个 token 后只剩 '[MASK] sales: pricing'
  对比：4 个选项时每选项可留 44 token，整句描述都能看到。
```

官方 README 承认了对应的精度代价：Banking77（77 个标签）上 Laya 0.425，而 TypeSafe Jev 0.870——「> 20 个选项」是 Laya 明确弱于 Jev 的地方（**官方数据**）。

### 7.3 修法一：抬高预算

```text
  head_max_len=192   -> 每选项保留 4 token
  head_max_len=256   -> 每选项保留 4 token
  head_max_len=512   -> 每选项保留 6 token
  head_max_len=1024  -> 每选项保留 13 token
  抬高后实际跑一次：2368 ms，输入 483 tokens，答案 = intent_09
```

代码：

```python
agent.cfg["head_max_len"] = 512      # 给选项更多空间
agent.cfg["max_len"] = 1024          # 同时把总长抬上去，否则 state 没地方放
```

代价是序列变长、延迟上升（本机 77 选项从 ~150 ms 涨到 2368 ms）。官方建议做 50+ 选项时把 `head_max_len` 设到 512、`max_len` 设到 1024（也可以一路到 2048/4096/8192）。

### 7.4 修法二：两级选择（更推荐）

把一个大选项集拆成「先选大类、再选具体项」，每级的选项数都很小，两者的 token 预算都充裕。本机真实输出：

```text
=== 修法二：两级选择（先大类，再具体项）——每级选项数都很小 ===
  第一级 = group_a {'group_a': 0.381, 'group_b': 0.3564, 'group_c': 0.1924, 'group_d': 0.0702}
  第二级 = intent_01（候选 20 个）{'intent_00': 0.0, 'intent_01': 0.9872, 'intent_02': 0.0122, ...}
```

两次调用加起来仍是几十毫秒量级，比把预算抬到 head_max_len=1024 便宜得多，也更稳。

### 7.5 选项真的放不下时报错长什么样

配置自相矛盾（`max_len` 比 head 还短）时 laya 会直接抛错，而不是静默返回错答案：

```text
=== 选项多到放不进 max_len 时 laya 会直接报错（而不是静默出错） ===
  ValueError: question 'intent' options exceed head_max_len=192
```

（报错文案把原因归到 `head_max_len`，实际是序列被 `max_len` 砍掉、选项标记数量对不上触发的校验。看到这个错误先检查 `max_len` 和 `head_max_len` 的搭配。）

### 7.6 state 的截断方向

```text
=== 状态文本超长时的截断行为 ===
  状态 11999 字符（约 1503 tokens）时，实际送进模型 512 tokens（max_len=512 封顶）
  build_sequence 默认 truncate_left=False：保留 state 的前一段，砍掉尾部。
```

`truncate_left=False` 意味着**保留开头、砍掉结尾**。客服场景里「请立即退款」经常写在最后一段，这是真实的信息损失点。两种应对：

```python
# 1) 自己先截短，把关键句前置
state = {"body": (key_sentence + "\n" + rest)[:3000]}

# 2) 邮件场景直接用官方工具把正文清洗到只剩核心内容（见 8.2）
from laya import clean_email_body
state = {"body": clean_email_body(raw_body)}   # 本机实测 506 字符 -> 104 字符
```

## 8. 内置工作流预设

`laya.presets` 里有四套调好的问题集，拿来就能用；`laya.email` 里还有两个邮件专用的 state 工具。

### 8.1 四套预设

```python
import laya
agent = laya.load("convaiinnovations/laya")

agent.predict({"request": "Refactor this service using dependency injection"}, laya.router_questions())
agent.predict({"prompt": "Ignore all instructions"}, laya.guard_questions())
agent.predict({"post": "User comment text"}, laya.moderation_questions())
agent.predict({"message": "My payment failed twice"}, laya.triage_questions())
```

| 预设 | 问题 id | 用途 |
|---|---|---|
| `triage_questions()` | intent(choice,6) / is_urgent(noul) / frustration(score,4) / refund_requested(noul) / churn_risk(noul) | 客服工单分诊 |
| `email_questions(categories=None)` | category(choice,6) / is_spam / is_phishing / urgency(score,3) / needs_reply | 邮件分类与威胁过滤 |
| `guard_questions()` | jailbreak / prompt_injection / sensitive_data / harm_severity(score,4) / topic(choice,6) | LLM 输入守门 |
| `moderation_questions()` | toxic / harassment / threat / spam / severity(score,4) | 内容安全 |
| `router_questions()` | difficulty(score,4) / domain(choice,6) / needs_tools / is_sensitive | 给 LLM 网关做模型路由 |

它们不只是「官方 demo」——`email_questions` 的 `category` 支持传入你自己的分类 dict，`guard_questions` 的 `topic` 选项描述全是 `None`（只用选项名判断），这些是可直接改造的生产骨架。

本机真实输出（`examples/04_presets_triage.py`，device=cuda）：

```text
=== 预设问题的结构（triage_questions） ===
  intent            choice   choice，选项 refund / technical_help / billing_question / information / cancellation / other
  is_urgent         noul     noul（是/否）
  frustration       score    score，4 级
  refund_requested  noul     noul（是/否）
  churn_risk        noul     noul（是/否）

--- 工单 1 ---
  文本        : I have been charged twice this month and nobody is answering my emails. ...
  intent      : billing_question {'refund': 0.3056, 'technical_help': 0.0017, 'billing_question': 0.6235, 'information': 0.0012, 'cancellation': 0.0198, 'other': 0.0482} confidence 0.4979
  is_urgent   : 0.7894 (confidence 0.7894)
  frustration : 1.9049 / 3.0 {'0': 0.0208, '1': 0.1254, '2': 0.782, '3': 0.0718}
  refund?     : 0.8569
  churn_risk  : 0.8559

--- 工单 2 ---
  文本        : How do I add another seat to our team plan?
  intent      : other {'refund': 0.0214, 'technical_help': 0.0121, 'billing_question': 0.0114, 'information': 0.0568, 'cancellation': 0.0167, 'other': 0.8816} confidence 0.7047
  is_urgent   : 0.0725 (confidence 0.9275)
  frustration : 0.9704 / 3.0 {'0': 0.3688, '1': 0.3443, '2': 0.2345, '3': 0.0524}
  refund?     : 0.0
  churn_risk  : 0.0031

--- 工单 3 ---
  文本        : Your API returns 502 on the /v2/export endpoint since the last release.
  intent      : technical_help {'refund': 0.0004, 'technical_help': 0.9967, ...} confidence 0.985
  is_urgent   : 0.0443 (confidence 0.9557)
  frustration : 1.5321 / 3.0 {'0': 0.1282, '1': 0.2409, '2': 0.6013, '3': 0.0295}
  refund?     : 0.1906
  churn_risk  : 0.1173

=== 按预设结论做分支（confidence 门控） ===
  判定结果： 转人工（intent confidence=0.50, churn=0.86）
```

三个直接看出来的行为：技术问题判定得很干脆（0.9967）；模板化的短问题被判成 `other`（缺上下文时模型会往「都不像」上靠）；而明确写了 "switching to your competitor" 的工单拿到 churn=0.8559——这是第 3 章那个 churn=0.2771 的反例，说明零样本下的稳定性依赖文本显式程度。

### 8.2 邮件工具

```python
from laya import clean_email_body, email_state, email_questions

cleaned = clean_email_body(raw_body)                 # 去引用/签名/免责声明
state   = email_state(subject, body, sender="john.doe@acme.com")   # 生成标准 state
res     = agent.predict(state, email_questions())
```

`clean_email_body` 做的事（正则规则，源码可查）：

```text
1. 逐行扫：遇到 "On ... wrote:" / "-----Original Message-----" / 连续下划线 / "From: " 开头的
   引用头就整段截断，独立的 ">" 引用行直接丢弃。
2. 找签名：从行数 60% 处往后扫，遇到 "--"、"Best regards"、"Thanks"、"Sent from my iPhone"
   这类短行即截断。
3. 段落级再过滤免责声明（confidential / intended solely for the addressee / received this
   email in error）。
4. 合并空白，默认上限 3000 字符。
```

本机真实输出（`examples/05_email_triage.py`）：

```text
=== clean_email_body 的效果 ===
  原文 506 字符 -> 清洗后 104 字符
  清洗后全文：
    | Hi support team,
    | 
    | We were charged twice for the March invoice. Please refund the duplicate charge today.
  引用段被丢弃： True
  签名被丢弃  ： True
  免责声明被丢弃： True

--- 重复扣费（正常工单） ---
  category   : billing {'billing': 0.987, 'technical': 0.0028, 'sales': 0.0024, 'security': 0.0023, 'hr': 0.0016, 'other': 0.0039}
  is_phishing: 0.0135  confidence 0.9865
  is_spam    : 0.0
  urgency    : 1.1742 / 2.0
  needs_reply: 0.0928

--- 钓鱼邮件 ---
  category   : security {'billing': 0.0014, 'technical': 0.0046, 'sales': 0.0011, 'security': 0.9917, 'hr': 0.0006, 'other': 0.0007}
  is_phishing: 0.834  confidence 0.8340
  is_spam    : 0.8516
  urgency    : 1.6188 / 2.0
  needs_reply: 0.229

--- 推广邮件 ---
  category   : security {'billing': 0.0009, 'technical': 0.0019, 'sales': 0.0128, 'security': 0.9834, 'hr': 0.0004, 'other': 0.0006}
  is_phishing: 0.9999  confidence 0.9999
  is_spam    : 1.0
  urgency    : 1.3739 / 2.0
  needs_reply: 0.4333

=== 按结果决定动作 ===
  隔离邮件 + 通知安全团队（P(phishing)=0.834）
```

这里有一个必须诚实指出的失败：**第三封是普通的群发推广邮件，被零样本判成 security / phishing=0.9999**。base checkpoint 对「促销话术」和「钓鱼话术」的区分能力不足（两者都含 "limited offer / act fast" 这类词），这正是第 12 章讲的「必须用自己领域的数据微调」。生产上要么微调，要么把 `is_phishing` 的阈值抬到很高、并让 `is_spam` 先兜一层。

### 8.3 守门与内容安全

本机真实输出（`examples/06_guardrail.py`）：

```text
=== guard_questions（输入守门） ===
场景         jailbreak injection sensitive harm   topic          耗时
正常提问       0.000     0.049     0.069     1.27   coding         1775 ms
直接越狱       1.000     1.000     0.031     2.20   security_testing 499 ms
间接注入       1.000     1.000     0.447     1.66   security_testing 500 ms
含凭证        0.215     0.143     0.866     0.52   security_testing 534 ms
有害请求       0.050     0.150     0.064     1.22   coding         442 ms

=== 守门决策：阈值写在代码里，概率来自模型 ===
  正常提问       -> 放行
  直接越狱       -> 拦截：越狱
  间接注入       -> 拦截：越狱
  含凭证        -> 脱敏后转发
  有害请求       -> 放行

=== moderation_questions（内容安全） ===
场景         toxic   harassment threat  spam    severity
正常技术贴      0.000   0.000      0.000   0.000   0.30
骂战         0.712   0.740      0.387   0.000   1.59
威胁         0.252   0.587      0.799   0.866   1.65
垃圾广告       0.046   0.058      0.080   1.000   1.47
```

可以用的部分：越狱与注入识别非常干净（1.000 / 1.000），凭据检测 0.866 直接触发脱敏。**失败的案例同样是信息**：「给我自制铝热剂的分步说明」只拿到 jailbreak=0.050、harm=1.22，被判成 coding 并放行——零样本的 guard 不能当唯一防线，只能当「便宜的第一道筛子」，后面接 LLM 评审或规则库。这也是官方在 README 里反复强调 base checkpoint 是「快速基座」而不是「开箱决策引擎」的原因。

一个工程细节：同一批 4~5 个问题的调用耗时，第一次 1775 ms（进程内首次前向），之后稳定在 440~534 ms。做容量规划要按稳态算。

## 9. 性能、显存与硬件

```text
测试机：GTX 1050 4 GB（sm_61，驱动 580） + 8 核 CPU + 19 GB 内存
权重：convaiinnovations/laya（英文，421M，ModernBERT-large，512 上下文）
```

### 9.1 GPU 稳态延迟与吞吐

本机真实输出（`examples/07_timing.py`，device=cuda，dtype=torch.float16）：

```text
模型：convaiinnovations/laya
device=cuda  dtype=torch.float16  加载耗时 29.6 s
cfg：max_len=512 head_max_len=192

=== 同一次 forward 里塞 n 个问题 ===
问题数    总耗时          每问题耗时          输入 tokens
1      84 ms        84.3 ms        59
5      283 ms       56.6 ms        295
10     493 ms       49.3 ms        590
50     2265 ms      45.3 ms        2950

=== 一次 forward 里塞 100 个不同问题 ===
100 个问题：4748 ms，即 47.5 ms/问题，5900 tokens
返回的答案个数： 100

=== 同一批问题重复 20 次（看稳态延迟） ===
min=219 ms  p50=220 ms  mean=220 ms  max=225 ms

GPU 显存占用：2.62 GB（torch.cuda.max_memory_allocated）
```

读法：

```text
1. 单问题 84 ms（4 个问题一起问是 220 ms 稳态），摊薄到 45~47 ms/问题。
   官方在 T4 上量到 39.5 ms / 7.2 ms per question（批量），本机这块 4 GB 老卡慢一倍多，
   量级一致，符合「源码 amp_dtype 是 bf16，但在算力 < 8.0 的卡上被强制成 fp16」的预期。
2. 吞吐 ≈ 1/0.045 ≈ 22 问题/秒（这块卡）。官方在 T4 上给的是 103~332 问题/秒。
3. 3 个问题的请求在这块卡上是 220 ms 稳态，一天 86400 秒 → 单进程约 39 万次请求/天。
4. p50 与 max 只差 6 ms，没有明显抖动，适合做同步阻塞式的在线判定。
```

### 9.2 第一次前向的一次性开销

同一进程里的**第一次** `predict` 明显更慢，本机实测：

```text
02_primitives.py（4 个问题）：30598 ms     ← 进程内第一次
03_router.py   （3 个问题）：11449 ms      ← 多语言 checkpoint 的第一次
06_guardrail.py（5 个问题）：1775 ms
07_timing.py   （预热之后的测量）：84 ms / 220 ms
```

这是 CUDA 上下文初始化 + 内核首次加载的一次性成本，不是每步开销。**服务化时必须在启动阶段做一次预热调用**（第 10 章的 `/health` 就是干这个的），否则第一个真实用户要多等 1~30 秒。

### 9.3 CPU 对照

CPU 下 laya 用 fp32 推理（源码：`device.type in ("cpu","mps") → dtype=torch.float32`），输出结构不变，只是慢。`examples/07_timing.py` 用 `LAYA_DEVICE=cpu` 跑一遍的完整输出（本机真实输出）：

```text
模型：convaiinnovations/laya
device=cpu  dtype=torch.float32  加载耗时 28.2 s
cfg：max_len=512 head_max_len=192

=== 同一次 forward 里塞 n 个问题 ===
问题数    总耗时          每问题耗时          输入 tokens
1      276 ms       276.1 ms       59
5      1044 ms      208.8 ms       295
10     2234 ms      223.4 ms       590
50     10141 ms     202.8 ms       2950

=== 一次 forward 里塞 100 个不同问题 ===
100 个问题：19048 ms，即 190.5 ms/问题，5900 tokens
返回的答案个数： 100

=== 同一批问题重复 20 次（看稳态延迟） ===
min=776 ms  p50=815 ms  mean=829 ms  max=981 ms
```

把这组数字和第 9.1 节的 GPU 数字放在一起，本机的真实倍数是：

```text
                GPU（GTX 1050）      CPU（本机）        倍数
单个问题            84 ms            276 ms          3.3x
50 个问题/次        2265 ms          10141 ms        4.5x
100 个问题/次       4751 ms          19048 ms        4.0x
每问题（批量）      45~47 ms         190~203 ms      4.3x
稳态 p50            220 ms（4 问）   815 ms（4 问）   3.7x
加载                64.6 s（英文）   28.2 s（英文）   CPU 反而更快
```

两点值得注意：

1. **本机这块 GPU 只快 3~4.5 倍，而不是官方说的 10~15 倍。** 官方那句话是对着 T4 级别的卡说的（`~200-500 ms rather than ~35 ms`），GTX 1050 的 FP32 吞吐和 T4 差着一个数量级，所以「GPU 一定比 CPU 快很多」在低端卡上并不成立——本机实测的 3~4 倍收益，值不值得为它单独维护一个 CUDA 环境，取决于你的吞吐需求。
2. **CPU 加载反而更快**（28.2 s vs 64.6 s）：GPU 路径上多了一步把权重搬到显存并建立 CUDA 上下文/内核的开销。这也是「每个进程在 GPU 上加载一次要 60 秒以上」那条经验（第 9.5 节）的由来。

另外，`examples/13_batch_labeling.py` 有一次因为 OOM 静默降级到 CPU 的运行，量到 **2.5 条/秒**（每条 3 个问题、约 205 tokens，含 JSON（反）序列化与排序开销），即约 9000 条/小时——这正是「批量任务不要在 4 GB 卡上并发塞多份权重」的代价。

### 9.4 显存：4 GB 卡上的三种活法

本机实测的显存账：

```text
单份英文 checkpoint（fp32）     allocated 1.69 GB  reserved 1.80 GB（load 后）
                               reserved 2.50 GB（第一次前向之后）
单份英文 checkpoint（fp16）     allocated 0.86 GB  reserved 1.90 GB   峰值 1.79 GB
三份全加载（fp32）              allocated 2.99 GB  reserved 4.16 GB  → OOM
```

三种活法：

```python
# 1) 只服务一份权重（最省事）
agent = laya.load("convaiinnovations/laya")                 # 1.7 GB，4 GB 卡够用

# 2) 转 fp16 再压一半（本机实测 14_gpu_fp16.py）
agent = laya.load("convaiinnovations/laya", device="cuda")
agent.model.half()                                          # 0.86 GB
# 本机输出：p50=154 ms，峰值显存 1.79 GB，答案与 fp32 一致

# 3) 三份都要，就别用同一个进程/同一张 4 GB 卡
router = Router(device="cpu")            # 或者拆到多进程/多卡，每份一个进程
router.preload(["english", "multilingual", "typed-decisions"])
```

关于 `agent.model.half()`：这是绕过 laya 公开 API 的直接操作，本机验证能跑、结果一致，但它不在官方文档里，升级版本时要重新验证。另外**不要**指望 `torch.set_default_dtype(torch.float16)` 省显存——本机验证过，transformers 是按 `encoder/config.json` 里的 dtype 建模型的，设完之后参数仍然是 `torch.float32`：

```text
  set_default_dtype 后参数 dtype = torch.float32
  [load 之后] allocated=1.63 GB reserved=1.74 GB
  half() 之后参数 dtype = torch.float16
  [half() 之后] allocated=0.86 GB reserved=1.85 GB
  [第一次前向之后] allocated=0.87 GB reserved=1.91 GB
```

还有一点：laya 在放不下时**不会崩**，而是打印一段带真实原因的 warning 然后退回 CPU：

```text
[laya] Warning: could not place the model on cuda, so it is running on CPU.
  Reason: CUDA out of memory. Tried to allocate 22.00 MiB. ...
  Inference will be roughly 10-15x slower (~200-500 ms rather than ~35 ms).
```

这段文案有一处会误导人：它默认建议「Blackwell / RTX 50 系请装 nightly cu128」。本机的失败原因根本不是新卡不支持，而是显存不够——排查时先看 `Reason:` 那一行，别照着后半段换 torch。

## 10. 部署：包成 HTTP 服务

把 Laya 包成一个决策服务只需要几十行：启动时 preload、请求时路由 + 一次前向。完整代码在 `examples/12_service.py`。

### 10.1 服务代码

```python
import os
import time
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from laya import Router

DEVICE = os.environ.get("LAYA_DEVICE") or None          # "cpu" / "cuda" / None(自动)
PORT = int(os.environ.get("LAYA_PORT", "8077"))

DEFAULT_QUESTIONS = {
    "department": {
        "type": "choice",
        "instructions": "Which department should handle this request?",
        "criteria": {
            "billing": "invoices, payments, refunds",
            "technical": "bugs, outages, system errors",
            "sales": "pricing, new contracts",
            "other": "everything else",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this request?",
        "criteria": ["not urgent", "soon", "critical deadline or blocking issue"],
    },
    "churn_risk": {"type": "noul", "instructions": "Does the user threaten to cancel or leave?"},
}


class DecideRequest(BaseModel):
    state: Any
    questions: Optional[Dict[str, Any]] = None
    model: Optional[str] = None          # english / multilingual / typed-decisions


app = FastAPI(title="laya-decide")
router: Router = None
STARTED_AT = time.time()


@app.on_event("startup")
def load_models():
    global router
    t0 = time.time()
    # 两步写法：Router(preload=["english", "multilingual"]) 会被当成 preload=True，
    # 把三个 checkpoint 全部加载（在 4 GB 显存的卡上会 OOM 并退回 CPU）。
    router = Router(device=DEVICE)
    router.preload(["english", "multilingual"])
    print("已 preload %s，耗时 %.1f s" % (router.loaded, time.time() - t0), flush=True)


@app.get("/health")
def health():
    return {"status": "ok", "loaded": router.loaded, "device": DEVICE or "auto",
            "uptime_s": round(time.time() - STARTED_AT, 1)}


@app.post("/decide")
def decide(req: DecideRequest):
    t0 = time.time()
    res = router.predict(req.state, req.questions or DEFAULT_QUESTIONS, model=req.model)
    res["latency_ms"] = round((time.time() - t0) * 1000, 1)
    return res


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
```

依赖：`fastapi` + `uvicorn`（laya 本身不带，要另外装）：

```bash
uv pip install --python /opt/ai-lab/laya/.venv/bin/python \
  --index-url https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn
# 本机装到：fastapi 0.141.1 / uvicorn 0.53.0 / starlette 1.6.0 / pydantic 2.13.5
```

### 10.2 启动与实测

启动（本机实测，CPU 模式，为了不和 GPU 上的其它测试抢显存）：

```bash
cd /opt/study-work/laya/examples
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
export LAYA_DEVICE=cpu
/opt/ai-lab/laya/.venv/bin/python -u 12_service.py
```

启动日志与健康检查（本机真实输出）：

```text
已 preload ['english', 'multilingual']，耗时 170.0 s
（首次启动的两份权重冷加载：CPU 上每份 25~90 秒不等，实测总计 170 秒；
  同一台机器加载一次之后缓存热，重新启动会明显更快）

$ curl -s localhost:8077/health
{"status":"ok","loaded":["english","multilingual"],"device":"cpu","uptime_s":170.6}
```

第一个请求（英文工单，本机真实输出，注意 `latency_ms` 含进程内首次前向的一次性开销）：

```text
$ curl -s -X POST localhost:8077/decide -H 'Content-Type: application/json' \
    -d '{"state":{"message":"We were charged twice for March and nobody replies. Please refund today or we cancel."}}'

{"model":"laya-rl-agent",
 "answers":{
   "department":{"type":"choice","choice":"billing",
     "probabilities":{"billing":0.9916,"technical":0.0028,"sales":0.0025,"other":0.003},
     "confidence":0.9585,"action":{"act_probability":1.0}},
   "urgency":{"type":"score","score":1.3651,
     "legend":{"0":"not urgent","1":"soon","2":"critical deadline or blocking issue"},
     "probabilities":{"0":0.1015,"1":0.432,"2":0.4665},"confidence":0.1349,
     "action":{"act_probability":1.0}},
   "churn_risk":{"type":"noul","noul":0.8385,"confidence":0.8385,"action":{"act_probability":1.0}}},
 "usage":{"input_tokens":180,"output_tokens":0},
 "routing":{"model":"english","repo":"convaiinnovations/laya","reason":"English Latin text",
   "detection":{"script":"latin","script_profile":{"latin":1.0},"language":"en",
     "is_english":true,"non_latin_fraction":0.0},"workflow":null},
 "latency_ms":7313.4}
```

第二个请求（德文，触发多语言路由；这一次已经热了）：

```text
$ curl -s -X POST localhost:8077/decide -H 'Content-Type: application/json' \
    -d '{"state":{"message":"Der Kunde wurde zweimal belastet, bitte erstatten Sie die Zahlung."}}'

{"model":"laya-rl-agent",
 "answers":{
   "department":{"type":"choice","choice":"billing",
     "probabilities":{"billing":0.9992,"technical":0.0003,"sales":0.0001,"other":0.0004},
     "confidence":0.9948,"action":{"act_probability":1.0}},
   "urgency":{"type":"score","score":1.8842,"probabilities":{"0":0.0033,"1":0.1092,"2":0.8875},
     "confidence":0.6664,"action":{"act_probability":1.0}},
   "churn_risk":{"type":"noul","noul":0.0284,"confidence":0.9716,"action":{"act_probability":1.0}}},
 "usage":{"input_tokens":171,"output_tokens":0},
 "routing":{"model":"multilingual","repo":"convaiinnovations/laya/multilingual",
   "reason":"Latin script but language looks like 'de', not English",
   "detection":{"script":"latin","script_profile":{"latin":1.0},"language":"de",
     "is_english":false,"non_latin_fraction":0.0},"workflow":null},
 "latency_ms":192.7}
```

第三个请求（自定义 questions + 显式指定模型，验证「调用方自带 schema」这条路）：

```text
$ curl -s -X POST localhost:8077/decide -H 'Content-Type: application/json' -d '{
    "state":{"body":"The API returns 502 on /v2/export since the last deploy."},
    "model":"english",
    "questions":{
      "bug":{"type":"noul","instructions":"Does this report a software defect?"},
      "area":{"type":"choice","instructions":"Which area?",
              "criteria":{"api":"API endpoints","ui":"web UI","other":"none of the above"}}}}'

{"model":"laya-rl-agent",
 "answers":{
   "bug":{"type":"noul","noul":0.8413,"confidence":0.8413,"action":{"act_probability":1.0}},
   "area":{"type":"choice","choice":"api","probabilities":{"api":0.9871,"ui":0.0063,"other":0.0066},
     "confidence":0.929,"action":{"act_probability":1.0}}},
 "usage":{"input_tokens":100,"output_tokens":0},
 "routing":{"model":"english","repo":"convaiinnovations/laya","reason":"explicit model='english'",
   "detection":null,"workflow":null},
 "latency_ms":448.5}
```

三组数字放在一起看很有价值：

```text
第一次请求 7313.4 ms   ← 进程内首次前向（CUDA/CPU 上下文与内核首次加载）＋ 首条真实流量
第二次请求  192.7 ms   ← 已热，且走的是 multilingual
第三次请求  448.5 ms   ← CPU、10 个选项 + 2 个问题、约 100 tokens
```

**结论：健康检查返回 ok 不代表可以直接接流量，第一次请求仍可能慢一个数量级。** 生产上要在启动流程里打一发真实问题做预热（上面的 `/health` 只暴露了 `loaded`，可以在它内部顺带做一次预热调用），或者用「启动后延迟接入负载均衡」的方式规避。

停服务时按 PID 停（**不要**用 `pkill -f "12_service.py 8077"` 这类带脚本名的模式，pattern 会匹配到 pkill 自己的命令行，把当前 shell 一起杀掉）：

```bash
ps -eo pid,args | grep -F '12_service.py' | grep -v grep | awk '{print $1}' | xargs -r kill
ss -lntp | grep 8077     # 确认端口已释放
```

### 10.3 生产注意事项

```text
1. preload 而不是懒加载：本机 preload 两份耗时 170 s（CPU 冷启），但之后每次请求都是几十~几百毫秒；
   懒加载在语言交替流量下每次都要重建模型（官方量到 7.4 s / 10.3 s）。
2. 常驻内存：英文 fp32 约 1.7 GB + 多语言约 1.3 GB，另外要考虑 Python 自身与 FastAPI 的开销。
   显存紧张的机器只 preload 一份，或者用第 9.4 节的 fp16 做法。
3. 并发：laya 的 forward 是同步阻塞的，`uvicorn` 单 worker 下请求会排队。
   提高并发有两条路——多 worker（每 worker 各自加载一份权重，内存/显存翻倍）
   或者自己加一层队列把请求攒成 batch（laya 内部已经支持一次前向多问题，
   攒成 multi-state batch 需要自己拼，官方没有暴露 batch API）。
4. 超时与熔断：单次决策在 CPU 上是几百毫秒量级、GPU 上几十毫秒，客户端超时可以设得比较紧（1~2 s），
   但要给首次请求留余量。
5. 观测：把 routing.model / routing.reason / latency_ms / confidence 全部记日志，并按模型分桶统计，
   否则多语言流量会把英文侧的指标带偏。
6. 版本固定：权重与 laya 版本都要固定（本文是 laya 0.3.4 + torch 2.14.0+cu126），
   升级 transformers 大版本后要重跑一遍回归——本机验证过 5.17.0 可用，但这是「当前可用」而非承诺。
```

### 10.4 外部调用（接入文档）

上面这套服务本机已经用 systemd 常驻在 `0.0.0.0:8077`，并且开了 `X-API-Key` 鉴权。如果你要把它接进自己的系统（Spring Boot 后端、Vue 前端、脚本、别的机器、手机），接口字段、鉴权、五种语言的客户端示例、局域网/Tailscale 接入、超时与容量参数、排错速查，都单独写在 [[Laya服务接入文档]] 里——那一篇是给「调用方」看的，本篇是给「理解模型的人」看的。

几个最容易踩的接入点先在这里提一句：

```text
1. 它在 HTTP 层只暴露两个端点：GET /health、POST /decide；没有版本前缀，没有 SSE，没有流式。
2. 响应里 usage.output_tokens 恒为 0 —— 它不生成自然语言，只给结构化判断。
3. 服务 health 返回 ok 不等于可以打流量：进程内首次前向实测要 5.4 秒，之后才回到 200~700 毫秒。
4. 客户端读超时给 60 秒（不是 5 秒）；connect 超时 3~5 秒就够。
5. 一个 choice 题的选项控制在 10 个以内：30 个选项时剩余题面预算已经是负数，77 个时每项只剩 4 token。
6. 门控别直接用 confidence 卡阈值：它是归一化熵不是正确率（官方 mean ECE 0.466）。
```

## 11. 批量打标

一次前向能并行回答「一条 state 上的多个问题」，但多条 state 之间是循环的（`system_one` 内部只把一批问题拼成一个 batch）。所以离线批量任务要自己写：分片、进度、断点续跑、汇总。`examples/13_batch_labeling.py` 是一份最小可用的生产者：

```text
输入：batch_input.jsonl（每条 {"id": ..., "message": ...}，脚本能自己用模板生成 120 条）
输出：batch_output.jsonl（每条结果一行，含 intent / confidence / urgency / needs_reply / 路由信息）
续跑：--resume 参数跳过已完成 id（读 output 里已有的 id 集合）
汇总：按 intent 统计条数与平均置信度，并把 confidence < 0.5 的挑出来送人工
```

本机真实运行（GPU，device=cuda，英文 checkpoint，120 条 × 3 个问题）：

```text
待处理 120 条
  已处理 20/120（8.57 s，2.3 条/秒，205 tokens/条）
  已处理 40/120（15.79 s，2.5 条/秒，208 tokens/条）
  已处理 60/120（23.00 s，2.6 条/秒，205 tokens/条）
  已处理 80/120（30.21 s，2.6 条/秒，205 tokens/条）
  已处理 100/120（37.43 s，2.7 条/秒，202 tokens/条）
  已处理 120/120（44.65 s，2.7 条/秒，202 tokens/条）
完成：120 条，用时 44.6 s，吞吐 2.7 条/秒

=== 结果分布 ===
  technical_help      41 条  平均置信度 0.880  高紧急 0 条
  other               27 条  平均置信度 0.416  高紧急 0 条
  cancellation        22 条  平均置信度 0.998  高紧急 0 条
  refund              20 条  平均置信度 1.000  高紧急 0 条
  information         10 条  平均置信度 0.408  高紧急 0 条
低置信度（<0.5）需要人工的：34 条
   t0000  How do I migrate data from Salesforce to your platfo  conf=0.432
   t0001  How do I migrate data from HubSpot to your platform?  conf=0.326
   t0006  What is the price difference between starter and ent  conf=0.459
   t0007  What is the price difference between pro and enterpr  conf=0.432
   t0008  How do I migrate data from Intercom to your platform  conf=0.303
```

三条实用结论：

```text
1. 吞吐：这块 4 GB 卡上 2.7 条/秒（每条 3 个问题、约 205 tokens）= 约 9700 条/小时。
   同机 CPU 上一次因 OOM 退化的运行量到 2.5 条/秒——注意 CPU 在这个批量场景下没有想象中慢，
   因为瓶颈是 Python 侧的逐条循环与拼接，不完全是算力。
2. 置信度分布直接指出了模型的能力边界：模板化的 "Please cancel our X plan" 拿到 0.998，
   而 "How do I migrate data from X" 只有 0.30~0.43——后者是信息类问题，
   预设的六类意图里本来就没有「how-to / 迁移咨询」这一类，模型只能往 information/other 上挤。
   看到这种分布就该回去改 criteria，而不是调阈值。
3. 断点续跑是必须的：GPU 任务中途 OOM、机器重启、你手动 Ctrl-C，都要能接着跑。
   脚本的做法是「输出文件已存在的 id 集合」作为已完成标记，一行一条 JSON、每条 flush。
```

## 12. 微调

### 12.1 为什么必须微调

官方在 typed-decisions 基准（400 条、2000 个决策、四个工作流）上量到（**官方数据**）：

| 模型 | accuracy | soft acc | Brier | ECE | score MAE |
|---|---|---|---|---|---|
| `laya-typed-decisions`（微调后） | **0.766** | 0.471 | **0.062** | 0.213 | **0.242** |
| `laya`（英文 base） | 0.362 | 0.332 | 0.316 | 0.175 | 0.694 |
| `laya-multilingual`（base） | 0.342 | 0.326 | 0.439 | 0.285 | 0.687 |
| TypeSafe Jev 1.13.0（第三方公布） | 0.727 | 0.580 | 0.148 | 0.144 | 0.391 |
| 教师自一致性上限 | 0.735 | | | | |
| 逐题多数类基线 | 0.461 | | | | |
| 随机猜 | 0.318 | | | | |

关键读法：**两个 base checkpoint 在 typed-decisions 上低于「多数类基线」**（0.362 / 0.342 vs 0.461），也就是说零样本时它们在这类任务上还不如「每题都答最常见的那个选项」。0.766 那个成绩来自在基准自己的训练集上微调过的 checkpoint。官方原话：把 Laya 当作「可以快速特化的底座」，而不是「开箱即用的决策引擎」。

### 12.2 微调流程

官方 notebook：`notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb`（Kaggle 免费 2×T4 就能跑）。它把整条链路都做好了：

```text
1. 构建数据集（你自己的领域数据，整理成 state + questions + 目标分布）
2. 用 RLCD 训练：奖励是严格 proper 的评分规则
   源码 laya.common.proper_reward = 对数分数 + 0.5 × 球面分数（+ 有序任务再减 RPS）
   —— 优化的是「概率是否与真实结果对齐」，不是「像不像人说的话」
3. 策略梯度是 GRPO 风格（同组样本内比较），支持多轮对话轨迹的 TD(λ) 目标
   （源码 laya.common.td_lambda_targets）
4. 按 (问题类型, 选项数) 分桶拟合校准温度，写回 rl_agent_config.json
5. 评估（accuracy / soft acc / Brier / ECE / score MAE 全套）
6. 推到 HuggingFace Hub
```

训练开销：2×T4 上约 3 万个问题、4 个 epoch，**4~5 小时**（官方数据）。数据量不大的领域任务（几千条）实际会更快。

### 12.3 微调能带来什么、不能带来什么

```text
能：把「接近随机」的零样本表现拉到可用水平（官方 0.362 -> 0.766），
    并把概率重新校准到可以拿阈值门控的程度（ECE 0.213 -> 拟合约 0.081/0.106 这个量级）。
不能：把 Laya 变成生成模型。它依然只会从你给的选项里选，多轮推理、写文案、解释理由是 LLM 的活。
    另外微调过的 checkpoint 只在你定义的 schema 上强，换一套 criteria 又要重新评估。
```

一条实践经验：froze 之前先跑一遍 `laya-typed-decisions` 这份已经微调过的 checkpoint 当参考系——如果你的 schema 恰好接近那四个工作流（客服、发票、安全事件、agent 轨迹），它已经能直接用，不必自己训。

## 13. 与 TypeSafe Jev、通用 LLM 的对比

| | TypeSafe Jev | Laya | 通用 LLM |
|---|---|---|---|
| 形态 | 托管 API | 自托管权重（Apache 2.0） | 托管或自托管 |
| 权重 | 闭源 | 开源，421M / 322M | 通常闭源或巨大 |
| 计费 | $0.042 / 1M 输入 token | $0（自付硬件） | 按 token |
| 单问题延迟 | 第三方实测 p50 236~276 ms | 本机 84 ms；官方 T4 39.5 ms | 秒级 |
| 语言覆盖 | 未公布基准 | 官方 51 语言里 45 可用（路由后） | 强 |
| 高基数选项（> 20） | 支持到 255 选项，Banking77 0.870 | 默认配置下只有 0.425，要抬 head_max_len | 看 prompt 设计 |
| 校准 | 原始 ECE 0.144 | 拟合后 0.081（官方），原始偏高 | 通常没有可用置信度 |
| 数据出网 | 必须出网 | 完全本地 | 看出网 |

官方 README 里那张「Laya（路由）vs Jev」表的关键行（**官方与第三方公布数据，非本机测量**）：

```text
typed-decisions 2000 个决策   Jev 0.727    Laya 0.766
AG News（4 类）               Jev 0.910    Laya 0.950
DAIR Emotion（6 类）          Jev 0.480    Laya 0.595
Banking77（> 20 选项）        Jev 0.870    Laya 0.425   ← Jev 明显更强
p50 单问题延迟                Jev 236-276 ms  Laya 32.8 ms
```

选型建议（结合本机实测）：

```text
1. 要数据不出内网、要零调用成本、要毫秒级批量判定 → Laya 自托管。
2. 选项特别多（50+）、或者不想管模型运维 → Jev 这类托管 API 更合适。
3. 需要「解释理由」「多轮追问」「生成一段话」 → 谁都不合适，用 LLM；
   实践中是「Laya 做路由/守门/打分 → 需要推理的转发给 LLM」的两段式。
4. 已经在用 Jev 且效果够用 → 不必因为「有开源版」就迁移；
   迁移动机通常是成本、延迟、合规（数据不出网）这三条里的一条。
```

## 14. 常见问题与排查

### 坑 1：`torch.cuda.is_available()` 是 True，但一跑就 `no kernel image is available`

**结论**：老显卡（sm_50~sm_70）必须换 cu126 构建的 torch，cu130 里没有这些架构的内核。

**原因**：PyPI 上的 torch 默认是 CUDA 13 构建，只编译 sm_75 及以上；`is_available()` 只检查驱动与设备可见性，不检查内核是否匹配，所以它照样返回 True，laya 也会把 device 选成 cuda。

**解法**：

```bash
uv pip install --python /opt/ai-lab/laya/.venv/bin/python \
  --index https://download.pytorch.org/whl/cu126 \
  --default-index https://pypi.tuna.tsinghua.edu.cn/simple \
  'torch==2.14.0+cu126'
```

复验用 `examples/09_pitfall_torch_cu130.py`：它会打印 torch 的架构列表、显卡算力，并真的跑一个 512×512 矩阵乘法来判断。

### 坑 2：`Router(preload=["english"])` 会加载全部三个 checkpoint

**结论**：`Router.__init__` 里 `if preload:` 只判真假，传列表等于 `preload=True`，三份权重全建；4 GB 显存的卡直接 OOM 并退回 CPU。

**原因**：构造函数没有把 `preload` 参数转交给 `self.preload(names)`，而是无参调用。

**解法**：两步写 `router = Router(); router.preload(["english"])`。

### 坑 3：模型下载中途 401（Xet CAS 端点）

**结论**：`HF_HUB_DISABLE_XET=1`，或者卸载 `hf-xet`。

**原因**：huggingface_hub 1.x 默认启用 Xet 传输，hf-mirror 不支持它的 CAS 重构建接口：

```text
RuntimeError: Task error: File reconstruction error: CAS Client Error: Request error:
HTTP status client error (401 Unauthorized), domain: https://cas-server.xethub.hf.cloud/...
```

**解法**：设环境变量后再下载；已经下了一部分的字节会复用，不会白下。

### 坑 4：以为用置信度能兜住「模型看不懂这门语言」

**结论**：兜不住。英文 checkpoint 在高棉语上准确率 0.000、置信度 0.952（官方数据）；本机也复现了错误样本 confidence=0.999 的情况。

**原因**：confidence 是归一化熵，衡量分布形状，不衡量正确性。

**解法**：路由决定必须做在前向之前（用 `laya.lang` 的检测，微秒级），或者用第 6.4 节的「在带标签数据上量阈值表」，不要凭感觉设 0.85。

### 坑 5：高基数选择题悄悄变差

**结论**：选项超过 20 个就要显式抬 `head_max_len`（官方建议 512）或改成两级选择。

**原因**：选项共享 head 预算，50+ 选项时每个选项只剩下限 4 个 token，`billing: invoices, payments, refunds...` 只剩 `billing: invo`。

**解法**：见第 7 章；注意抬预算会让延迟显著上升（本机 77 选项从 ~150 ms 到 2368 ms），两级选择通常更划算。

### 坑 6：拿第一次前向的耗时做容量规划

**结论**：进程内第一次 `predict` 有 1~30 秒的一次性开销（CUDA 上下文 + 内核首次加载），必须预热。

**原因**：CUDA 上下文初始化与内核加载不在模型加载阶段完成。

**解法**：服务启动后跑一次假请求再对外提供服务（本文的 `/health` 也顺带承担这个职责）；压测报告里注明是否预热。

### 坑 7：把 `output_tokens` 或 `action.act_probability` 当成有意义的信号

**结论**：`usage.output_tokens` 恒为 0（它不生成文本）；`action.act_probability` 本机实测恒在 1.0 附近，官方 README 没有展开说明，别拿它做决策。

**原因**：前者是非自回归设计的体现，后者是另一个头（act_head）的输出，缺少公开文档与校准保证。

**解法**：只依赖 `choice` / `score` / `noul` / `probabilities` / `confidence` 这五个字段。

## 应用场景实战

### 场景一：客服工单自动分诊（单次调用完成四个判定）

需求：工单进来后自动判断「哪个部门、多紧急、是否要求退款、是否会流失」，高置信度自动路由，低置信度进人工队列。

```python
import os
from laya import Router, triage_questions

router = Router(device=os.environ.get("LAYA_DEVICE") or None)
router.preload(["english", "multilingual"])       # 英文工单 + 其他语言工单

DEPARTMENTS = {"refund": "billing-refund", "billing_question": "billing",
               "technical_help": "engineering", "information": "support",
               "cancellation": "retention", "other": "triage"}

def triage(ticket: dict, auto_conf: float = 0.85, churn_cut: float = 0.6):
    res = router.predict({"message": ticket["text"]}, triage_questions())
    a = res["answers"]
    intent, conf = a["intent"]["choice"], a["intent"]["confidence"]
    churn = a["churn_risk"]["noul"]
    need_human = conf < auto_conf or churn >= churn_cut or a["frustration"]["score"] >= 2.5
    return {
        "ticket_id": ticket["id"],
        "queue": DEPARTMENTS[intent],
        "urgent": a["is_urgent"]["noul"] >= 0.7,
        "refund": a["refund_requested"]["noul"] >= 0.7,
        "churn_risk": churn,
        "escalate": need_human,
        "model": res["routing"]["model"],          # 线上排查用：走的是哪份权重、为什么
        "reason": res["routing"]["reason"],
        "confidence": conf,
    }
```

本机真实输出（单个工单，device=cuda，见 `examples/04_presets_triage.py`）：

```text
--- 工单 1 ---
  文本        : I have been charged twice this month and nobody is answering my emails. ...
  intent      : billing_question ... confidence 0.4979
  is_urgent   : 0.7894 (confidence 0.7894)
  frustration : 1.9049 / 3.0 {'0': 0.0208, '1': 0.1254, '2': 0.782, '3': 0.0718}
  refund?     : 0.8569
  churn_risk  : 0.8559

=== 按预设结论做分支（confidence 门控） ===
  判定结果： 转人工（intent confidence=0.50, churn=0.86）
```

设计要点：

```text
1. 四个判定一次前向（本机 220 ms 稳态），不要拆成四次调用。
2. 「转人工」的触发条件是三条 or：意图不确定、流失风险高、情绪激动。
   把模型输出当输入、把阈值当配置，阈值换版本时不用动代码。
3. 一定要把 routing.model / routing.reason 落进日志：多语言流量下，
   同样的阈值在 english 与 multilingual 上的含义不同（第 6.4 节）。
```

### 场景二：邮件安全网关（清洗 → 分类 → 威胁判定）

需求：入站邮件先去掉引用/签名/免责声明，再判是否是钓鱼/垃圾，再决定投递队列。

```python
from laya import Router, clean_email_body, email_questions

router = Router()
router.preload(["english"])

def screen(subject: str, body: str, sender: str):
    cleaned = clean_email_body(body)                       # 506 字符 -> 104 字符
    state = {"subject": subject, "body": cleaned, "from": sender}
    a = router.predict(state, email_questions())["answers"]
    if a["is_phishing"]["noul"] >= 0.9 and a["is_spam"]["noul"] >= 0.5:
        return {"action": "quarantine", "notify": "security-team",
                "p_phishing": a["is_phishing"]["noul"]}
    if a["is_spam"]["noul"] >= 0.9:
        return {"action": "spam-folder", "p_spam": a["is_spam"]["noul"]}
    return {"action": "deliver", "queue": a["category"]["choice"],
            "urgency": a["urgency"]["score"], "needs_reply": a["needs_reply"]["noul"]}
```

本机真实输出（`examples/05_email_triage.py`）：

```text
  原文 506 字符 -> 清洗后 104 字符
  引用段被丢弃： True    签名被丢弃： True    免责声明被丢弃： True

--- 重复扣费（正常工单） ---   category: billing   is_phishing: 0.0135   is_spam: 0.0
--- 钓鱼邮件 ---               category: security  is_phishing: 0.834    is_spam: 0.8516
--- 推广邮件 ---               category: security  is_phishing: 0.9999   is_spam: 1.0
```

设计要点（含本机踩到的真实失败）：

```text
1. 清洗是免费的收益：省 token、去噪声，还把「引用里的旧邮件内容」这种干扰源删掉。
2. 上面那个 AND 条件（is_phishing >= 0.9 且 is_spam >= 0.5）不是随手写的：
   本机实测普通推广邮件也被判成 phishing=0.9999，单靠 phishing 阈值会误杀大量营销邮件。
   真实上线的做法是先用 is_spam 分流，或者用自己业务的邮件微调后再定阈值。
3. sender 域名、SPF/DKIM 这类结构化信号应放进 state（键名会进序列），
   让模型把「域名可疑」和「话术可疑」结合起来判——纯文本判定必然会踩上面的坑。
```

### 场景三：给 LLM 应用加守门（便宜的第一道筛子）

需求：用户输入进 LLM 之前先用本地模型判越狱/注入/敏感数据/危害等级，把明显恶意的拦掉、把可疑的降级处理，剩下的才花钱调大模型。

```python
from laya import Router, guard_questions

router = Router()
router.preload(["english"])

def guard(prompt: str):
    a = router.predict({"prompt": prompt}, guard_questions())["answers"]
    if a["jailbreak"]["noul"] >= 0.8 or a["prompt_injection"]["noul"] >= 0.8:
        return "block", "越狱/注入"
    if a["sensitive_data"]["noul"] >= 0.8:
        return "redact", "含敏感数据，先脱敏再送模型"
    if a["harm_severity"]["score"] >= 2.5:
        return "review", "人工审核"
    return "allow", None
```

本机真实输出（`examples/06_guardrail.py`）：

```text
场景         jailbreak injection sensitive harm   topic
正常提问       0.000     0.049     0.069     1.27   coding
直接越狱       1.000     1.000     0.031     2.20   security_testing
间接注入       1.000     1.000     0.447     1.66   security_testing
含凭证        0.215     0.143     0.866     0.52   security_testing
有害请求       0.050     0.150     0.064     1.22   coding

正常提问 -> 放行      直接越狱 -> 拦截：越狱      间接注入 -> 拦截：越狱
含凭证   -> 脱敏后转发   有害请求 -> 放行     ← 这一条是漏的
```

设计要点：

```text
1. 守门模型的定位是「廉价筛子」，不是最终防线：越狱/注入识别很干净（1.000），
   但「有害请求」这种需要世界知识的判断它漏了（0.050）。拦下来的部分省了 LLM 的钱，
   漏掉的部分必须靠后面的大模型/规则库兜住。
2. 单次调用 4~5 个问题、440~534 ms（稳态）——比一次 LLM 调用便宜一到两个数量级。
3. 「含凭证」不要拦，要脱敏后转发；把「拦」和「脱敏」分成两个动作是这类系统的关键设计。
```

### 场景四：多语言批量打标（用路由统一处理 100+ 语言）

需求：把从各国渠道收集的用户反馈统一打标，中文、印地语、德语、英语混合；不做出网。

```python
from laya import Router

router = Router(device="cuda")
router.preload(["english", "multilingual"])        # 两份常驻，路由开销只剩检测

def label(items):
    out = []
    for it in items:
        res = router.predict({"message": it["text"]}, QUESTIONS)
        out.append({"id": it["id"],
                    "label": res["answers"]["intent"]["choice"],
                    "conf": res["answers"]["intent"]["confidence"],
                    "model": res["routing"]["model"]})   # english / multilingual
    return out
```

本机真实输出（`examples/03_router.py`，同一个问题集，四种语言的工单）：

```text
  [英文] 11449 ms   department = billing {'billing': 0.9659, 'technical': 0.0161, 'other': 0.0179}
  [德文] 66 ms      department = billing {'billing': 0.9603, ...}      routing=multilingual
  [印地文] 68 ms    department = billing {'billing': 0.9968, ...}      routing=multilingual
  [中文] 62 ms      department = billing {'billing': 0.9993, ...}      routing=multilingual
```

（第一次 11449 ms 是多语言 checkpoint 的首次前向开销，之后稳定在 62~68 ms。）

设计要点：

```text
1. 两份权重都 preload，别让 Router 懒加载去接混合语言流量（每次切换要重建模型，官方量到 7.4~10.3 s）。
2. 逐条循环时把 routing.model 记下来，按模型分开统计阈值与准确率——
   多语言版和英文版的概率口径不同，混在一起算指标会得出错结论。
3. 本机验证过中文/韩文/泰文/印地文都能被正确路由到 multilingual（汉字占 100% 时 reason 会写明
   "non-Latin script (han, 100% of letters)"）；但路由对不等于答对，
   中文这种语言官方没有给出逐语言基准，上线前要用自己的数据量一遍。
```

## 最佳实践与踩坑记录

### 最佳实践

1. **一个问题一次问完**：把同一段 state 上所有判定放进一个 dict 一次调用，本机摊薄到 45 ms/问题；拆成多次调用是纯浪费。
2. **服务启动必须预热**：进程内第一次前向有 1~30 秒一次性开销，启动阶段打一发假请求。
3. **preload 常驻，不要懒加载接混合语言流量**：冷加载 25~90 秒，语言切换时的重建是 7~10 秒量级。
4. **只用公开语义的五个字段**（choice / score / noul / probabilities / confidence），别依赖 `action.act_probability`。
5. **阈值按 (题型, 选项数) 分桶、在自己的带标签数据上量**，不要照抄 0.85，也不要在小样本上拟合温度。
6. **routing.model 与 routing.reason 必须进日志**：多语言场景排查成本会低一个数量级。
7. **state 要洗**：邮件用 `clean_email_body`，其他场景自己把无关内容剪掉；键名会进序列，起名要有信息量。
8. **选项描述要互相可区分**，宁可写长一点（4 个选项时每项有 44 token 可用），也别写「A 情况 / 类似 A 的情况」。
9. **超过 20 个选项就改成两级选择**，比抬 head_max_len 便宜且稳。
10. **把 Laya 当底座而不是成品**：零样本在它没训过的 schema 上可能低于多数类基线，领域任务预留微调预算（2×T4 约 4~5 小时）。
11. **离线部署把权重落成自带目录**（`snapshot_download(local_dir=...)`），之后 `laya.load("/path/to/dir")` 完全不碰网络。
12. **批量任务必须可续跑**：逐条 flush，用已完成 id 集合做断点标记。

### 踩坑记录

```
坑 1：cu130 的 torch 在老卡上「看着有 GPU 其实用不了」
结论：sm_50~sm_70 的卡必须装 cu126 构建，否则所有算子报 no kernel image is available。
原因：is_available() 只检查驱动与可见性，不检查内核架构匹配；CUDA 13 构建只编译 sm_75+。
解法：uv pip install --index https://download.pytorch.org/whl/cu126 'torch==2.14.0+cu126'，
      用 examples/09_pitfall_torch_cu130.py 跑一次矩阵乘法复验。

坑 2：Router(preload=["english"]) 加载了全部三份权重
结论：构造函数只判断 preload 的真假，传列表等于全加载；4 GB 卡 OOM 后退回 CPU。
原因：__init__ 里 `if preload: self.preload()` 没把名单传下去。
解法：两步写法 Router() + router.preload(["english"])，并用 router.loaded 确认。

坑 3：hf-mirror 下载中途 401（CAS 端点）
结论：必须 HF_HUB_DISABLE_XET=1，或在 venv 里卸载 hf-xet。
原因：huggingface_hub 1.x 默认走 Xet 传输，镜像不支持其 CAS 重构建接口。
解法：两个环境变量一起设：HF_ENDPOINT=https://hf-mirror.com、HF_HUB_DISABLE_XET=1。

坑 4：allow_patterns 里的 "*" 会跨目录
结论："*.safetensors" 会把 multilingual/ 和 typed-decisions/ 的权重一起下下来。
原因：huggingface_hub 用 fnmatch 匹配完整路径，"*" 不过滤 "/"。
解法：写精确模式（model.safetensors、tokenizer/*、encoder/*），本机实测能把单份控制在 0.85 GB。

坑 5：小样本上拟合温度，ECE 反而更差
结论：24 条训练集上选出 T=3.00，测试集 ECE 从 0.1605 变成 0.3087。
原因：温度是单参数但样本太少仍然过拟合；官方是在几千条 held-out 数据上按桶拟合。
解法：样本不够就别拟合，直接量阈值表（放行数/精确率/人工数）来定门控。

坑 6：以为 confidence 能兜住「模型读不懂这门语言」
结论：英文 checkpoint 在高棉语上 0.000 准确率时置信度 0.952（官方数据）；
      本机也出现错误样本 confidence=0.999。
原因：confidence 是归一化熵，衡量分布形状而非正确性。
解法：前向前做脚本/语言路由（laya.lang，微秒级），并且阈值分模型分桶量。

坑 7：高基数选项静默变差
结论：50+ 选项时每个选项只剩 4 个 token（下限），billing: invoices... 只剩 billing: invo。
原因：选项共享 head_max_len 预算，超出时统一截断。
解法：抬 head_max_len（官方建议 512）或改两级选择；本机 77 选项抬到 head_max_len=1024 后
      每次调用 2368 ms，两级选择只需几十毫秒。

坑 8：长 state 的尾部被静默丢弃
结论：11999 字符的 state 只送进去 512 tokens，truncate_left=False → 保留开头、砍掉结尾。
原因：build_sequence 按 max_len 截断，默认从右边砍。
解法：把关键句前置，或在进入模型前自己把 state 剪短（邮件场景用 clean_email_body）。

坑 9：用第一次前向的耗时做容量规划
结论：首次 1~30 秒，稳态 84~220 ms；不预热就上线，第一个用户要多等十几秒。
原因：CUDA 上下文初始化与内核首次加载发生在第一次前向。
解法：启动阶段预热（本机 /health 之外再打一发真实问题）；压测报告注明是否预热。

坑 10：CPU 场景误判「慢十几倍」
结论：本机 CPU 单问题 276 ms、4 问题稳态 815 ms，相对这块老卡只有 3~4 倍差距；
      批量打标 CPU 2.5 条/秒 vs GPU 2.7 条/秒，几乎持平（瓶颈在 Python 侧循环）。
原因：官方「10-15x slower」是对现代 GPU 说的；批量场景的瓶颈不完全是算力。
解法：小批量/低 QPS 场景直接用 CPU 更省事（也免掉显存 OOM 风险），
      高 QPS 在线判定才需要 GPU。

坑 11：把一个「长选项集」直接塞给 choice
结论：官方自己也承认 Banking77（77 标签）上 0.425 对 Jev 0.870，这是架构层面的 token 预算约束。
原因：见坑 7。
解法：> 20 选项就设计成分层选择，或者换用支持长选项的托管 API。

坑 12：忽略 laya 的 OOM 兜底警告
结论：显存不够时 laya 不报错，而是打印 warning 退回 CPU 继续跑，结果照出但慢十几倍。
原因：Agent 里对 .to(device) 与 forward 都做了 RuntimeError/OOM 捕获与 CPU 降级。
解法：把启动日志里的 "[laya] Warning: could not place the model on cuda" 当成致命错误处理
      （监控里 grep 这条），否则线上会静默降速；排查时先看 Reason: 那一行，
      不要照抄文案后半段「装 nightly cu128」的建议（那针对的是 Blackwell 新卡）。
```

## 相关文档

- [[Laya服务接入文档]] — 把本教程里训练/调通的模型接进自己的系统：HTTP 接口契约、鉴权、五种语言客户端、局域网/Tailscale 接入、超时与容量、systemd 运维与排错速查

- [[TypeSafe-Jev完整教程]] — 同一时期整理的托管决策模型教程（System One 决策模型的另一种形态：闭源 API），两者的基准对比见本文第 13 章
- [[algorithm-engineer/README]] — 算法工程师知识库总入口，模型推理/部署相关章节与本篇互补
- [[16.2-模型服务]] — 自托管模型服务的通用部署方式（批处理、显存、并发），与本文第 9、10 章对照看
- [[16.3-推理优化]] — 推理延迟与吞吐优化（量化、批处理、KV cache），对照本文第 9 章的实测数字看
- [[Docker完整教程]] — 把第 10 章的 FastAPI 服务容器化的基础操作（镜像、网络、compose）
- [[10.2-systemd]] — 把第 10 章的服务做成 systemd 常驻单元的规范做法（unit 文件、日志、自启）
