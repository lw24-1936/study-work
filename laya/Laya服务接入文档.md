---
title: Laya 决策服务接入文档
created: 2026-09-21
updated: 2026-09-21
type: reference
tags: [laya, api, fastapi, http, 接入, systemd, curl, python, java, vue, spring-boot, 部署]
status: 已完成
---

# Laya 决策服务接入文档

> 本文是 `12_service.py` 这层服务的**接入说明书**：接口长什么样、怎么鉴权、四种语言的客户端怎么写、从别的机器（含手机）怎么连、出错了怎么查。
> 模型本身的原理、安装、校准、踩坑见同目录 [Laya完整教程](./Laya完整教程.md)；本文只管「怎么把决策能力接进你的系统」。
> 状态：已完成 ｜ 本机部署时间：2026-09-21 ｜ 全部接口响应均为本机实测（原始日志 `/opt/ai-lab/laya/logs/external_call_test.txt`）。

## 目录

- [1. 你要接入的是什么](#1-你要接入的是什么)
- [2. 本机部署现状（含启停命令）](#2-本机部署现状含启停命令)
- [3. 接口契约](#3-接口契约)
- [4. 客户端接入示例（curl / Python / Java 8 / Vue 2 / Node）](#4-客户端接入示例curl--python--java-8--vue-2--node)
- [5. 从别的机器 / 手机接入](#5-从别的机器--手机接入)
- [6. 性能、容量与超时设置](#6-性能容量与超时设置)
- [7. 运维手册](#7-运维手册)
- [8. 排错速查](#8-排错速查)
- [9. 客户端文件清单](#9-客户端文件清单)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

---

## 1. 你要接入的是什么

Laya 是一个**非自回归的决策模型**：一次前向就能对一条 `state`（文本）在同一批 `questions` 上给出**一次性、相互独立**的判断，不做逐 token 生成。所以它接进来的形态不是「聊天接口」，而是**结构化打标 / 分诊接口**：

```text
你给她一段文本 + 一组问题  →  她一次性回给你 每个问题的答案 + 概率分布 + 置信度 + 路由信息
```

它不产生自然语言回答（没有 output token 这回事，响应里 `usage.output_tokens` 恒为 0），所以**不要指望用它生成回复内容**；它的位置在「LLM 前面做路由 / 守门」或「LLM 后面做结构化落库」这两处。

三种题型（`questions[*].type` 只允许这三个值）：

```text
choice  从 N 个互斥选项里选一个     →  answers.<key>.choice + probabilities（每个选项一个概率）
score  在有序刻度上打一个分        →  answers.<key>.score（0..k-1 的期望）+ probabilities
noul   不需要选项，直接给概率      →  answers.<key>.noul（"是不是…" 是/否，连续概率，不是二分类）
```

单次调用里可以问**多个问题**（比如同时问部门、紧急度、流失风险），它们共享同一条 state，只在序列里各占一个 head——这就是它比「调三次 LLM」便宜的地方。

---

## 2. 本机部署现状（含启停命令）

```text
服务地址（本机）    http://127.0.0.1:8077
服务地址（局域网）  http://192.168.1.167:8077
服务地址（Tailscale）http://100.71.112.119:8077
监听              0.0.0.0:8077（对外可达）
鉴权              开（X-API-Key 请求头，key 存在 /etc/laya-decide.env，权限 600）
加载的 checkpoint  english + multilingual（装在同一进程里，按语言自动路由）
运行设备          cpu（本机是 4 GB 显存的 GTX 1050，两份权重同时上卡会 OOM 退回 CPU，见教程第 9 章）
托管方式          systemd 单元 laya-decide.service（开机自启）
日志              /opt/ai-lab/laya/logs/laya-decide.log
代码              /opt/study-work/laya/examples/12_service.py
环境变量文件      /etc/laya-decide.env
```

日常命令：

```bash
systemctl status laya-decide          # 看状态（active / 加载中）
systemctl restart laya-decide         # 重启（会重新加载模型，CPU 冷启 2~3 分钟，缓存热 60 秒左右）
systemctl stop laya-decide            # 停
systemctl disable --now laya-decide   # 停掉并取消开机自启（不想让它常驻时用这条）
journalctl -u laya-decide -n 50       # 单元级日志（程序自身的 print 在 append 的日志文件里）
tail -f /opt/ai-lab/laya/logs/laya-decide.log    # 服务自身日志（含 preload 用时）
```

改配置（端口、设备、key、镜像地址）都改 `/etc/laya-decide.env`，改完 `systemctl restart laya-decide`：

```text
HF_ENDPOINT=https://hf-mirror.com      # 权重走国内镜像（首次拉取/清缓存后需要）
HF_HUB_DISABLE_XET=1                   # 关掉 Xet 传输，否则镜像会 401
LAYA_DEVICE=cpu                        # 改成 cuda 可用 GPU，但两份权重同时上卡会 OOM，只留一份才稳
LAYA_HOST=0.0.0.0                      # 只给本机用就改回 127.0.0.1
LAYA_PORT=8077
LAYA_API_KEY=<32 位随机串>              # 留空 = 不校验（客户端就不用带 X-API-Key）
```

**不装 systemd 时的前台跑法**（调试用）：

```bash
cd /opt/study-work/laya/examples
export HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1
export LAYA_DEVICE=cpu LAYA_HOST=0.0.0.0 LAYA_API_KEY=你的key
/opt/ai-lab/laya/.venv/bin/python -u 12_service.py
```

---

## 3. 接口契约

两个端点，都是同步的（模型推理在请求线程里跑完才返回）。

### 3.1 `GET /health`

无鉴权（方便探活；如果不想暴露它，把它也挂上 `Depends(require_key)`）。

```json
{"status":"ok","loaded":["english","multilingual"],"device":"cpu","auth":true,"uptime_s":65.0}
```

| 字段 | 含义 | 能拿来干什么 |
|---|---|---|
| `status` | 恒为 `ok`（服务在加载模型时这个端点**还不可用**） | 探活 |
| `loaded` | 已加载的 checkpoint 名列表 | 确认想要的模型进内存了 |
| `device` | `cpu` / `cuda` / `auto` | 环境对了没 |
| `auth` | 是否开启 key 校验 | 客户端据此决定要不要带 key |
| `uptime_s` | 进程启动至今秒数 | 判断是不是刚重启过（刚启动就别打流量，见第 6 章） |

### 3.2 `POST /decide`

**请求体**

```json
{
  "state": {"message": "We were charged twice for March and nobody replies. Please refund today or we cancel."},
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which department should handle this request?",
      "criteria": {"billing": "invoices, payments, refunds", "technical": "bugs, outages, system errors"}
    },
    "urgency": {
      "type": "score",
      "instructions": "How urgent is this request?",
      "criteria": ["not urgent", "soon", "critical deadline or blocking issue"]
    },
    "churn_risk": {"type": "noul", "instructions": "Does the user threaten to cancel or leave?"}
  },
  "model": "english"
}
```

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `state` | 是 | 字符串 **或** 对象 | 要判断的文本。给字符串 = 原样送进模型；给对象 = 每个键值对渲染成 `key: value` 再送（`{"message": "..."}`、`{"subject": "...", "body": "..."}` 都行）。**别把它当成 prompt**，模型读的是文本本身，不是指令 |
| `questions` | 否 | 对象 | 缺省时用服务端的 `DEFAULT_QUESTIONS`（department / urgency / churn_risk 三问，中文文本也走这三个问题）。想按业务定制就传 |
| `questions[*].type` | 是 | `choice`\|`score`\|`noul` | 只有这三种，别的值直接 422 |
| `questions[*].instructions` | 是 | 字符串 | 这个问题的题面（英文 checkpoint 用英文题面最稳） |
| `questions[*].criteria` | choice/score 必填 | `choice`：`{选项key: 解释}`；`score`：`[刻度0解释, 刻度1解释, ...]` | 选项数不是越多越好，见下方「token 预算」 |
| `model` | 否 | `english`\|`multilingual`\|`typed-decisions` | 显式指定就不走自动路由。**注意：指定的模型必须已 preload，否则会现场加载（首次几秒~几十秒）** |

**响应体**（真实响应，本机实测；为便于阅读做了换行）

```json
{
  "model": "laya-rl-agent",
  "answers": {
    "department": {
      "type": "choice",
      "choice": "billing",
      "probabilities": {"billing": 0.9916, "technical": 0.0028, "sales": 0.0025, "other": 0.003},
      "confidence": 0.9585,
      "action": {"act_probability": 1.0}
    },
    "urgency": {
      "type": "score",
      "score": 1.3651,
      "legend": {"0": "not urgent", "1": "soon", "2": "critical deadline or blocking issue"},
      "probabilities": {"0": 0.1015, "1": 0.432, "2": 0.4665},
      "confidence": 0.1349,
      "action": {"act_probability": 1.0}
    },
    "churn_risk": {"type": "noul", "noul": 0.8385, "confidence": 0.8385, "action": {"act_probability": 1.0}}
  },
  "usage": {"input_tokens": 180, "output_tokens": 0},
  "routing": {
    "model": "english",
    "repo": "convaiinnovations/laya",
    "reason": "English Latin text",
    "detection": {"script": "latin", "script_profile": {"latin": 1.0}, "language": "en", "is_english": true, "non_latin_fraction": 0.0},
    "workflow": null
  },
  "latency_ms": 5412.2
}
```

| 字段 | 怎么用 |
|---|---|
| `answers.<你的key>.choice` | choice 题的唯一答案（**这是 argmax，不是「唯一确定的答案」**） |
| `answers.<你的key>.probabilities` | 全部标签的概率分布，做「低置信度转人工」时用它，而不是只看 confidence |
| `answers.<你的key>.score` | score 题的打分（0..k-1 的**期望值**，所以会出现 1.3651 这种小数） |
| `answers.<你的key>.legend` | score 题的刻度文案，原样回带，前端不用自己映射 |
| `answers.<你的key>.noul` | noul 题的连续概率（0~1）。**它不是二分类**，要么阈值化，要么直接当特征用 |
| `answers.<你的key>.confidence` | `1 - H(p)/log(k)` 的归一化熵（教程 6.1）。**不是答对的概率**，官方英文 checkpoint 的 mean ECE 是 0.466——门控阈值必须自己在业务数据上量（教程 6.4） |
| `answers.<你的key>.action.act_probability` | typed-decisions checkpoint 才会给非 1.0 的值，其余为占位 |
| `usage.input_tokens` | 这条 state + 全部问题占的 token（按 192/256 的 head 预算记账），**用来做成本/容量估算** |
| `routing.model` / `routing.reason` | 实际用了哪个 checkpoint、为什么（路由理由直接可读，非常适合打日志） |
| `routing.detection` | 脚本/语言检测明细：`script`（latin/han/cyrillic…）、`script_profile`（各脚本占比）、`language`（BCP-47 或 null）、`is_english` |
| `routing.workflow` | 用了内置预设时才是非 null（如 `triage`、`email`） |
| `latency_ms` | 服务端**纯推理**耗时，不含网络往返（客户端自己再量一次总耗时，两者差值就是网络 + 序列化） |

**错误响应**

| HTTP | 触发条件 | 响应体 | 客户端该怎么办 |
|---|---|---|---|
| 401 | 服务端开了鉴权，`X-API-Key` 缺失或不对 | `{"detail":"bad or missing X-API-Key"}` | 检查 key 与请求头名字（是 `X-API-Key`，不是 `Authorization`） |
| 404 | 路径写错（如 `/api/decide`） | `{"detail":"Not Found"}` | 端点是 `/decide`，没有版本前缀 |
| 422 | 请求体不合 schema（`type` 给了 `bool`、`criteria` 缺失、`state` 是数字等） | FastAPI 标准校验错误 | **模型没跑**，直接修请求体；这是最便宜的失败 |
| 500 | 推理内部异常（如选项多到塞不进 `max_len`） | `{"detail":"Internal Server Error"}` | 看服务日志；先确认问题/选项数没超预算（教程第 7 章） |
| 503 / 连接被拒 | 服务还在 preload，或没启动 | 连不上/连接超时 | 探活重试；**注意 health 通 ≠ 可以打流量**（第 6 章） |

### 3.3 token 预算：接入前必须算的一笔账

一次 `/decide` 的输入空间是**两段**的（教程 7.1）：`state` 走 `max_len`（英文 512 / 多语言 256+），问题区走各 checkpoint 的 `head_max_len`（英文 192、多语言与 typed-decisions 256）。选项越多数，每个选项能分到的 token 越少（**会静默截断**：选项 `criteria` 的文字被砍掉，只剩下 key）：

```text
（英文 checkpoint，head_max_len=192 时实测）
选项数   选项占用 token   剩余给题面   每选项 token 上限
4        28             164         44
10       70             122         17
30       210             -18          5      ← 已经不是「够不够」而是超预算
77       539             -347          2      ← 实测每选项只剩 4 个 token，criteria 基本被砍光
```

**接入建议**：单个 choice 题的选项控制在 **10 个以内**、`criteria` 每个选项一句话（10 个词以内）。选项数上百（例如上万 SKU 的分类）不要塞进一个问题，用**两级选择**：先选大类（≤8 个），再在大类里选具体项（教程 7.3 有完整写法）。

---

## 4. 客户端接入示例（curl / Python / Java 8 / Vue 2 / Node）

> 下面 5 个文件都在 `/opt/study-work/laya/examples/http-clients/`，**Python / Node / Java / curl 四个本机实测通过**（Java 按 `--release 8` 编译），Vue 版需要 axios 未在本机运行。
> 所有示例里的 key 都从环境变量读，不要写进代码或提交进仓库。

### 4.1 curl（最快验证通路）

```bash
export LAYA_API_KEY=<你的key>
BASE=http://192.168.1.167:8077

# 探活
curl -s $BASE/health

# 无 key → 401（实测 1.5 ms 返回）
curl -s -X POST $BASE/decide -H 'Content-Type: application/json' \
  -d '{"state":{"message":"Please refund the duplicate charge."}}'
# {"detail":"bad or missing X-API-Key"}

# 带 key → 200
curl -s -X POST $BASE/decide \
  -H 'Content-Type: application/json' -H "X-API-Key: $LAYA_API_KEY" \
  -d '{"state":{"message":"We were charged twice for March and nobody replies. Please refund today or we cancel."}}'
```

### 4.2 Python（只用标准库，目标机器不需要装 laya/torch）

`http-clients/client.py`：

```python
import json, os, urllib.request

def decide(base_url, text, api_key=None, timeout=60.0):
    body = json.dumps({"state": {"message": text}}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(base_url.rstrip("/") + "/decide", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("X-API-Key", api_key)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

res = decide("http://192.168.1.167:8077", "请把 3 月的账单退款", os.environ.get("LAYA_API_KEY"))
print(res["routing"]["model"], res["answers"]["department"]["choice"], res["answers"]["department"]["confidence"])
```

实测输出（德文文本，走的是多语言 checkpoint）：

```text
$ python3 client.py --url http://192.168.1.167:8077 --text "Der Kunde wurde zweimal belastet, bitte erstatten Sie die Zahlung."
路由模型   : multilingual（Latin script but language looks like 'de', not English）
部门       : billing（置信度 0.9948）
紧急度     : 1.88  {'0': 'not urgent', '1': 'soon', '2': 'critical deadline or blocking issue'}
流失风险   : 0.0284（置信度 0.9716）
tokens     : 输入 171
服务端耗时 : 266.0 ms（不含网络往返）
```

### 4.3 Java 8 + Spring Boot 2.7

`http-clients/Client.java` 用 `HttpURLConnection` 写（**不用 `java.net.http.HttpClient`，那是 JDK 11+**），本机 `javac --release 8` 编译通过并运行：

```bash
javac --release 8 -d /tmp/laya-client Client.java
java -cp /tmp/laya-client Client http://192.168.1.167:8077 "My invoice from February is still unpaid, please resend it."
```

实测输出（服务端 `latency_ms` 649.6 ms，Java 进程总耗时 3162 ms，差值主要是 JVM 启动与首次 JIT）：

```text
HTTP 响应（3162 ms，含网络往返）:
{"model":"laya-rl-agent","answers":{"department":{"type":"choice","choice":"billing",...
 "confidence":0.9646,...},"urgency":{"score":1.1527,...},"churn_risk":{"noul":0.0469,...}},
 "usage":{"input_tokens":168,"output_tokens":0},"routing":{"model":"english",...},"latency_ms":649.6}
```

放进 Spring Boot 2.7 项目时，用 `RestTemplate` + Jackson 更顺手（**下面是接入写法，未在本机编译——本机没有 Spring 依赖；已验证的是上面的 `Client.java` 写法**）：

```java
// LayaClient.java —— JDK 1.8 口径：javax.*、匿名内部类、无 Stream/Lambda
import java.util.HashMap;
import java.util.Map;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

public class LayaClient {

    private final RestTemplate restTemplate;
    private final String baseUrl;
    private final String apiKey;

    public LayaClient(String baseUrl, String apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        // 服务端首次请求可能慢一个数量级，读超时别用默认值
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(60000);
        this.restTemplate = new RestTemplate(factory);
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> decide(String text) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        if (apiKey != null && apiKey.length() > 0) {
            headers.set("X-API-Key", apiKey);
        }
        Map<String, Object> state = new HashMap<String, Object>();
        state.put("message", text);
        Map<String, Object> payload = new HashMap<String, Object>();
        payload.put("state", state);
        // 想自定义问题集就往 payload 里再塞一个 "questions"（Map），结构见 3.2

        try {
            ResponseEntity<Map> resp = restTemplate.postForEntity(
                    baseUrl + "/decide", new HttpEntity<Map<String, Object>>(payload, headers), Map.class);
            return resp.getBody();
        } catch (HttpClientErrorException e) {
            // 401 = key 不对；422 = 请求体不合 schema；500 = 推理异常
            throw new IllegalStateException("laya 调用失败 HTTP " + e.getRawStatusCode() + ": " + e.getResponseBodyAsString(), e);
        }
    }
}
```

解析响应时的口径（避免踩坑）：`answers` 是 `Map<String, Map<String, Object>>`；`choice` 题的答案是 `answers.get("department").get("choice")`，`noul` 题是 `("churn_risk").get("noul")`（**Double**，不是 Boolean），`score` 题是 `("urgency").get("score")`（**Double**）。别用强类型实体去硬映射整棵树——`probabilities` 的 key 是你自己定的选项名，实体类只能写到 `Map` 这一层。

### 4.4 Vue 2（CLI5 + router3 + Vuex3）+ axios

`http-clients/api.js` 是一个可 import 的 api 模块（走 `VUE_APP_LAYA_URL` / `VUE_APP_LAYA_KEY`，key 放 `.env.local` 不提交）：

```javascript
// .env.local
// VUE_APP_LAYA_URL=http://192.168.1.167:8077
// VUE_APP_LAYA_KEY=<你的key>

import { decide } from '@/api/laya'

export default {
  data() {
    return { text: '', result: null, loading: false, error: '' }
  },
  methods: {
    async submit() {
      this.loading = true
      this.error = ''
      try {
        this.result = await decide(this.text)          // 返回的就是响应体本身
      } catch (e) {
        this.error = e.message                          // 401/503 已在拦截器里转成中文提示
      } finally {
        this.loading = false
      }
    },
  },
}
```

**跨域**：浏览器直连本机服务会吃到 CORS 限制。两种做法——① 开发期用 `vue.config.js` 的 `devServer.proxy` 代理到 `http://127.0.0.1:8077`；② 生产环境让 nginx 同域反代 `/laya/` 到后端（第 5.3 节），前端就写相对路径 `/laya/decide`，不涉及跨域。

### 4.5 Node（内置 fetch，Node 18+）

`http-clients/client.js` 不需要 `npm install`：

```text
$ node client.js http://192.168.1.167:8077 "The API returns 502 on /v2/export since the last deploy."
路由模型   : english（English Latin text）
部门       : technical（置信度 0.6691）
紧急度     : 1.15
流失风险   : 0.0002（置信度 0.9998）
服务端耗时 : 715.9 ms ｜ 客户端总耗时 758 ms（含网络往返）
```

---

## 5. 从别的机器 / 手机接入

### 5.1 为什么默认连不上

服务默认 `LAYA_HOST=127.0.0.1`，只在回环地址监听 —— 这是**故意的**（避免一台笔记本上跑的模型服务被同网段任何人白嫖）。要对外必须先设 `LAYA_HOST=0.0.0.0`（本机已设好）**并且**有可达的 IP。

### 5.2 三种可达路径（按暴露面从小到大）

```text
① 局域网（同一 Wi-Fi）      http://192.168.1.167:8077
   实测：192.168.1.167/24（wlp0s20f3）。手机连同一个 Wi-Fi 就能调用。
   代价：同网段任何人都能扫到端口，**所以必须开 LAYA_API_KEY**。

② Tailscale（推荐给「在外网也要用」）  http://100.71.112.119:8077
   实测：本机装了 tailscale0，地址 100.71.112.119。手机/笔记本装上 Tailscale 并在同一 tailnet 里，
   就能像内网一样直连，**不需要公网 IP、不需要开防火墙、不需要证书**。
   代价：调用方必须加入你的 tailnet。

③ 公网（不推荐直接把 8077 暴露到互联网）
   如果确实要，前面加 nginx + TLS + 鉴权，只反代 /laya/ 前缀，并且限制来源 IP。
```

### 5.3 公网/同域反代（nginx 片段）

```nginx
location /laya/ {
    # 去掉前缀转发：/laya/decide -> /decide
    proxy_pass http://127.0.0.1:8077/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    # 首次请求可能 5 秒以上，60 秒内不要断
    proxy_read_timeout 60s;
    proxy_send_timeout 60s;

    # 决策接口是纯计算，不需要传大 body
    client_max_body_size 64k;

    # 可选：在这一层再加一道 Basic Auth 或 JWT，服务本身的 X-API-Key 继续保留
}
```

### 5.4 本机防火墙

本机 `ufw` 状态为 **不活动**（未启用），所以局域网直连不需要额外开放端口。如果哪天启用了 ufw，记得：

```bash
ufw allow from 192.168.1.0/24 to any port 8077 proto tcp   # 只给局域网
ufw status
```

**注意**：这套 `systemd` 直跑的方式**没有容器网络层**；如果以后把它挪进 Docker，就要额外处理端口映射与 `--network host` 的差异（见 [[Docker完整教程]]）。

---

## 6. 性能、容量与超时设置

本机（GTX 1050 4 GB + CPU 双跑模式）实测数据，接入时的超时/容量参数直接照着设：

```text
场景                                 服务端 latency_ms     客户端总耗时       说明
服务刚起，第一条真实请求               5412.2             5413 ms          含进程内首次前向的一次性开销
之后（英文，短文本）                   649.6             3162 ms（Java）    差值 = JVM 启动 + 首次 JIT
之后（英文，Node）                     715.9              758 ms           网络 + 序列化约 42 ms
之后（德文，走多语言 checkpoint）      266.0              272 ms            多语言路线比英文更省（state 更短）
之后（中文，走多语言）                 197.6              199 ms            han 脚本直接判给多语言，不试探英文
无 key 的 401 拒绝                     1.5                —                 鉴权在推理之前，几乎零成本
```

要点：

```text
1. 超时：客户端 read timeout 设 60 s（首次请求要 5 秒以上），connect timeout 3~5 s。
   别学「统一 5 秒」——那会在冷启或预热期把好请求打死。
2. 预热：服务 health 返回 ok 之后，自己再打 1~2 条真实请求（比如固定的样例文本）再放进负载均衡。
   实测第一条 5412 ms，第二条就回到 266 ms。
3. 并发：laya 的 forward 是**同步阻塞**的，uvicorn 单 worker 下请求排队。
   本机 CPU 模式单问 ~200~800 ms（教程 9.3），也就是**单进程约 1~5 QPS**；
   要更高只有三条路：换 GPU（本机 3~4 倍，教程 9.3）、多 worker（每 worker 各自加载一份权重，
   内存/显存翻倍）、上游批量合并（把多条 state 攒批，需要自己写，官方没暴露 batch API）。
4. 容量：每条 `/decide` 的 `usage.input_tokens` 就是成本口径（实测英文三问约 170~180 tokens，
   多语言约 170 tokens）。按你的峰值 QPS × 平均 tokens 估内存带宽与延迟预算。
5. 别在 4 GB 卡上同时装两份权重：会 OOM 并**静默退回 CPU**（教程坑 2、坑 12）。
```

---

## 7. 运维手册

```text
日志分割          服务日志 append 到 /opt/ai-lab/laya/logs/laya-decide.log，没有自动轮转；
                  接生产建议加 logrotate 或在 unit 里改成 StandardOutput=journal。
健康探针          建议 30 s 一次 GET /health，并检查 loaded 是否包含你需要的模型；
                  进程活着但 preload 没完成时，端口还没监听，探针会失败——这正是要的语义。
key 轮换          改 /etc/laya-decide.env 里的 LAYA_API_KEY，systemctl restart laya-decide，
                  然后通知调用方换 key（**重启会触发权重重新加载，CPU 冷启 2~3 分钟**，
                  选低峰期做；想避免重载可以把 key 写成读文件 + 热更新，需要改服务代码）。
模型升级          换 laya 或 transformers 版本后，先跑一遍 /opt/study-work/laya/examples/
                  下的示例确认输出分布没漂移，再重启服务。
停用              systemctl disable --now laya-decide.service（保留 unit 文件）或
                  rm /etc/systemd/system/laya-decide.service && systemctl daemon-reload。
                  顺带提醒：/etc/laya-decide.env 里是 key，权限保持 600。
```

---

## 8. 排错速查

| 现象 | 原因 | 处理 |
|---|---|---|
| `连不上服务（Connection refused）` | 服务没起 / 还在 preload / `LAYA_HOST` 不是 `0.0.0.0` | `systemctl status laya-decide`；`ss -lntp \| grep 8077` 看监听地址；看日志最后一行是不是 `已 preload` |
| 从别的机器连不上，本机 `curl localhost` 正常 | 服务只监听了回环 | 改 `LAYA_HOST=0.0.0.0` 后重启 |
| `HTTP 401` | key 缺失/不对/请求头名字写错 | 请求头是 `X-API-Key`；key 在 `/etc/laya-decide.env` |
| `HTTP 422` | 请求体不合 schema（`type` 不是三种之一、`criteria` 缺失、`state` 类型错） | 对着 3.2 的表逐字段核；422 不消耗推理 |
| `HTTP 500` | 推理内部异常（最常见：选项多到放不进 `max_len`） | 减少选项数或改两级选择（教程 7.3） |
| 第一次请求特别慢（数秒） | 进程内首次前向的一次性开销 | 启动后主动预热；客户端读超时给到 60 s |
| 中文/日文结果很差 | 被路由到了英文 checkpoint | 看响应 `routing.model`；中文应为 `multilingual`（实测 reason: `non-Latin script (han, 100% of letters)`）。若不对，显式传 `"model":"multilingual"` |
| 响应里 `answers` 缺某个 key | 响应的 key 就是你 `questions` 的 key | 检查拼写；用默认问题集时 key 是 `department`/`urgency`/`churn_risk` |
| `confidence` 很高但结果是错的 | confidence 是归一化熵，不是正确率（官方 mean ECE 0.466） | 门控阈值必须在自己的数据上量（教程 6.4）；或先做温度校准（教程 6.3） |
| 并发一大就排队/超时 | forward 同步阻塞 + 单 worker | 见第 6 章「并发」三条路 |
| GPU 明明可用却跑在 CPU | 权重同时加载超过显存 → laya 静默降级 | 看日志里的 `[laya] Warning: could not place the model on cuda`；只 preload 一份权重 |

---

## 9. 客户端文件清单

```text
/opt/study-work/laya/examples/http-clients/
├── client.py      Python 标准库客户端（含 --raw 打印完整 JSON、401/503 错误处理）  ← 本机实测通过
├── client.js      Node 18+ 内置 fetch 客户端（无需 npm install）              ← 本机实测通过
├── Client.java    Java 8 兼容客户端（HttpURLConnection + 手拼 JSON）           ← 本机实测通过
├── api.js         Vue 2 + axios 的 api 模块（含 401/503 中文提示与拦截器）      ← 未在本机运行（需 axios）
└── client.sh      curl 版示例（含无 key / 带 key 两次调用对比）                 ← 本机实测通过
```

服务端代码与单元文件：

```text
/opt/study-work/laya/examples/12_service.py     FastAPI 服务（LAYA_HOST / LAYA_PORT / LAYA_API_KEY / LAYA_DEVICE）
/etc/laya-decide.env                            环境变量（含 key，权限 600）
/etc/systemd/system/laya-decide.service         systemd 单元（开机自启，日志 append 到文件）
/opt/ai-lab/laya/logs/laya-decide.log           运行日志
/opt/ai-lab/laya/logs/external_call_test.txt    本文所有外部调用实测的原始输出
```

---

---

## 应用场景实战

### 场景一：客服工单自动分诊（Spring Boot 2.7 接入）

```text
现有系统：工单表 ticket(id, title, content, dept, urgency, churn_risk, created_at)
接入点    ：工单入库时同步调 /decide（CPU 模式 200~800 ms，够用），把三问结果写回字段
```

```java
// TicketService.java（JDK 1.8 口径）
public void onTicketCreated(Ticket ticket) {
    Map<String, Object> res = layaClient.decide(ticket.getTitle() + "\n" + ticket.getContent());
    Map<String, Object> answers = (Map<String, Object>) res.get("answers");

    Map<String, Object> dept = (Map<String, Object>) answers.get("department");
    ticket.setDept((String) dept.get("choice"));

    Map<String, Object> urgency = (Map<String, Object>) answers.get("urgency");
    ticket.setUrgency(((Number) urgency.get("score")).doubleValue());

    Map<String, Object> churn = (Map<String, Object>) answers.get("churn_risk");
    ticket.setChurnRisk(((Number) churn.get("noul")).doubleValue());

    // 低置信度转人工：阈值必须自己在业务数据上量（见教程 6.4），别抄别人的
    double conf = ((Number) dept.get("confidence")).doubleValue();
    if (conf < 0.7) {
        ticket.setNeedHumanReview(true);
    }
    // 路由信息记日志，多语言流量会把英文侧指标带偏
    log.info("laya route={} reason={} latency={}ms",
             ((Map<String, Object>) res.get("routing")).get("model"),
             ((Map<String, Object>) res.get("routing")).get("reason"),
             res.get("latency_ms"));
}
```

真实请求/响应（本机实测，取第 4.1 节那条英文工单）：

```text
请求 state ："We were charged twice for March and nobody replies. Please refund today or we cancel."
department ：billing   （置信度 0.9585，剩余 3 类概率 0.0025~0.003）
urgency    ：1.3651    （刻度 0/1/2 的概率 0.1015 / 0.4320 / 0.4665）
churn_risk ：0.8385    ← 威胁流失，应当命中「高优先级回访」
usage      ：input_tokens 180
```

注意这条数据的两个信号：`urgency` 的 confidence 只有 0.1349（分布几乎是平的三选一），
但 `churn_risk` 给出了 0.8385 的强信号——**只看单个问题的 confidence 会漏掉这条工单的真实风险**，
所以「转人工」的判定建议做成多个问题的联合规则，而不是只看一个总置信度。

### 场景二：邮件安全网关的第一道闸

```text
邮件进来到达 MTA → 解析出 subject + body（先做清洗，教程 8.2 的 clean_email_body 能把引用历史、
签名、HTML 标签去掉）→ 调 /decide 问 noul 题「Is this email a phishing attempt?」
→ 阈值以上直接进隔离区，阈值以下交给后面的 LLM 或人工
```

```json
{
  "state": {"subject": "Urgent: verify your account", "body": "..."},
  "questions": {
    "phishing": {"type": "noul", "instructions": "Is this message an attempt to phish or defraud the recipient?"},
    "intent": {"type": "choice", "instructions": "What does the sender want?",
               "criteria": {"click_link": "click a link or open an attachment", "reply_info": "reply with credentials or personal data", "pay": "send money", "other": "none of the above"}}
  }
}
```

**别把它当唯一防线**：教程第 12 章的实测里，一封普通的推广邮件被判 phishing = 0.9999。
它是**高召回的第一道闸 + 人工复核队列**，不是终审。

### 场景三：LLM 前置守门（省钱的那种接法）

```text
用户输入 → /decide 问「是否包含有害请求 / 是否需要工具调用 / 属于哪个业务域」
        → 无害且命中 FAQ 域：直接走规则或小模型
        → 需要生成：再调 LLM（把 Laya 的判定拼进 system prompt 或用于选工具）
```

好处是**成本口径明确**：一次 `/decide` 实测 100~180 input token、0 output token，
比「先让 LLM 判断意图」便宜一两个数量级，而且没有生成的不确定性。实测延迟 200~700 ms（CPU）。

### 场景四：离线批量打标（不是 HTTP，直接调库）

数据量大（几十万条以上）时不要走 HTTP：HTTP 层是给在线流量用的，批量直接 import laya 更快
（少一次序列化、少一次进程间拷贝），脚本见 `examples/13_batch_labeling.py`（断点续跑）。
实测吞吐见教程 9.4：CPU 上约 2.5 条/秒（每条 3 问），GPU 上约 370 ms/条。

---

## 最佳实践与踩坑记录

### 最佳实践

```text
1. 客户端读超时给 60 s、连接超时 3~5 s；不要因为「服务本地」就把超时设成 1~2 s。
2. 启动后先打 1~2 条固定样例预热，再接入流量（首条 5412 ms → 第二条 266 ms 的实测差距）。
3. 把 routing.model / routing.reason / latency_ms / usage.input_tokens 全部落日志并按模型分桶统计。
4. 转人工的判定用「多问题联合规则」，不要只卡单个 confidence（场景一里的真实反例）。
5. choice 题选项 ≤ 10 个、criteria 每条一句话；选项上百改用两级选择（第 3.3 节）。
6. key 放环境变量或 `.env.local`，前端只放 `VUE_APP_*` 前缀的变量，绝不进仓库。
7. 显式指定 model 之前先确认它已被 preload（`/health` 的 loaded 字段），否则首次请求要现场加载。
8. 让 nginx 同域反代 `/laya/`，前端写相对路径，从根上绕开 CORS。
9. 上线前用真实业务文本跑一遍，量出你自己数据上的 ECE 与阈值（官方英文 checkpoint 的 mean ECE 是 0.466）。
10. 别在 4 GB 显存的卡上同时装两份权重（会 OOM 并静默退回 CPU，速度掉到 CPU 档）。
```

### 踩坑记录

```text
坑 1：服务默认只监听 127.0.0.1，外部机器 curl 直接 connection refused。
      处理：LAYA_HOST=0.0.0.0 后重启；对外暴露时务必同时设 LAYA_API_KEY。

坑 2：把 /health 通当成「可以打流量」，结果第一条请求 5412 ms 被客户端超时打断。
      处理：health ok 之后再打 1~2 条预热请求；客户端读超时给到 60 s。

坑 3：Java 客户端照抄网上的 java.net.http.HttpClient 写法，在 JDK 8 项目里编译不过
      （那是 JDK 11+ 的 API）。
      处理：用 HttpURLConnection（本机 examples/http-clients/Client.java 按 --release 8 编译通过），
      或 Spring 里用 RestTemplate。

坑 4：看到 Java 客户端「总耗时 3162 ms」就以为模型很慢。
      处理：看服务端返回的 latency_ms——同一请求只有 649.6 ms，剩下的是 JVM 启动与首次 JIT；
      这也说明「短连接的一次性脚本」不适合评估模型延迟。

坑 5：Vue 页面直连服务，被浏览器 CORS 拦掉。
      处理：开发期 devServer.proxy，生产期 nginx 同域反代（第 5.3 节），别用 allow_origins=["*"] 图省事。

坑 6：把 key 写进前端 JS 或直接提交进仓库。
      处理：key 只放环境变量 / .env.local（VUE_APP_LAYA_KEY）；本机已扫过仓库确认没有真实 key。

坑 7：探针在服务启动期间一直失败，误判成服务挂了。
      处理：preload 完成前端口根本不监听（实测缓存热 61.8 s、冷启约 170 s 才出现 "已 preload ..."），
      这是设计如此；探针失败即「未就绪」，不要据此重启。

坑 8：选项太多时服务返回 500（不是 422），且 criteria 会被静默截断。
      处理：单题选项 ≤ 10 个；先按第 3.3 节的 token 表算预算再定 schema。

坑 9：用强类型实体硬映射整棵响应树。
      处理：probabilities 的 key 是你自己定义的选项名，实体类只能写到 Map 一层；
      另注意 noul 题返回的是 Double（不是 Boolean），score 题返回的也是 Double（期望值）。

坑 10：中文请求落到了英文 checkpoint，结果惨不忍睹。
      处理：检查响应 routing.model——中文应落到 multilingual（实测 reason:
      "non-Latin script (han, 100% of letters); the English checkpoint cannot read it"）；
      必要时显式传 "model":"multilingual"，但要先确保它已 preload。
```

---

## 相关文档

- [[Laya完整教程]] — 模型原理、安装（含 torch 架构选择）、原语、路由、校准、token 预算、踩坑记录
- [[algorithm-engineer/README]] — 算法工程知识库入口（推理、评估、部署相关内容）
- [[16.2-模型服务]] — 自托管模型服务的通用部署方式（并发、显存、批处理），与本文第 6 章对照看
- [[16.3-推理优化]] — 推理延迟与吞吐优化（量化、批处理、KV cache）；Laya 没有 KV cache，但批处理思路通用
- [[Docker完整教程]] — 把这套服务容器化（端口映射、compose、镜像）的基础操作
- [[10.2-systemd]] — 本文第 2 章用到的 systemd 单元写法与排障
