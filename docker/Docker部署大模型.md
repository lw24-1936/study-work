---
title: 通过 Docker 部署大模型：从 Ollama 到 vLLM 生产推理
created: 2026-09-16
updated: 2026-09-16
type: integration
tags: [docker, 大模型, llm, vllm, ollama, llama-cpp, gpu, 推理, 量化, 部署]
---

# 通过 Docker 部署大模型：从 Ollama 到 vLLM 生产推理

整理日期：2026-09-16

> 状态：已完成

本文讲清楚一件事：如何用 Docker 把大语言模型（LLM）跑起来并提供服务，覆盖「本地体验 → 单机生产推理 → 多 GPU 高吞吐」的完整路径。部署方案从简单到生产依次是 Ollama（体验最快）→ llama.cpp / llama-server（低显存、GGUF 量化）→ vLLM（生产高吞吐、OpenAI 兼容 API）→ TGI（HuggingFace 生态）。所有命令都来自真实部署场景，关键点已在本机核对环境。

## 目录

- [1. 大模型部署全景与选型](#1-大模型部署全景与选型)
- [2. GPU 环境准备：nvidia-container-toolkit](#2-gpu-环境准备nvidia-container-toolkit)
- [3. Ollama：一键起一个本地大模型](#3-ollama一键起一个本地大模型)
- [4. llama.cpp / llama-server：GGUF 与低显存推理](#4-llama-cpp--llama-servergguf-与低显存推理)
- [5. vLLM：生产级高吞吐推理](#5-vllm生产级高吞吐推理)
- [6. HuggingFace TGI](#6-huggingface-tgi)
- [7. 推理前端：Open WebUI](#7-推理前端open-webui)
- [8. 模型缓存与数据卷](#8-模型缓存与数据卷)
- [9. 量化：GGUF / AWQ / GPTQ / FP8](#9-量化gguf--awq--gptq--fp8)
- [10. 多 GPU 与张量并行](#10-多-gpu-与张量并行)
- [11. 显存规划与性能调优](#11-显存规划与性能调优)
- [12. OpenAI 兼容 API 与客户端接入](#12-openai-兼容-api-与客户端接入)
- [13. 生产运行要点](#13-生产运行要点)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)
- [相关文档](#相关文档)

## 1. 大模型部署全景与选型

大模型部署的本质是「把权重加载进显存/内存，接收请求，跑前向推理」。Docker 在这里解决的是「运行环境一致性」问题：CUDA 版本、Python 依赖、推理框架版本、编译好的算子库（如 FlashAttention、量化内核）都是出了名的难装，用官方镜像能一键规避「在我机器上编译不过」的坑。

四条路线，按「上手成本从低到高、生产性能从低到高」排列：

| 方案 | 定位 | 模型格式 | 显存需求 | 吞吐 | 上手成本 |
|---|---|---|---|---|---|
| Ollama | 本地体验、个人/小团队 | GGUF | 低（可 CPU） | 低 | 最低 |
| llama.cpp / llama-server | 低显存、边缘、CPU+GPU 混合 | GGUF | 极低 | 中 | 低 |
| vLLM | 生产高吞吐推理服务 | HF 权重 + AWQ/GPTQ/FP8 | 较高 | 最高 | 中 |
| TGI | HuggingFace 生态推理 | HF 权重 | 较高 | 高 | 中 |

选型原则：

- 只想在自己机器上跑个模型聊天、跑通流程 → Ollama
- 显存小（≤ 8GB）、要跑量化模型、或 CPU 也要能用 → llama.cpp / llama-server
- 线上服务、要高并发高吞吐、要标准 OpenAI 接口 → vLLM
- 团队已深度绑定 HuggingFace 生态 → TGI

本机环境说明（下面所有结论都在此环境核对过）：

```text
Docker Engine 29.5.2 / Compose v5.1.4
GPU：NVIDIA GeForce GTX 1050（4GB 显存，Pascal 架构，计算能力 6.1）
驱动 580.173.02（CUDA 12.13 支持），未安装 nvidia-container-toolkit
内存 19GiB / 磁盘空闲 786GB
```

注意：GTX 1050 是 Pascal 架构（计算能力 6.1），显存仅 4GB。它只能跑小体量 GGUF 量化模型（1B~3B，配合 CPU 卸载），**跑不了 vLLM**（vLLM 要求计算能力 ≥ 7.0，Volta 起步）。下面的 vLLM/TGI 章节是给有合适 GPU（A10/A100/4090 等）的生产环境准备的，写清门槛不误导。

## 2. GPU 环境准备：nvidia-container-toolkit

容器默认看不到宿主的 GPU。要让容器用 GPU，需要三步：宿主装 NVIDIA 驱动 → 装 nvidia-container-toolkit → Docker 支持 `--gpus` 参数。

第一步：确认宿主驱动正常：

```bash
nvidia-smi
# 能看到 GPU 列表和 Driver Version 即正常
```

第二步：安装 nvidia-container-toolkit（Ubuntu/Debian，本机未装、下面为官方标准流程）：

```bash
# 添加官方 apt 源
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 让 Docker 识别 nvidia runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

第三步：验证 GPU 能进容器：

```bash
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
# 输出里能看到宿主 GPU 即成功
```

关键点：

- `--gpus all`：把宿主全部 GPU 暴露给容器；`--gpus '"device=0,1"'` 只暴露指定卡
- nvidia-container-toolkit 的核心是把 NVIDIA 驱动、CUDA 库、设备文件通过 runtime 注入容器，容器内不需要自己装驱动
- 检查 Docker 是否已支持：`docker info` 里 Runtimes 应出现 `nvidia`。本机 `docker info` 只有 `runc`，即未装 toolkit，这也是 GTX 1050 上暂时跑不了 GPU 推理的直接原因

CUDA 版本匹配提示：容器内镜像带的 CUDA 版本必须 ≤ 宿主驱动支持的 CUDA 版本。宿主驱动 580.173.02 支持到 CUDA 13.0，可以跑任何 ≤ 13.0 的 CUDA 镜像。`nvidia/cuda` 镜像 tag 形如 `12.4.0-cudnn8-devel-ubuntu22.04`，选 `runtime`/`base`（不带 cudnn/devel）体积更小，推理够用。

## 3. Ollama：一键起一个本地大模型

Ollama 把「下载模型、量化、加载、提供 API」全打包了，是最快的上手方式。官方镜像 `ollama/ollama`，模型存在容器内 `/root/.ollama`。

CPU 版（无 GPU 也能跑，慢但可用）：

```bash
docker run -d \
  --name ollama \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  ollama/ollama
```

GPU 版（需要第 2 章装好 toolkit）：

```bash
docker run -d \
  --name ollama \
  --gpus all \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  ollama/ollama
```

拉模型并对话：

```bash
# 拉取一个模型（首次会自动下载权重，小模型几百 MB）
docker exec -it ollama ollama pull qwen2.5:1.5b

# 交互式对话
docker exec -it ollama ollama run qwen2.5:1.5b

# 查看已下载的模型
docker exec -it ollama ollama list
```

API 调用（Ollama 同时提供原生 API 和 OpenAI 兼容 API）：

```bash
# 原生 API
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:1.5b",
  "prompt": "用一句话解释什么是容器",
  "stream": false
}'

# OpenAI 兼容 API
curl http://localhost:11434/v1/chat/completions -d '{
  "model": "qwen2.5:1.5b",
  "messages": [{"role": "user", "content": "你好"}]
}'
```

常用环境变量：

| 变量 | 作用 |
|---|---|
| OLLAMA_HOST | 监听地址（默认 127.0.0.1:11434，服务化要改 0.0.0.0） |
| OLLAMA_MODELS | 模型存储目录（默认 /root/.ollama/models） |
| OLLAMA_KEEP_ALIVE | 模型驻留显存时长（如 5m、-1 表示常驻） |
| OLLAMA_NUM_PARALLEL | 并发请求数 |
| OLLAMA_MAX_LOADED_MODELS | 同时加载几个模型 |

模型命名规律：`qwen2.5:1.5b` 的 `:1.5b` 是 tag，不同的 tag 对应不同参数量和量化等级（如 `qwen2.5:7b`、`qwen2.5:7b-instruct-q4_K_M`）。`ollama pull` 默认拉 tag 指向的推荐版本，显存小就选带 `q4` 的小 tag。

## 4. llama.cpp / llama-server：GGUF 与低显存推理

llama.cpp 是 C++ 写的推理引擎，主打「用 GGUF 量化模型在低配硬件（甚至纯 CPU）上跑 LLM」。它提供了 `llama-server`（内置 OpenAI 兼容 HTTP 服务），官方镜像带 CUDA 变体。

GGUF 是 llama.cpp 生态的模型格式，把量化后的权重打包成单文件，Q4/Q5/Q6/Q8 代表不同量化精度（见第 9 章）。

纯 CPU 版（任何机器都能跑）：

```bash
mkdir -p models
# 先下载一个 GGUF 模型（以 Qwen2.5-1.5B-Instruct 的 Q4_K_M 为例）
# 模型下载见第 8 章，这里假设已放到 ./models/ 下

docker run -d \
  --name llama-server \
  -v "$(pwd)/models:/models" \
  -p 8080:8080 \
  ghcr.io/ggml-org/llama.cpp:server \
  -m /models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 --port 8080
```

GPU 版（CUDA 镜像，`-ngl` 指定卸载到 GPU 的层数）：

```bash
docker run -d \
  --name llama-server \
  --gpus all \
  -v "$(pwd)/models:/models" \
  -p 8080:8080 \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -m /models/qwen2.5-7b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 --port 8080 \
  -ngl 99 -c 4096
```

常用参数：

- `-m`：模型文件路径
- `-ngl N`：把前 N 层放 GPU（99 = 全部放 GPU；显存不够就减层，剩余层走 CPU）
- `-c`：上下文长度（KV cache 大小，越长越吃内存）
- `--host` / `--port`：监听地址
- `--api-key`：给 OpenAI 兼容接口加鉴权

调用（OpenAI 兼容）：

```bash
curl http://localhost:8080/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "qwen",
  "messages": [{"role": "user", "content": "你好"}]
}'
```

llama.cpp 的定位：显存 4~8GB、要跑 7B~13B 量化模型、CPU 和 GPU 混合推理、边缘设备。GTX 1050（4GB）跑 7B Q4 模型正好是典型场景——部分层放 GPU、剩余走 CPU，速度慢但能跑起来。

## 5. vLLM：生产级高吞吐推理

vLLM 是当前最主流的开源生产推理引擎，核心是 PagedAttention（把 KV cache 分页管理，避免显存碎片）和连续批处理（continuous batching），吞吐比朴素实现高一个量级。官方镜像 `vllm/vllm-openai`，开箱就是 OpenAI 兼容 API。

硬门槛：vLLM 依赖较新的 GPU 架构，要求计算能力 ≥ 7.0（Volta 及以上），GTX 10 系（Pascal 6.1）不支持。生产一般用 A10/A100/H100/L40S 或 RTX 3090/4090。

单卡启动：

```bash
docker run -d \
  --runtime nvidia --gpus all \
  --ipc=host \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  -e HF_TOKEN=hf_xxx \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-7B-Instruct \
  --served-model-name qwen2.5-7b \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192
```

关键参数：

- `--model`：模型名（HF 仓库名，首次会自动下载到 HF cache）或本地路径
- `--served-model-name`：对外暴露的模型名（客户端调用时用这个名字）
- `--gpu-memory-utilization`：显存使用比例（默认 0.9，留 10% 给 KV cache 之外的碎片）
- `--max-model-len`：最大上下文长度（决定 KV cache 显存占用，越大越吃显存）
- `--tensor-parallel-size`：张量并行数（多卡时用，见第 10 章）
- `--quantization`：量化方式（awq/gptq/fp8，见第 9 章）

两个必须注意的挂载/参数：

- `--ipc=host`：vLLM 多进程间用共享内存通信，容器默认 64MB shared memory 不够，会报 `Bus error` 或卡死。要么 `--ipc=host`，要么 `--shm-size=1g`
- `-v ~/.cache/huggingface:/root/.cache/huggingface`：挂 HF 缓存，避免每次重启重新下载模型

调用（标准 OpenAI 接口，用 OpenAI SDK 直接指 base_url 即可）：

```bash
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "qwen2.5-7b",
  "messages": [{"role": "user", "content": "你好"}]
}'

# 健康检查
curl http://localhost:8000/health
```

gated model（如 Llama、Mistral）需要 HF_TOKEN；镜像内模型下载走 HF，国内网络慢时先在宿主下载好再挂载目录（见第 8 章）。

## 6. HuggingFace TGI

TGI（Text Generation Inference）是 HuggingFace 官方的推理服务，与 HF Hub 深度集成，支持张量并行、量化、连续批处理，也提供 OpenAI 兼容接口。镜像 `ghcr.io/huggingface/text-generation-inference`。

```bash
docker run -d \
  --gpus all \
  --shm-size 1g \
  -p 8080:80 \
  -v ~/.cache/huggingface:/data \
  -e HF_TOKEN=hf_xxx \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id Qwen/Qwen2.5-7B-Instruct \
  --max-total-tokens 8192
```

说明：

- 端口：TGI 服务默认监听容器内 80 端口（映射到宿主 8080）
- `--model-id`：模型名，`--max-total-tokens` 限制输入+输出总 token 数
- 多卡：`--num-shard N`（或自动 `--sharded true`）
- 注意：TGI 官方在 2024 年底起进入维护模式（maintenance mode），功能不再激进演进，新项目优先考虑 vLLM，但已有 TGI 部署仍可继续使用

## 7. 推理前端：Open WebUI

上面都是「后端推理服务」，Open WebUI 是一个 Web 前端（ChatGPT 风格界面），对接 Ollama 或 OpenAI 兼容接口，提供对话、多模型切换、RAG 文档、用户管理。

对接本机 Ollama：

```bash
docker run -d \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --add-host=host.docker.internal:host-gateway \
  ghcr.io/open-webui/open-webui:main
```

说明：

- 容器内 8080 端口映射到宿主 3000，浏览器访问 `http://localhost:3000`
- `OLLAMA_BASE_URL` 指向 Ollama 的地址；Ollama 跑在宿主时用 `host.docker.internal`（Linux 需加 `--add-host=host.docker.internal:host-gateway`）
- Open WebUI 也支持任意 OpenAI 兼容后端（vLLM、llama-server），在设置里把 API 地址指向对应 `/v1` 即可

## 8. 模型缓存与数据卷

大模型权重动辄几 GB 到几十 GB，最怕「每次重启容器都重新下载」。核心原则：把模型缓存目录挂成卷。

HuggingFace 缓存（vLLM / TGI / transformers 用）：

```text
容器内默认缓存目录：/root/.cache/huggingface（root 用户）
相关环境变量：
  HF_HOME              # 缓存根目录（默认 ~/.cache/huggingface）
  HF_HUB_CACHE         # hub 下载缓存（默认 $HF_HOME/hub）
  TRANSFORMERS_CACHE   # transformers 专用缓存
```

```bash
# 先建一个命名卷，后续所有推理容器共用
docker volume create hf-cache

docker run ... \
  -v hf-cache:/root/.cache/huggingface \
  vllm/vllm-openai:latest --model ...
```

Ollama 缓存：

```text
容器内默认目录：/root/.ollama（含 models 子目录）
环境变量 OLLAMA_MODELS 可改
```

```bash
docker volume create ollama-models
docker run -d -v ollama-models:/root/.ollama ...
```

llama.cpp 模型（GGUF 单文件）：

```text
无内置缓存，自己下载到 ./models/ 再挂载
```

国内网络加速下载 HF 模型：宿主上设置 `HF_ENDPOINT=https://hf-mirror.com`（国内镜像）再下载，或直接用 hf 命令行工具下载到本地目录后挂载：

```bash
# 宿主上：用 hf 工具下载（模型会缓存在 ~/.cache/huggingface）
pip install huggingface_hub
HF_ENDPOINT=https://hf-mirror.com hf download Qwen/Qwen2.5-1.5B-Instruct
```

备份与迁移：命名卷用第 8 章末尾的方法打包（`docker run --rm -v hf-cache:/data -v $(pwd):/backup alpine tar czf /backup/hf-cache.tgz -C /data .`）。几十 GB 的缓存迁移，直接卷打包比重新下载快。

## 9. 量化：GGUF / AWQ / GPTQ / FP8

量化是把高精度权重（FP16）转成低精度（INT8/INT4），用精度换显存和速度。大模型部署里「能不能跑起来」往往取决于量化等级。

| 量化 | 生态 | 精度 | 显存（7B 模型） | 说明 |
|---|---|---|---|---|
| FP16（原始） | 通用 | 16bit | ~14GB | 基准，不量化 |
| INT8 | 通用 | 8bit | ~7GB | 损失极小 |
| GGUF Q4_K_M | llama.cpp/Ollama | ~4bit | ~4GB | 质量/体积平衡点，最常用 |
| GGUF Q5_K_M | llama.cpp/Ollama | ~5bit | ~5GB | 质量更好，稍大 |
| GGUF Q8_0 | llama.cpp/Ollama | 8bit | ~8GB | 接近 FP16 质量 |
| AWQ | vLLM/TGI | 4bit | ~4GB | GPU 推理，激活感知量化 |
| GPTQ | vLLM/TGI | 4bit | ~4GB | GPU 推理，需校准 |
| FP8 | vLLM（Hopper+） | 8bit | ~7GB | 新卡专用，速度最快 |

显存估算公式（粗略）：

```text
显存 ≈ 参数量（十亿）× 每参数字节数 + KV cache + 运行开销
每参数字节数：FP16 = 2，INT8/FP8 = 1，INT4 = 0.5
例：7B 模型 FP16 = 7 × 2 = 14GB；7B INT4 = 7 × 0.5 = 3.5GB（实际 ~4GB）
```

选型：

- 显存紧张、要 CPU 混合推理 → GGUF（llama.cpp / Ollama）
- 有 A10/4090 这类 GPU、跑 vLLM 生产服务 → AWQ（4bit 质量好）或 FP8（Hopper 上最快）
- 显存足够（≥ 单卡装下 FP16）→ 不量化，用 FP16 保证质量

Ollama 里选量化：`ollama pull qwen2.5:7b-instruct-q4_K_M`（tag 后缀带量化等级）；vLLM 里用 `--quantization awq --model <AWQ 版本模型名>`（模型本身需是 AWQ 量化版本，如 `Qwen/Qwen2.5-7B-Instruct-AWQ`）。

## 10. 多 GPU 与张量并行

单卡装不下大模型（如 70B 需要 ~140GB FP16，单卡只有 80GB）时，用张量并行把模型切分到多张卡上。

vLLM 张量并行：

```bash
docker run -d \
  --gpus all \
  --ipc=host \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-72B-Instruct-AWQ \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9
```

`--tensor-parallel-size 4` 表示把模型切到 4 张卡。前提：`--gpus all` 暴露了 4 张卡，且卡之间走 NVLink 或高带宽 PCIe（否则通信成为瓶颈）。

TGI 多卡：`--num-shard 4`（`--sharded true` 自动探测卡数）。

llama.cpp 多卡：`-sm layer`（split-mode）按层拆分到多卡，配合 `-ngl` 控制。

说明：单机多卡是「推理服务」层面的加速；跨机分布式推理（几十张卡跑几百 B 模型）超出 Docker 单机范畴，一般走 K8s + Ray/vLLM 集群，本文不展开。

## 11. 显存规划与性能调优

显存三块构成：模型权重 + KV cache + 运行开销（激活、框架、碎片）。

KV cache 是大头，与「并发 × 上下文长度」成正比：

```text
KV cache ≈ 2 × 层数 × 头数 × head_dim × 上下文长度 × 并发 × 每元素字节数
```

调优方向：

1. `--gpu-memory-utilization` 调高（0.9~0.95）多留 KV cache 空间，但要留碎片
2. `--max-model-len` 按业务实际设（不需要 32K 就别开 32K，省显存）
3. 降低并发（`--max-num-seqs`）或缩短上下文
4. 量化（AWQ/FP8 直接砍权重显存）
5. 开启 continuous batching（vLLM/TGI 默认开），吞吐比串行高数倍

性能基准思路（部署前先测，别拍脑袋）：

```bash
# 用 vLLM 自带的 benchmark 脚本测吞吐（在另一个容器或宿主跑）
curl http://localhost:8000/v1/completions -d '{"model":"qwen2.5-7b","prompt":"...","max_tokens":100}' \
  # 或直接用 vLLM 的 bench_serving 工具压测
```

调优顺序：先确认「单请求延迟」达标（模型加载、首 token 延迟），再压「并发吞吐」（token/s），最后调显存利用率。

## 12. OpenAI 兼容 API 与客户端接入

上面四个推理后端（Ollama、llama-server、vLLM、TGI）都提供 OpenAI 兼容接口，意味着用 OpenAI SDK 改一下 `base_url` 就能无缝接入。

Python 接入（OpenAI SDK）：

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",  # vLLM
    api_key="EMPTY",  # vLLM 默认不校验，填任意值
)

resp = client.chat.completions.create(
    model="qwen2.5-7b",
    messages=[{"role": "user", "content": "你好"}],
)
print(resp.choices[0].message.content)
```

各后端 base_url 对照：

| 后端 | base_url | 端口 |
|---|---|---|
| vLLM | `http://host:8000/v1` | 8000 |
| TGI | `http://host:8080/v1` | 8080 |
| llama-server | `http://host:8080/v1` | 8080 |
| Ollama | `http://host:11434/v1` | 11434 |

主流框架接入：LangChain / LlamaIndex 用 `ChatOpenAI(base_url=..., api_key=...)`；Dify / FastGPT / One API 这类网关平台把多个推理后端聚合成一个 OpenAI 出口，多模型统一调度。

## 13. 生产运行要点

推理服务上生产，比「能跑起来」多几个要求：

1. **健康检查**：vLLM 有 `/health` 端点，compose 里配上 healthcheck，配合 `depends_on: condition: service_healthy`
2. **共享内存**：vLLM 必须 `--ipc=host` 或 `--shm-size`，否则多进程通信卡死
3. **重启策略**：`restart: unless-stopped`，模型加载失败要能自动重试
4. **资源限制**：GPU 无法用 cgroup 限制显存（靠 `--gpu-memory-utilization`），但 CPU/内存可限；推理是显存敏感，别和别的服务抢卡
5. **模型不随容器删**：HF cache / Ollama models 挂卷，见第 8 章
6. **密钥安全**：HF_TOKEN 用 docker secret 或 compose `secrets`，别写死在 yaml 或 `-e`（会进 `docker inspect` 可见）
7. **非 root**：vLLM 官方镜像默认 root，生产可 `user:` 指定非 root + 挂卷权限正确
8. **预加载模型**：冷启动要下载+加载模型（分钟级），用 `--model` 指向已挂载的本地模型避免每次下载
9. **日志**：daemon 配日志轮转，推理服务日志量大

compose 示例（vLLM 生产配置）：

```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    ipc: host
    ports:
      - "8000:8000"
    volumes:
      - hf-cache:/root/.cache/huggingface
    environment:
      HF_TOKEN: ${HF_TOKEN}
    command:
      - --model
      - Qwen/Qwen2.5-7B-Instruct
      - --served-model-name
      - qwen2.5-7b
      - --gpu-memory-utilization
      - "0.9"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 120s
    restart: unless-stopped
volumes:
  hf-cache:
```

## 应用场景实战

### 场景一：给团队搭一个本地私有 ChatGPT（Ollama + Open WebUI）

目标：内网一台有 GPU 的机器，跑一个团队共用的对话服务，数据不出内网。

第一步：起 Ollama（GPU 版）：

```bash
docker run -d --name ollama --gpus all \
  -v ollama:/root/.ollama -p 11434:11434 ollama/ollama
```

第二步：拉一个适合内网的中文模型：

```bash
docker exec -it ollama ollama pull qwen2.5:7b
```

第三步：起 Open WebUI 对接：

```bash
docker run -d --name open-webui -p 3000:8080 \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --add-host=host.docker.internal:host-gateway \
  ghcr.io/open-webui/open-webui:main
```

第四步：验证：

```bash
curl http://localhost:11434/v1/chat/completions -d '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"你好"}]}'
# 浏览器打开 http://<机器IP>:3000 注册管理员账号，即可团队使用
```

### 场景二：生产推理服务（vLLM + 标准 OpenAI API + 压测）

目标：线上提供一个高吞吐、标准 OpenAI 接口的推理服务，给业务系统调用。

第一步：起 vLLM（A10/A100 机器）：

```bash
docker run -d --name vllm --gpus all --ipc=host \
  -v hf-cache:/root/.cache/huggingface -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-14B-Instruct-AWQ \
  --served-model-name qwen2.5-14b \
  --gpu-memory-utilization 0.9 --max-model-len 8192
```

第二步：健康检查 + 单发测试：

```bash
curl -f http://localhost:8000/health && echo "服务就绪"
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-14b","messages":[{"role":"user","content":"你好"}],"max_tokens":100}'
```

第三步：业务侧接入（OpenAI SDK 改 base_url，见第 12 章），加一层网关（One API）做多模型路由和 token 计费。

第四步：压测吞吐（vLLM 自带 bench）：

```bash
# 在能访问 8000 的机器上
pip install vllm  # 或直接用官方 benchmark 容器
python -m vllm.entrypoints.openai.api_server  # 参考官方 bench_serving
```

### 场景三：低显存机器跑 7B 模型（llama.cpp CPU+GPU 混合）

目标：一张 GTX 1050（4GB）或纯 CPU 的旧机器，也能跑 7B 量化模型做内部问答。

第一步：下载 GGUF 模型到宿主：

```bash
mkdir -p models && cd models
# 用 hf 或 wget 下载 Qwen2.5-7B-Instruct-GGUF 的 Q4_K_M 单文件到当前目录
```

第二步：起 llama-server（CUDA 镜像，层数按显存调）：

```bash
docker run -d --name llama-server --gpus all \
  -v "$(pwd)/models:/models" -p 8080:8080 \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -m /models/qwen2.5-7b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 --port 8080 -ngl 20 -c 2048
# -ngl 20 只放 20 层进 GPU，剩余走 CPU；显存不够就继续减
```

第三步：验证：

```bash
curl http://localhost:8080/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"qwen","messages":[{"role":"user","content":"你好"}]}'
```

## 最佳实践与踩坑记录

### 最佳实践

1. 模型缓存目录一定挂卷（HF cache / Ollama models），避免每次重启重下几十 GB
2. vLLM 必须 `--ipc=host` 或 `--shm-size`，否则报 Bus error 或卡死
3. 显存不够就降量化等级（FP16 → INT8 → AWQ/GGUF Q4），别硬跑 OOM
4. 生产用 OpenAI 兼容接口 + `--served-model-name` 固定模型名，业务代码与真实模型解耦
5. 部署前先测「单请求延迟 + 并发吞吐」两个指标，再定显存利用率和并发上限
6. HF_TOKEN 走 docker secret / compose secrets，不进环境变量和 yaml
7. 冷启动慢（下载+加载），用本地挂载模型 + 预加载，healthcheck 的 start_period 给足（120s+）
8. 国内环境用 HF_ENDPOINT=https://hf-mirror.com 加速模型下载

### 踩坑记录

坑 1：vLLM 起来后请求报 Bus error 或直接卡死

结论：容器默认共享内存只有 64MB，vLLM 多进程间用 shared memory 通信，超过就崩。

原因：vLLM 的张量并行和 batch 调度依赖 /dev/shm。

解法：`docker run --ipc=host` 或 `--shm-size=1g`。这是 vLLM 部署最常见的坑。

坑 2：容器里 `nvidia-smi` 报 `command not found` 或看不到 GPU

结论：容器里没有 NVIDIA 驱动/CUDA 库，或没传 `--gpus`。

原因：GPU 靠 nvidia-container-toolkit 注入，不是镜像自带；且必须显式 `--gpus all`。

解法：确认宿主 `nvidia-smi` 正常 → 装 nvidia-container-toolkit 并 `nvidia-ctk runtime configure` → 用 `--gpus all` 跑，用 `nvidia/cuda` 镜像验证。

坑 3：vLLM 在 GTX 10 系（Pascal）上报 CUDA 错误或直接不支持

结论：vLLM 要求计算能力 ≥ 7.0，Pascal（6.1）不支持，会报 kernel 编译错误。

原因：vLLM 的 PagedAttention 和量化内核面向 Volta 及更新架构编写。

解法：老卡用 llama.cpp / Ollama（GGUF 量化 + CPU 混合）；vLLM 留给 A10/A100/3090/4090 等。

坑 4：模型每次重启都重新下载，起个容器要十几分钟

结论：没挂 HF cache 卷，容器重建后缓存丢失。

原因：`~/.cache/huggingface` 在容器可写层里，容器删了缓存就没了。

解法：`-v hf-cache:/root/.cache/huggingface` 挂命名卷；或在宿主先下好再挂载本地目录。

坑 5：`-e HF_TOKEN=xxx` 之后 token 泄露

结论：`docker inspect` 能看到环境变量里的 token。

原因：环境变量写进容器配置，任何能 docker inspect 的人都能读。

解法：token 走 compose `secrets` 或 `--secret` 文件挂载，不放进 environment。

坑 6：多卡跑 vLLM 吞吐不升反降

结论：卡之间没有 NVLink/高带宽互联时，张量并行的通信开销大于并行收益。

原因：张量并行每层都要跨卡通信，PCIe 带宽不够就成了瓶颈。

解法：单卡能装下就用单卡；必须多卡时确保 NVLink 或高速 PCIe，并用 `--tensor-parallel-size` 合理切分。

坑 7：Ollama 容器里拉模型后，重建容器模型全没了

结论：`ollama pull` 的模型存在 `/root/.ollama`，没挂卷就随容器删。

原因：同上，数据在容器可写层。

解法：起 Ollama 时 `-v ollama:/root/.ollama`，模型数据持久化。

坑 8：上下文一长就 OOM，短请求没事

结论：KV cache 随「并发 × 上下文长度」线性增长，`--max-model-len` 开太大把显存吃满。

原因：显存 = 权重 + KV cache + 开销，KV cache 是弹性部分。

解法：按业务实际设 `--max-model-len`；降低并发；或量化权重腾显存给 KV cache。

## 相关文档

- [[Docker完整教程]] — Docker 基础：镜像、容器、Dockerfile、卷、网络、compose，本文的 Docker 用法基础
- [[Docker面试题]] — Docker 面试题大全，含容器底层原理与运维要点
- [[kubernetes-minikube-install]] — 单机推理服务如何走向集群：K8s 集群搭建
- [[kubernetes-springboot-vue-deploy]] — 容器化应用部署到 K8s 的完整对照
- [[Kubernetes完整教程]] — Kubernetes 完整知识教程，推理服务集群化编排的下一站
- [[16.4-容器与部署]] — 算法工程化：Docker/Kubernetes/GPU 调度/服务发现
