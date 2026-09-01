---
title: Spring Boot 文件识别与 Apache Tika 详解
created: 2026-09-01
updated: 2026-09-01
type: integration
tags: [spring-boot, tika, 文件签名, magic-number, mime, 文件上传, 文本抽取, ocr]
---

> 整理日期：2026-09-01

## 目录

1. [概述](#1-概述)
2. [文件签名（魔数）基础](#2-文件签名魔数基础)
3. [Apache Tika 介绍](#3-apache-tika-介绍)
4. [环境搭建](#4-环境搭建)
5. [Tika 核心用法](#5-tika-核心用法)
6. [类似的库与替代方案](#6-类似的库与替代方案)
7. [应用场景实战](#7-应用场景实战)
8. [最佳实践与踩坑记录](#8-最佳实践与踩坑记录)
9. [参考链接](#9-参考链接)

---

## 1. 概述

### 1.1 文件识别要解决什么问题

服务端接收用户上传的文件时，第一件要做的事是搞清楚"这到底是个什么文件"。这不是一个多余的动作，它直接决定后续三件事：

1. **安全**：只允许图片的接口收到一个伪装成 .jpg 的可执行文件，就是一个直接的攻击面。类型校验做错，等于把解析器（PDF 解析、Office 解析、图片解码）暴露给攻击者，历史上多个高危漏洞都发生在"解析了不该解析的文件"上。
2. **业务正确**：不同类型走不同处理链路（图片走缩略图、PDF 走预览、Office 走文档转换）。类型判断错了，链路就错了。
3. **存储与分发**：对象存储的 Content-Type 影响浏览器行为。存储时存的 MIME 类型错误，下载时浏览器会直接下载而不是在线预览。

判断文件类型有四个层次的手段，可靠性从低到高：

| 手段 | 原理 | 可靠性 | 成本 |
|------|------|--------|------|
| 扩展名 | .jpg / .pdf | 极低，可随意伪造 | 零 |
| 请求头 Content-Type | multipart 表单里浏览器声明的类型 | 低，可随意伪造 | 零 |
| 文件签名（魔数） | 读文件头几个字节比对特征 | 高，伪造需理解格式 | 低 |
| 内容解析 | 用解析器真正解析一次，能解出来才算数 | 最高，防一切伪装 | 高 |

真实项目里正确做法是**组合**：魔数做主校验，内容解析做兜底，扩展名和 Content-Type 只做提示、不做依据。

### 1.2 Tika 是什么

Apache Tika 是 Apache 基金会的"内容检测与分析"工具包，它把两件事统一封装了：

- **检测（Detection）**：识别文件类型，支持 1000+ 种 MIME 类型，检测手段包括魔数、文件名、容器内部结构。
- **解析（Parsing）**：从 PDF、Office、OpenDocument、HTML、RTF、图片（含 EXIF）、音视频容器、压缩包、邮件等格式中提取纯文本和结构化元数据。

对 Java 后端来说，Tika 几乎是文件识别与文本抽取的默认答案：Lucene/Solr 的文档索引、Elasticsearch 的 ingest attachment processor、很多 CMS 的附件解析，底层用的都是 Tika。

### 1.3 本文范围

本文覆盖四块内容：

1. 文件签名（魔数）的原理与常用签名表，以及不依赖第三方库的手写实现；
2. Spring Boot 中集成 Apache Tika 做类型检测、文本解析、元数据提取、OCR；
3. 同类/替代库的横向对比（JDK 自带能力、Spring 自带能力、libmagic、停更的 Java 老库、各专项解析库、其他语言生态）；
4. 三个完整可运行的应用场景 + 最佳实践与踩坑记录。

---

## 2. 文件签名（魔数）基础

### 2.1 魔数是什么

文件签名（File Signature），俗称"魔数"（Magic Number），是文件格式规范中规定写在文件头部（少数写在尾部或固定偏移处）的一段特征字节序列。文件格式的设计者为了让识别程序能快速区分格式，约定每个合法文件必须以特定字节开头。

例子：所有 PDF 文件的前 4 个字节必然是 `25 50 44 46`，也就是 ASCII 字符 `%PDF`。识别程序只需要读前 4 个字节，就能以接近 100% 的置信度判断"这是个 PDF"——前提是文件不是伪造的。想伪造也不难（把任意文件头改成 `%PDF`），所以魔数识别挡的是"无心之失"和"低级伪造"，挡不住"专门构造的伪装文件"，后者要靠内容解析兜底。

魔数的优势：

- **快**：只需读文件头几十个字节，O(1) 时间，不依赖文件大小；
- **准**：只要格式规范没被违反，命中即正确；
- **不依赖环境**：不查操作系统、不查外部命令，纯字节比对，任何环境行为一致；
- **不需要解析器**：识别不了的内容（加密文件、损坏文件）也能识别"它声称是什么"。

局限：

- 部分格式（尤其是容器格式，如 docx、xlsx、jar）魔数相同，需要进一步看内部结构才能细分；
- 有的格式魔数在固定偏移处（如 TAR 的 ustar 在 257 字节处），需要跳读；
- 纯文本类格式（txt、csv、json、xml）没有强特征，只能靠内容启发式或文件名补充。

### 2.2 常用文件签名表

下表是开发中最常遇到的一批格式，识别时直接对照即可。十六进制列即文件开头的字节序列，ASCII 列是对应的可打印字符（`.` 表示不可打印）。

| 格式 | 十六进制（开头） | ASCII | 偏移说明 |
|------|------------------|-------|----------|
| JPEG | `FF D8 FF` | 无 | 头 3 字节；结尾另有 `FF D9` |
| PNG | `89 50 4E 47 0D 0A 1A 0A` | `.PNG....` | 头 8 字节，第 4-6 字节是 `PNG` |
| GIF | `47 49 46 38 37 61` 或 `47 49 46 38 39 61` | `GIF87a` / `GIF89a` | 头 6 字节 |
| BMP | `42 4D` | `BM` | 头 2 字节 |
| WEBP | `52 49 46 46 .. .. .. .. 57 45 42 50` | `RIFF....WEBP` | 0 偏移 `RIFF`，8 偏移 `WEBP` |
| TIFF | `49 49 2A 00` 或 `4D 4D 00 2A` | `II*.` / `MM.*` | 小端/大端两种 |
| ICO | `00 00 01 00` | 无 | 头 4 字节 |
| PDF | `25 50 44 46` | `%PDF` | 头 4 字节；结尾应有 `%%EOF` |
| ZIP（含 docx/xlsx/jar） | `50 4B 03 04` | `PK..` | 空 ZIP 是 `50 4B 05 06`，分卷是 `50 4B 07 08` |
| RAR | `52 61 72 21 1A 07 00` | `Rar!...` | 头 7 字节 |
| 7Z | `37 7A BC AF 27 1C` | `7z..'.` | 头 6 字节 |
| GZIP | `1F 8B` | 无 | 头 2 字节 |
| BZIP2 | `42 5A 68` | `BZh` | 头 3 字节 |
| XZ | `FD 37 7A 58 5A 00` | `.7zXZ.` | 头 6 字节 |
| ZLIB（png 压缩流等） | `78 01` / `78 5E` / `78 9C` / `78 DA` | 无 | 头 2 字节 |
| OLE2（老版 doc/xls/ppt） | `D0 CF 11 E0 A1 B1 1A E1` | 无 | 头 8 字节 |
| MP3（带 ID3v2 标签） | `49 44 33` | `ID3` | 无标签的 MPEG 帧头是 `FF FB`/`FF F3` 等 |
| MP4/M4A | `.. .. .. .. 66 74 79 70` | `....ftyp` | `ftyp` 在偏移 4 |
| WAV | `52 49 46 46 .. .. .. .. 57 41 56 45` | `RIFF....WAVE` | `WAVE` 在偏移 8 |
| AVI | `52 49 46 46 .. .. .. .. 41 56 49 20` | `RIFF....AVI ` | `AVI ` 在偏移 8 |
| FLAC | `66 4C 61 43` | `fLaC` | 头 4 字节 |
| OGG | `4F 67 67 53` | `OggS` | 头 4 字节 |
| SQLite 数据库 | `53 51 4C 69 74 65 20 66 6F 72 6D 61 74 20 33 00` | `SQLite format 3.` | 头 16 字节 |
| ELF 可执行文件 | `7F 45 4C 46` | `.ELF` | 头 4 字节 |
| Java class 文件 | `CA FE BA BE` | 无 | 头 4 字节 |
| Java 密钥库 jks | `FE ED FE ED` | 无 | 头 4 字节 |
| Mach-O（macOS） | `FE ED FA CE` / `CF FA ED FE` 等 | 无 | 四种魔数之一 |
| WASM | `00 61 73 6D` | `.asm` | 头 4 字节 |
| XML | `3C 3F 78 6D 6C`（`<?xml`） | `<?xml` | UTF-16 编码时是 `3C 00 3F 00` |
| HTML | `3C 68 74 6D 6C`（`<html`）或 `3C 21 44 4F 43`（`<!DOC`） | `<html` / `<!DOC` | 允许前导空白 |
| RTF | `7B 5C 72 74 66` | `{\rtf` | 头 5 字节 |
| PS/EPS | `25 21 50 53` | `%!PS` | 头 4 字节 |
| TAR | 偏移 257 处是 `75 73 74 61 72` | `ustar` | 固定偏移 257 |
| ISO 9660 光盘镜像 | 偏移 0x8001（32769）处是 `43 44 30 30 31` | `CD001` | 固定偏移 |

说明两点：

1. docx/xlsx/pptx、jar、apk、war、ear 本质上都是 ZIP，魔数都是 `PK..`。要区分它们，必须解包看内部结构（ZIP 里是否有 `[Content_Types].xml`、`META-INF/MANIFEST.MF` 等）。这正是 Tika 的"容器检测"（Container Detection）做的事，后面 5.5 节展开。
2. OLE2 魔数 `D0 CF 11 E0...` 是老版 Office（doc/xls/ppt 97-2003 格式）的特征，它同时也是 Outlook .msg 等一堆复合文档格式的特征，同样需要看内部流（stream）名才能细分。

### 2.3 用 Java 读文件头字节

不依赖任何第三方库，自己读文件头做比对，是理解整个体系的第一步。核心就两行：用 `RandomAccessFile` 或 `FileInputStream` 读前 N 字节，转成十六进制字符串。

```java
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;

public class FileHeaderReader {

    /** 读取输入流前 length 个字节，返回大写十六进制字符串（不满 length 时返回实际读到的部分） */
    public static String readHexHeader(InputStream in, int length) throws IOException {
        byte[] buf = new byte[length];
        int read = in.readNBytes(buf, 0, length);   // JDK 9+，读满或读到 EOF
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < read; i++) {
            sb.append(String.format("%02X", buf[i]));
        }
        return sb.toString();
    }

    /** 读取文件前 length 个字节的十六进制 */
    public static String readHexHeader(String filePath, int length) throws IOException {
        try (InputStream in = new FileInputStream(filePath)) {
            return readHexHeader(in, length);
        }
    }

    public static void main(String[] args) throws IOException {
        // 用法示例：输出 PDF 文件的头 8 字节，应为 255044462D312E ("%PDF-1.")
        String hex = readHexHeader("/tmp/sample.pdf", 8);
        System.out.println(hex);
    }
}
```

`readNBytes` 是 JDK 9 加入的方法，语义是"尽可能读满，读到 EOF 就返回实际数量"，比裸 `read(byte[])` 省去了循环处理"一次没读满"的麻烦。Spring Boot 3.x 基于 Java 17，可以直接用。

### 2.4 自研魔数匹配工具类

实际项目里如果不引入 Tika，手写一个针对白名单格式的匹配工具就够用。完整实现如下，支持：单段魔数、带通配字节的魔数（如 WEBP 中间 4 字节是文件大小，需跳过）、偏移匹配（如 TAR 的 ustar）。

```java
import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;

/**
 * 魔数（文件签名）匹配工具。
 *
 * 设计：每种格式定义为一个 Magic 规则，规则包含魔数字节数组和匹配偏移。
 * 规则表用十六进制字符串维护（生产上魔数表就是这么写的），
 * 两个字符的 ?? 表示通配字节（该位置不参与比对）。
 *
 * 注意：Java 的 byte[] 是基本类型数组，装不下 null，
 * 通配必须用 Byte[]（包装类型）表达。
 */
public class MagicMatcher {

    /** 单条魔数规则。bytes 里 null 表示通配。 */
    public record Magic(Byte[] bytes, int offset) {

        /** 便捷构造：偏移 0 */
        public Magic(Byte[] bytes) {
            this(bytes, 0);
        }

        boolean matches(byte[] header) {
            if (offset + bytes.length > header.length) {
                return false;   // 头部数据不够长，无法匹配
            }
            for (int i = 0; i < bytes.length; i++) {
                Byte b = bytes[i];
                if (b != null && header[offset + i] != b) {
                    return false;
                }
            }
            return true;
        }
    }

    /** 十六进制魔数字符串转 Byte[]。空格分隔，"??" 表示通配。 */
    private static Byte[] hex(String pattern) {
        String[] parts = pattern.trim().split("\s+");
        Byte[] out = new Byte[parts.length];
        for (int i = 0; i < parts.length; i++) {
            out[i] = "??".equalsIgnoreCase(parts[i]) ? null : (byte) Integer.parseInt(parts[i], 16);
        }
        return out;
    }

    /** 常用格式规则表。?? 表示通配。 */
    public static final Magic[] COMMON_MAGICS = {
            new Magic(hex("89 50 4E 47 0D 0A 1A 0A")),                        // PNG
            new Magic(hex("FF D8 FF")),                                       // JPEG
            new Magic(hex("47 49 46 38 37 61")),                              // GIF87a
            new Magic(hex("47 49 46 38 39 61")),                              // GIF89a
            new Magic(hex("42 4D")),                                          // BMP
            new Magic(hex("52 49 46 46 ?? ?? ?? ?? 57 45 42 50")),            // WebP(RIFF....WEBP)
            new Magic(hex("25 50 44 46")),                                    // PDF
            new Magic(hex("50 4B 03 04")),                                    // ZIP 类
            new Magic(hex("52 61 72 21 1A 07 00")),                           // RAR
            new Magic(hex("37 7A BC AF 27 1C")),                              // 7z
            new Magic(hex("1F 8B")),                                          // GZIP
            new Magic(hex("D0 CF 11 E0 A1 B1 1A E1")),                        // OLE2
            new Magic(hex("49 44 33")),                                       // MP3(ID3)
            new Magic(hex("00 00 00 ?? 66 74 79 70")),                        // MP4(ftyp 在偏移 4)
            new Magic(hex("53 51 4C 69 74 65 20 66 6F 72 6D 61 74 20 33 00")),// SQLite
            new Magic(hex("7F 45 4C 46")),                                    // ELF
            new Magic(hex("CA FE BA BE")),                                    // Java class
            new Magic(hex("FE ED FE ED")),                                    // jks
            new Magic(hex("75 73 74 61 72"), 257),                            // TAR(偏移 257)
    };

    /** 读取输入流头部最多 maxLen 字节（自动 mark/reset 保护，不消费流） */
    public static byte[] readHeader(InputStream in, int maxLen) throws IOException {
        if (!in.markSupported()) {
            in = new BufferedInputStream(in);
        }
        in.mark(maxLen);
        byte[] buf = new byte[maxLen];
        int read = in.readNBytes(buf, 0, maxLen);
        in.reset();
        return read < maxLen ? Arrays.copyOf(buf, read) : buf;
    }

    /** 判断文件是否命中任一规则，返回规则描述（无命中返回 null） */
    public static String detect(InputStream in, int headerLen) throws IOException {
        byte[] header = readHeader(in, headerLen);
        for (Magic m : COMMON_MAGICS) {
            if (m.matches(header)) {
                return describe(m);
            }
        }
        return null;
    }

    private static String describe(Magic m) {
        // 简化：直接用规则的下标做描述，生产环境应换成格式名枚举
        return "magic#" + Arrays.asList(COMMON_MAGICS).indexOf(m);
    }

    public static void main(String[] args) throws IOException {
        try (InputStream in = new FileInputStream(new File(args[0]))) {
            String type = detect(in, 512);
            System.out.println(type == null ? "unknown" : type);
        }
    }
}
```

三个值得注意的实现细节：

1. **`mark/reset` 保护输入流**：`readHeader` 读完头部后把流复位，调用方还能继续读剩余内容。否则"读头"这个动作会消费掉流的开头，后面真正处理文件时读不到数据。`MultipartFile.getInputStream()` 返回的流不一定支持 mark，所以统一包一层 `BufferedInputStream`。
2. **通配字节**：WebP 的 `RIFF` 后 4 字节是文件长度，是动态值，用 `null` 跳过。这比"截断到魔数前缀"的偷懒写法准确得多——直接比对 `RIFF....WEBP` 整段，能顺带排除"假的 RIFF"。
3. **偏移匹配**：TAR 的 ustar 标记在 257 字节处，规则里直接给 offset，头部缓冲区读 512 字节即可覆盖。

### 2.5 魔数识别的边界

手写魔数匹配能覆盖 90% 的上传校验场景，但有三个边界必须知道：

1. **容器格式细分不了**：docx 和 zip 魔数相同，`PK..` 命中后无法区分。要细分就得解 ZIP 看 `[Content_Types].xml`，工作量陡增——这就是用 Tika 的理由。
2. **纯文本无特征**：txt、csv、json、log、yaml 的文件头都是任意字符，魔数匹配永远命中不了。这类文件要么接受"unknown 放行"，要么靠文件名/内容启发式（比如尝试按 JSON 解析）。
3. **伪装文件挡不住**：把病毒样本前面拼上 `%PDF` 魔数，手写匹配会判定为 PDF。所以"上传文件只允许图片"这种需求，光靠魔数不够，正规做法是魔数识别 + 真实解析双保险（Tika 的 parse 能直接把伪装 PDF 解析失败暴露出来）。

---

## 3. Apache Tika 介绍

### 3.1 核心能力

| 能力 | 说明 | 典型用途 |
|------|------|----------|
| MIME 类型检测 | 魔数 + 文件名 + 容器结构综合判定，支持 1000+ 类型 | 上传校验、文件分类 |
| 文本抽取 | 从 PDF/Office/HTML/邮件等抽取纯文本 | 全文检索索引、文档预览 |
| 元数据提取 | PDF 作者/页数、图片 EXIF/GPS、音视频时长码率、Office 文档属性 | 资源管理、信息采集 |
| 语言检测 | 识别文本语言（需单独模块） | 内容分类 |
| OCR | 扫描件/图片转文字（需 Tesseract + tika-parser-ocr-module） | 票据识别、扫描件检索 |
| 嵌入式文件 | 解出文档里内嵌的附件、图片 | 深度内容分析 |

### 3.2 架构：两个核心接口

Tika 的体系可以用两个接口概括：

**Detector（检测器）——负责回答"这是什么类型"**

```java
MediaType detect(InputStream input, Metadata metadata) throws IOException;
```

所有检测手段都实现这个接口，由 `DefaultDetector` 用 ServiceLoader 汇总，按优先级依次尝试：

1. **MagicDetector**：读文件头字节匹配 tika-mimetypes.xml 里的魔数规则（Freedesktop MIME-info 格式，Tika 在其上做了扩展）；
2. **XML 根元素检测**：文件头是 XML 时，解析根元素进一步细分（`<html>`、`<svg>`、`<project>` 各自对应不同 MIME）；
3. **NameDetector**：用文件名（`TikaCoreProperties.RESOURCE_NAME_KEY`）补充，比如魔数只能判定"文本文件"，文件名 `data.csv` 让它精化到 `text/csv`；
4. **ContainerDetector**（需要 parsers 模块）：ZIP/OLE2/RIFF 等容器格式，打开容器看内部结构，区分 docx/xlsx/zip、doc/xls、wav/avi；
5. **TextDetector**：以上都失败时，根据文本内容的字符分布判断是二进制还是文本。

**Parser（解析器）——负责回答"里面写了什么"**

```java
void parse(InputStream stream, ContentHandler handler, Metadata metadata, ParseContext context) throws ...;
```

每种格式一个 Parser 实现（PDFParser、OOXMLParser、OLE2Parser、HTMLParser、ImageParser……），把原始字节流变成标准化的 `ContentHandler` 事件（类似 SAX 的事件模型）。`BodyContentHandler` 把这些事件收集成纯文本字符串，这就是 `parseToString` 的本质。

### 3.3 版本选择

| 分支 | Java 要求 | 状态 | 说明 |
|------|-----------|------|------|
| 1.x | Java 7/8 | 已停止维护 | 老项目遗留 |
| 2.x | Java 8 | 2025-04 已 EOL | 2.x 分支停止支持 |
| 3.x | Java 11+ | 当前主流稳定分支 | 3.3.x 为最新小版本，Spring Boot 3.x（Java 17）直接可用 |
| 4.x | 待确认（发布说明为准） | 4.0.0 于 2026-08 发布 | 新项目可评估，3.x 更稳 |

结论：**Spring Boot 2.x（Java 8）用 Tika 2.9.x；Spring Boot 3.x（Java 17）用 Tika 3.3.x**。4.0.0 刚发布，等小版本沉淀再上不迟。

### 3.4 tika-core 与 tika-parsers-standard-package

这是 Tika 最容易搞混的一点。两个构件分工：

- **tika-core**：只有接口和核心类（Tika facade、Detector、MimeTypes、Metadata、TikaInputStream、AutoDetectParser 的定义），**不包含任何具体 Parser 实现**。只做"类型检测"（detect）用 core 就够了。
- **tika-parsers-standard-package**：聚合了 PDFBox、POI、jsoup 等一堆第三方解析库的 Parser 实现，体积大、传递依赖多。做"内容解析"（parseToString）必须引入它。

一个常见误区：只引了 tika-core 就调 `parseToString`，运行时报 `No parser available for application/pdf`——因为根本没有能解析 PDF 的 Parser 实现。

```text
只用检测：tika-core 即可，几 MB
检测 + 解析：tika-core + tika-parsers-standard-package，几十 MB（含传递依赖）
检测 + 解析 + OCR：再加 tika-parser-ocr-module + 系统安装 Tesseract
```

---

## 4. 环境搭建

### 4.1 Maven 依赖

Spring Boot 3.x + Java 17 的标准组合，Tika 用 3.3.x：

```xml
<dependency>
    <groupId>org.apache.tika</groupId>
    <artifactId>tika-core</artifactId>
    <version>3.3.2</version>
</dependency>

<!-- 需要文本解析/容器检测时再加这个（体积大，按需引入） -->
<dependency>
    <groupId>org.apache.tika</groupId>
    <artifactId>tika-parsers-standard-package</artifactId>
    <version>3.3.2</version>
    <type>pom</type>
</dependency>

<!-- 注意：tika-parsers-standard-package 已传递包含 tika-parser-ocr-module，
     上一步引了它就不需要再单独引；只有"只用 tika-core + 单加 OCR"才需要这个 -->
<dependency>
    <groupId>org.apache.tika</groupId>
    <artifactId>tika-parser-ocr-module</artifactId>
    <version>3.3.2</version>
</dependency>
```

两个注意点：

1. `tika-parsers-standard-package` 的 `<type>pom</type>` 是官方推荐写法（4.x 官方文档同样如此），它本身是个聚合 pom，靠它把各 parser 传递引入；
2. Tika 官方提供 BOM（`org.apache.tika:tika-bom`），多模块项目用 BOM 统一版本更干净：

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.apache.tika</groupId>
            <artifactId>tika-bom</artifactId>
            <version>3.3.2</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

### 4.2 Gradle 依赖

```groovy
dependencies {
    implementation 'org.apache.tika:tika-core:3.3.2'
    // 解析功能按需
    implementation 'org.apache.tika:tika-parsers-standard-package:3.3.2'
}
```

### 4.3 配置类与 Bean

Tika 的 `Tika` facade 和 `TikaConfig` 都是线程安全的，全局单例即可，不需要每次请求 new。在 Spring Boot 里注册成 Bean：

```java
import org.apache.tika.Tika;
import org.apache.tika.config.TikaConfig;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class TikaConfigBean {

    /**
     * Tika 门面：detect / parseToString 一行调用。
     * setMaxStringLength 限制文本抽取的最大字符数，防止恶意大文件把内存打爆。
     */
    @Bean
    public Tika tika() {
        Tika tika = new Tika();
        tika.setMaxStringLength(10_000_000);   // 单文件最多抽 1000 万字符
        return tika;
    }

    /** TikaConfig：持有默认 MimeTypes 与 Detector 链，解析底层细节时用 */
    @Bean
    public TikaConfig tikaConfig() {
        return TikaConfig.getDefaultConfig();
    }
}
```

注意 `TikaConfig.getDefaultConfig()` 内部缓存了默认配置，多线程共享安全，不需要每次 new。

### 4.4 application.yml

Tika 本身不需要任何配置项，只要依赖在 classpath 上就能工作。两个与集成相关的可选项：

```yaml
spring:
  servlet:
    multipart:
      max-file-size: 20MB          # 上传单文件上限
      max-request-size: 50MB       # 一次请求总上限
```

OCR 场景如果 Tesseract 不在 PATH 里，可以通过系统属性 `tesseract.path` 指定安装路径（见 5.7 节）。

---

## 5. Tika 核心用法

### 5.1 类型检测：Tika facade

最常用、最省事的方式。`org.apache.tika.Tika` 提供了覆盖常见输入形态的 detect 重载：

```java
import org.apache.tika.Tika;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.InputStream;

public class TikaDetectDemo {

    private final Tika tika;

    public TikaDetectDemo(Tika tika) {
        this.tika = tika;
    }

    /** 按文件内容检测（读魔数），与扩展名无关 */
    public String detectByFile(File file) throws Exception {
        return tika.detect(file);
    }

    /** 按输入流检测 */
    public String detectByStream(InputStream in) throws Exception {
        return tika.detect(in);
    }

    /** 输入流 + 文件名：魔数为主，文件名辅助精化（如 text/plain 精化为 text/csv） */
    public String detectWithName(InputStream in, String fileName) throws Exception {
        return tika.detect(in, fileName);
    }

    /** 只按文件名检测（不读内容，仅查扩展名映射表） */
    public String detectByNameOnly(String fileName) {
        return tika.detect(fileName);
    }

    /** Spring 上传文件场景：一行搞定 */
    public String detectMultipart(MultipartFile file) throws Exception {
        try (InputStream in = file.getInputStream()) {
            return tika.detect(in, file.getOriginalFilename());
        }
    }
}
```

返回的是 MIME 类型字符串，如 `image/png`、`application/pdf`、`application/vnd.openxmlformats-officedocument.wordprocessingml.document`（docx）。注意 docx 的 MIME 特别长，是 OOXML 的规范命名，不要试图手写字符串匹配，用 `MediaType` 类型或按前缀判断。

### 5.2 底层：Detector 链与 MimeTypes

要控制检测行为（比如只看魔数、忽略文件名），用底层 API：

```java
import org.apache.tika.config.TikaConfig;
import org.apache.tika.detect.Detector;
import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.mime.MediaType;
import org.apache.tika.mime.MimeTypes;

import java.io.File;

public class DetectorChainDemo {

    /**
     * 用默认 Detector 链检测。
     * 传入 TikaInputStream.get(file, metadata) 时，metadata 自动带上资源名，
     * NameDetector 才有机会参与。
     */
    public MediaType detectWithChain(TikaConfig config, File file) throws Exception {
        Detector detector = config.getDetector();
        Metadata metadata = new Metadata();
        try (TikaInputStream tis = TikaInputStream.get(file, metadata)) {
            return detector.detect(tis, metadata);
        }
    }

    /**
     * 只看魔数：直接用 MimeTypes 的魔数检测。
     * 注意这种写法不做文件名精化，文本类文件会得到 text/plain 而非 text/csv。
     */
    public MediaType detectMagicOnly(MimeTypes mimeTypes, File file) throws Exception {
        Metadata metadata = new Metadata();
        try (TikaInputStream tis = TikaInputStream.get(file, metadata)) {
            return mimeTypes.detect(tis, metadata);
        }
    }

    public static void main(String[] args) throws Exception {
        TikaConfig config = TikaConfig.getDefaultConfig();
        MediaType type = config.getDetector().detect(
                TikaInputStream.get(new File(args[0])), new Metadata());
        System.out.println(type.toString());
    }
}
```

检测优先级（官方文档明示）：**先魔数，再 XML 根元素，再文件名，最后 Content-Type 元数据**。文件名只在魔数判定为文本类时做精化，不会推翻魔数结论。

### 5.3 文本解析：parseToString

把 PDF、Office、HTML 等内容抽成纯文本，是全文检索场景的核心操作。

```java
import org.apache.tika.Tika;
import org.apache.tika.exception.TikaException;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.parser.AutoDetectParser;
import org.apache.tika.sax.BodyContentHandler;
import org.apache.tika.sax.WriteOutContentHandler;
import org.xml.sax.SAXException;

import java.io.IOException;
import java.io.InputStream;

public class TikaParseDemo {

    private final Tika tika;

    public TikaParseDemo(Tika tika) {
        this.tika = tika;
    }

    /** 最简方式：parseToString，返回纯文本字符串 */
    public String parseToString(InputStream in) throws IOException, TikaException {
        try (in) {
            return tika.parseToString(in);
        }
    }

    /**
     * 底层方式：AutoDetectParser + BodyContentHandler。
     * 好处：能拿到 Metadata；能精确控制文本量上限。
     */
    public String parseWithMetadata(InputStream in, Metadata metadata)
            throws IOException, SAXException, TikaException {
        AutoDetectParser parser = new AutoDetectParser();
        // 第二个参数是写上限，超过抛 TooLongContentException：
        // -1 表示不限制（危险），默认 100000，这里设 500 万
        BodyContentHandler handler = new BodyContentHandler(5_000_000);
        ParseContext context = new ParseContext();
        parser.parse(in, handler, metadata, context);
        return handler.toString();
    }

    /**
     * 把解析结果写向任意 ContentHandler。
     * WriteOutContentHandler 支持按字符数硬限流，适合超大文档降级处理。
     */
    public void parseToWriter(InputStream in, WriteOutContentHandler writer) throws Exception {
        AutoDetectParser parser = new AutoDetectParser();
        parser.parse(in, writer, new Metadata(), new ParseContext());
    }
}
```

`BodyContentHandler(int writeLimit)` 是防 OOM 的第一道闸：解析器往 handler 里写的内容超过上限就抛 `TooLongContentException`，调用方捕获后降级（比如只存摘要）。生产环境务必设置，不要用无参构造（默认 10 万字符其实也不算大，正文超长文档会直接失败——需要按业务调）。

### 5.4 元数据提取

同一份输入，解析时把 `Metadata` 对象传进去，解析完后里面就有结构化元数据了：

```java
import org.apache.tika.Tika;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.PagedText;
import org.apache.tika.metadata.TIFF;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.metadata.XMPDM;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;

public class TikaMetadataDemo {

    private final Tika tika;

    public TikaMetadataDemo(Tika tika) {
        this.tika = tika;
    }

    public Metadata extractMetadata(File file) throws Exception {
        Metadata metadata = new Metadata();
        // parseToString(InputStream, Metadata) 是 facade 支持的签名，
        // File 需要先转成流；内部实现就是 parse + BodyContentHandler
        try (InputStream in = new FileInputStream(file)) {
            tika.parseToString(in, metadata);
        }
        return metadata;
    }

    public void printCommonMetadata(Metadata metadata) {
        // 通用属性
        System.out.println("Title      = " + metadata.get(TikaCoreProperties.TITLE));
        System.out.println("Author     = " + metadata.get(TikaCoreProperties.CREATOR));
        System.out.println("Created    = " + metadata.get(TikaCoreProperties.CREATED));
        System.out.println("Modified   = " + metadata.get(TikaCoreProperties.MODIFIED));
        // 图片：宽高键是 tiff:ImageWidth / tiff:ImageLength（Tika 3.x 里"高度"不叫 ImageHeight）
        System.out.println("ImageW     = " + metadata.get(TIFF.IMAGE_WIDTH));
        System.out.println("ImageH     = " + metadata.get(TIFF.IMAGE_LENGTH));
        // GPS：键是 geo:lat / geo:long（不是 "GPS Latitude"）
        System.out.println("GPS        = " + metadata.get(TikaCoreProperties.LATITUDE)
                + "," + metadata.get(TikaCoreProperties.LONGITUDE));
        // PDF 页数：xmpTPg:NPages
        System.out.println("PageCount  = " + metadata.get(PagedText.N_PAGES));
        // 音视频时长
        System.out.println("Duration   = " + metadata.get(XMPDM.DURATION));
    }
}
```

元数据键用 `org.apache.tika.metadata.*` 的常量类引用（`TikaCoreProperties`、`TIFF`、`PagedText`、`XMPDM`），不要硬编码裸字符串——Tika 3.x 里图片尺寸键是 `tiff:ImageWidth`/`tiff:ImageLength`、GPS 键是 `geo:lat`/`geo:long`，与 2.x 时代的旧键名（`Image Width`/`GPS Latitude`）不一样，写死字符串容易在升级后静默拿到 null。

### 5.5 容器格式检测

5.2 节说的"魔数 + 文件名"链，有一个著名盲区：**docx 和 zip 的魔数都是 `PK..`，只靠 core 分不开**。Tika 的解法是 ContainerDetector：检测到 ZIP/OLE2 魔数后，打开容器看内部结构。

- **ZIP 容器**（docx/xlsx/pptx/odt/jar/apk）：解包看有没有 `[Content_Types].xml`（OOXML 系列）、`mimetype`（ODF 系列）、`META-INF/MANIFEST.MF`（jar），据此细分；
- **OLE2 容器**（老版 doc/xls/ppt/msg）：看内部流名（`WordDocument`、`Workbook`、`PowerPoint Document`、`__properties_version1.0` 等）细分。

容器检测的实现分布在 standard-package 聚合的各模块中（ZIP 检测在 `tika-parser-zip-commons` 的 `ZipContainerDetector`，OLE2 检测在 `tika-parser-microsoft-module` 的 `POIFSContainerDetector`），tika-core 只有接口没有实现。所以：

```text
只引 tika-core：  detect(docx) -> application/zip     （只能到 ZIP 这层）
引了 parsers：    detect(docx) -> application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

这是"检测到底要不要引 parsers 模块"的关键决策点：如果业务需要区分 Office 文档类型，就必须引 parsers。

### 5.6 自定义 MIME 类型

业务内部格式（比如自己的 .biz 文件头是 `BIZ1`）想让 Tika 认识，两种方式：

**方式一：classpath 根目录放 custom-mimetypes.xml**（Tika 3.x 的加载位置，2.x 是 `org/apache/tika/mime/` 下）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mime-info>
    <mime-type type="application/x-biz">
        <glob pattern="*.biz"/>
        <magic priority="50">
            <match value="BIZ1" type="string" offset="0"/>
        </magic>
    </mime-type>
</mime-info>
```

放在 `src/main/resources/custom-mimetypes.xml`，Tika 自动加载，`detect` 就能识别 `.biz` 文件。`priority` 越高越优先；`type="string"` 是 ASCII 字符串匹配，也支持 `type="byte"` 的十六进制序列。

**方式二：编程式注册（注意公开 API 的限制）**

Tika 的公开 API 里，魔数的增删**没有**对外开放——`MimeType.addMagic` 是包私有方法，运行时动态加魔数规则做不到，魔数规则只能走 custom-mimetypes.xml。公开 API 能做的只有两件事：

1. 注册/追加**扩展名**映射（`MimeTypes.addPattern`），适合"同一个 MIME 类型追加业务后缀"的场景；
2. 用 `MimeType.matchesMagic(byte[])` 对已注册类型的魔数做运行时校验。

```java
import org.apache.tika.mime.MimeType;
import org.apache.tika.mime.MimeTypeException;
import org.apache.tika.mime.MimeTypes;

import java.io.IOException;
import java.io.InputStream;

public class CustomMimeRegister {

    /**
     * 给已有 MIME 类型追加扩展名映射。
     * 注意：addPattern 只影响"按文件名检测"，不影响魔数检测。
     */
    public MimeTypes registerPattern() throws MimeTypeException {
        MimeTypes mimeTypes = MimeTypes.getDefaultMimeTypes();
        MimeType biz = mimeTypes.forName("application/x-biz");
        mimeTypes.addPattern(biz, "*.biz");
        return mimeTypes;
    }

    /** 对已注册类型做运行时魔数校验（读文件头前 4 字节比对 BIZ1） */
    public boolean matchesBizMagic(InputStream in) throws IOException, MimeTypeException {
        byte[] header = in.readNBytes(4);
        return MimeTypes.getDefaultMimeTypes()
                .forName("application/x-biz")
                .matchesMagic(header);
    }
}
```

如果确实需要"规则存数据库、运行时加载"的动态魔数，正确做法不是魔数注册，而是自己实现一个 `Detector`（见 7.3 场景三的自定义检测器），把业务规则写进 detect 逻辑里。

### 5.7 OCR：扫描件与图片转文字

Tika 的 OCR 能力封装的是 Tesseract。三步：

1. **系统安装 Tesseract**：

```bash
# Ubuntu/Debian
apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
# 需要中文识别就装 chi-sim 语言包；不装则只认英文

# 验证
tesseract --version
```

2. **引入 OCR 模块**（见 4.1 节的第三个依赖 `tika-parser-ocr-module`）；
3. **配置 Tesseract 路径**（不在 PATH 时）：

```java
import org.apache.tika.parser.ocr.TesseractOCRConfig;
import org.apache.tika.parser.ocr.TesseractOCRParser;
import org.apache.tika.parser.ParseContext;

public class OcrDemo {

    public ParseContext buildOcrContext() {
        // 识别参数在 Config 上
        TesseractOCRConfig config = new TesseractOCRConfig();
        config.setLanguage("chi_sim+eng");           // 中文+英文
        config.setTimeoutSeconds(30);                 // 单张超时秒数
        config.setMaxFileSizeToOcr(10 * 1024 * 1024); // 超过 10MB 不 OCR

        // tesseract 可执行文件路径在 Parser 上（注意不是在 Config 上）
        TesseractOCRParser parser = new TesseractOCRParser();
        parser.setTesseractPath("/usr/bin/");

        ParseContext context = new ParseContext();
        context.set(TesseractOCRConfig.class, config);
        context.set(TesseractOCRParser.class, parser);
        return context;
    }
}
```

OCR 在 Tesseract 安装到位时默认**启用**（`getSupportedTypes` 里 `hasTesseract && !skipOcr` 即生效），不需要额外开关；两种情况下不 OCR：系统里没有 tesseract 可执行文件、或显式 `config.setSkipOcr(true)`。注意：OCR 是重型操作，单张图可能几秒到几十秒，务必走异步任务，别在请求线程里同步做；另外如果 `setLanguage` 指定了系统没装的语言包，解析时 `checkInitialization` 会直接抛 `TikaConfigException`。

### 5.8 命令行与独立服务

不写代码也能用 Tika：

```bash
# tika-app：命令行工具
java -jar tika-app-3.3.2.jar --text document.pdf     # 抽文本到 stdout
java -jar tika-app-3.3.2.jar --metadata document.pdf # 只输出元数据
java -jar tika-app-3.3.2.jar --detect document.pdf   # 只输出 MIME 类型

# tika-server：REST 服务（默认 9998 端口）
java -jar tika-server-standard-3.3.2.jar
curl -T document.pdf http://localhost:9998/tika       # PUT 上传，返回抽出的文本
curl -T document.pdf -H "Accept: application/json" http://localhost:9998/meta
```

架构上把 tika-server 部署成独立进程，业务服务通过 HTTP 调用，好处是：解析器的内存爆炸、崩溃不影响主服务（解析在独立 JVM 里），也方便多语言服务共用。代价是多一个进程要运维。中小项目直接用库内嵌即可，这个方案留给"解析量很大/需要隔离"的场景。

---

## 6. 类似的库与替代方案

### 6.1 方案总览

| 方案 | 定位 | 维护状态 | 适用场景 |
|------|------|----------|----------|
| Apache Tika | 检测 + 解析一站式 | 活跃（Apache 顶级项目） | 通用首选 |
| JDK Files.probeContentType | 检测（扩展名为主） | JDK 自带 | 兜底、不依赖三方 |
| JDK URLConnection.guessContentTypeFromStream | 检测（读流头） | JDK 自带，覆盖极少 | 基本不用 |
| Spring MediaTypeFactory | 检测（扩展名映射） | Spring Web 自带 | 已知文件名、无需读内容 |
| libmagic / file 命令 | 检测（系统级魔数库） | 活跃（开源标准） | 服务器本地、Linux 环境 |
| JMimeMagic | 检测（Java） | 停更多年 | 老项目遗留 |
| MimeUtil (eu.medsea) | 检测（Java） | 停更多年 | 老项目遗留 |
| Apache POI | Office 解析 | 活跃 | 只处理 Office，且要细粒度 API |
| Apache PDFBox | PDF 解析 | 活跃 | 只处理 PDF，要细粒度 API |
| metadata-extractor | 图片元数据 | 活跃 | 只取图片 EXIF/GPS |
| jsoup | HTML 解析 | 活跃 | 只处理 HTML |
| tika-server | Tika 的 HTTP 封装 | 随 Tika | 解析隔离/多语言共用 |

### 6.2 JDK 自带：Files.probeContentType

```java
import java.nio.file.Files;
import java.nio.file.Path;

public class JdkProbeDemo {

    public String probe(Path path) {
        try {
            // 返回 MIME 类型，无法判定时返回 null
            return Files.probeContentType(path);
        } catch (Exception e) {
            return null;
        }
    }
}
```

原理：调用 `FileTypeDetector` SPI。JDK 默认实现（`DefaultFileTypeDetector`）基本只按**扩展名**查内置小表，Linux 上很多格式返回 null，Windows 上依赖注册表。它不会读文件内容，所以伪造扩展名照样骗过它。可以作为"先试系统、不行再说"的兜底，但不能当安全校验。

补充：JDK 允许自定义 `FileTypeDetector`（实现类 + `META-INF/services` 注册）来接管 `probeContentType`，但注册是进程级的，覆盖全局行为，慎用。

### 6.3 JDK 自带：URLConnection.guessContentTypeFromStream

```java
import java.io.InputStream;
import java.net.URLConnection;

public class JdkGuessDemo {

    public String guess(InputStream in) throws Exception {
        // 只能识别极少数格式：HTML/XML/GIF/JPEG/PNG 等
        return URLConnection.guessContentTypeFromStream(in);
    }
}
```

内部走 ContentHandler 工厂，能识别的格式非常有限（就是上面那几种），且实现不可配置。理解魔数原理后看一眼就知道它做不了正经的类型校验，新代码不建议依赖。

### 6.4 Spring 自带：MediaTypeFactory

spring-web 提供的扩展名映射工具，内部读 `org/springframework/http/mime.types` 资源：

```java
import org.springframework.http.MediaType;
import org.springframework.http.MediaTypeFactory;

import java.util.Optional;

public class SpringMediaTypeDemo {

    /** 按文件名推断，返回 Optional.empty 表示未知 */
    public Optional<MediaType> fromFileName(String fileName) {
        return MediaTypeFactory.getMediaType(fileName);
    }
}
```

覆盖常见类型（图片、Office、音视频、压缩包都有），纯扩展名匹配、不读内容。适合"已知文件名、只需要补一个 Content-Type 头"的场景，比如文件下载接口里根据文件名设置 `Content-Disposition` 和 `Content-Type`。安全校验不要用它。

### 6.5 libmagic / file 命令

`file` 命令背后的库，Linux 系统自带：

```bash
file -b --mime-type /tmp/sample.pdf   # 输出 application/pdf
```

Java 侧没有官方绑定，常见做法是 `ProcessBuilder` 调用 `file` 命令，或者引入 JNI 绑定库。优点是识别规则库极其庞大（/usr/share/misc/magic），缺点是依赖系统环境：Docker 镜像要装 `file` 包，跨平台（Windows/macOS）行为不一致。与 Tika 相比，Tika 是纯 Java 跨平台，更适合 Java 服务。

### 6.6 停更的 Java 老库：JMimeMagic 与 MimeUtil

这两个是 Tika 出现之前 Java 生态的检测库，都处于停更状态，遇到老项目代码里还有它们时知道是怎么回事即可：

- **JMimeMagic**（`net.sf.jmimemagic:jmimemagic`）：基于魔数的检测库，最后一次发布在 2018 年前后，多年未更新，新的文件格式（WebP 之后的格式）识别不全，也没有文本解析能力。
- **MimeUtil**（`eu.medsea.mimeutil:mime-util`）：同样是魔数 + 扩展名检测，停更更早（2016 年左右），GPL/LGPL 双协议授权，部分用法对商用有约束，新项目不要选。

选型结论：**只要不是历史包袱，检测统一用 Tika**。它规则库最大、维护最活跃、唯一同时解决"检测 + 解析"两个问题。

### 6.7 专项解析库

Tika 的 Parser 底层就是包了一层这些库。如果你的业务只处理一种格式、且需要这些库独有的细粒度 API，可以直接用专项库：

| 库 | 格式 | Tika 内的角色 |
|----|------|---------------|
| Apache PDFBox | PDF | PDFParser 的底层 |
| Apache POI | Office（doc/xls/ppt 与 OOXML） | OOXMLParser / OLE2Parser 的底层 |
| metadata-extractor (com.drew) | 图片 EXIF/XMP/GPS | 部分图片元数据的来源 |
| jsoup | HTML | JSoupParser 的底层（Tika 3.x 起 HTML 解析用 jsoup 替代了 TagSoup） |

直接引专项库 vs 引 Tika 的取舍：

```text
只要 PDF 文本 -> 引 PDFBox，API 更直接
要 PDF + Word + 图片一起处理 -> 引 Tika parsers，一个入口全搞定
要"改 PDF 内容/生成 PDF" -> 必须直接引 PDFBox（Tika 只读不写）
```

Tika 只做"读"，不做"写"。生成/编辑 PDF、操作 Excel 单元格这类需求，Tika 帮不上忙，该用 PDFBox/POI 本体。

### 6.8 其他语言生态

非 Java 服务的参考（原理相同，都是魔数匹配）：

| 语言 | 库 | 说明 |
|------|-----|------|
| Python | `python-magic` | libmagic 绑定，等同于 file 命令 |
| Python | `filetype` | 纯 Python 魔数库，轻量无依赖 |
| Node.js | `file-type` | 纯 JS 魔数检测，npm 生态事实标准 |
| Go | `h2non/filetype` | 纯 Go 魔数检测 |
| C | `libmagic` | 一切魔数库的源头 |

### 6.9 选型建议

结合 2~6 节，给一个务实的决策路径：

```text
需求：上传接口要限制文件类型
  -> 引 tika-core，detect 校验白名单（够用且轻）
  -> 需求更严（防伪装文件）-> 加 tika-parsers-standard-package，parse 一次做真实验证
  -> 需要区分 docx/xlsx/pptx -> 必须引 parsers（容器检测）
需求：全文检索 / 文档预览的文本抽取
  -> 引 parsers，parseToString + BodyContentHandler 限流
需求：只补下载响应头
  -> Spring MediaTypeFactory 就够了，别引 Tika
需求：扫描件 OCR
  -> tika-parser-ocr-module + Tesseract，异步执行
```

---
## 7. 应用场景实战

### 7.1 场景一：上传文件类型白名单校验

需求：头像上传接口只允许 PNG/JPEG/GIF/WebP 图片。校验链路分三层，缺一不可：

1. 大小与数量限制（Spring 配置 + 代码二次校验）；
2. 魔数检测（Tika detect，不看扩展名）——挡掉"把 exe 改名成 .png"的常见操作；
3. 图片解码验证（ImageIO 真实解码）——挡掉"文件头拼了 PNG 魔数的伪造文件"。

```java
import org.apache.tika.Tika;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.InputStream;
import java.util.Set;

@Service
public class ImageUploadValidator {

    private static final Set<String> ALLOWED_TYPES = Set.of(
            "image/png", "image/jpeg", "image/gif", "image/webp");

    private static final long MAX_SIZE = 5 * 1024 * 1024;   // 5MB

    private final Tika tika;

    public ImageUploadValidator(Tika tika) {
        this.tika = tika;
    }

    /**
     * 校验上传文件，通过返回规范化后的 MIME 类型，失败抛 IllegalArgumentException。
     */
    public String validate(MultipartFile file) throws Exception {
        // 第 0 层：基础参数
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("文件不能为空");
        }
        if (file.getSize() > MAX_SIZE) {
            throw new IllegalArgumentException("图片不能超过 5MB");
        }

        // 第 1 层：魔数检测（核心）。文件名只作为辅助提示传给 Tika，
        // 但白名单判断只看 detect 结果，不看扩展名。
        String mime;
        try (InputStream in = file.getInputStream()) {
            mime = tika.detect(in, file.getOriginalFilename());
        }
        if (!ALLOWED_TYPES.contains(mime)) {
            throw new IllegalArgumentException("不支持的图片类型: " + mime);
        }

        // 第 2 层：真实解码验证。能 decode 出来才说明确实是合法图片，
        // 顺带把解码后的尺寸信息返回给上层（可存库用于前端展示）。
        try (InputStream in = file.getInputStream()) {
            BufferedImage image = ImageIO.read(in);
            if (image == null) {
                throw new IllegalArgumentException("图片内容损坏或非合法图片");
            }
            return mime + ";w=" + image.getWidth() + ";h=" + image.getHeight();
        } catch (IllegalArgumentException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalArgumentException("图片解码失败", e);
        }
    }
}
```

配套 Controller：

```java
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@RestController
@RequestMapping("/api/upload")
public class UploadController {

    private final ImageUploadValidator validator;

    public UploadController(ImageUploadValidator validator) {
        this.validator = validator;
    }

    @PostMapping("/avatar")
    public ResponseEntity<Map<String, String>> uploadAvatar(
            @RequestParam("file") MultipartFile file) {
        try {
            String result = validator.validate(file);
            // 生产环境这里还要：生成 object key -> 存对象存储 -> 落库
            return ResponseEntity.ok(Map.of("status", "ok", "detail", result));
        } catch (IllegalArgumentException e) {
            // 业务拒绝：类型不允许 / 超大小 / 解码失败，返回 400
            return ResponseEntity.badRequest().body(Map.of("status", "error", "message", e.getMessage()));
        } catch (Exception e) {
            // 系统异常：IO 错误等，返回 500（生产环境应记日志 + 告警）
            return ResponseEntity.internalServerError()
                    .body(Map.of("status", "error", "message", "服务器处理失败"));
        }
    }
}
```

这个场景为什么必须用 Tika 而不是手写魔数：头像场景要精确区分 PNG/JPEG/GIF/WebP 四种，手写规则表完全能覆盖，但一旦白名单扩到 PDF/Office（下个场景的文档库），手写表的维护成本就上来了。Tika 的规则库是现成的。

### 7.2 场景二：文档全文检索的文本抽取

需求：企业文档库里允许上传 PDF/Word/Excel/PPT，上传后异步抽取文本存入数据库（或发给 Elasticsearch），供全文搜索。核心要求：不阻塞上传请求、解析失败不影响上传本身、单个文件解析有资源上限。

```java
import org.apache.tika.Tika;
import org.apache.tika.exception.TikaException;
import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.PagedText;
import org.apache.tika.metadata.TikaCoreProperties;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.concurrent.CompletableFuture;

@Service
public class DocumentParseService {

    private final Tika tika;

    public DocumentParseService(Tika tika) {
        this.tika = tika;
    }

    /**
     * 上传入库后异步调用：抽文本 + 抽元数据。
     * 返回结果对象由调用方决定存哪（这里演示返回，生产可落库）。
     */
    public CompletableFuture<ParsedDocument> parseAsync(MultipartFile file, String docId) {
        return CompletableFuture.supplyAsync(() -> parseSync(file, docId));
        // 生产环境建议注入专用线程池 Executor，别用 ForkJoinPool.commonPool
    }

    public ParsedDocument parseSync(MultipartFile file, String docId) {
        Metadata metadata = new Metadata();
        ParsedDocument result = new ParsedDocument();
        result.setDocId(docId);
        result.setFileName(file.getOriginalFilename());
        result.setSize(file.getSize());

        // TikaInputStream.get(InputStream, Metadata) 这个二参重载在 Tika 3.x 不存在，
        // 资源名要手动写进 metadata（容器检测 docx 细分依赖文件名做辅助）
        try (InputStream raw = file.getInputStream();
             TikaInputStream tis = TikaInputStream.get(raw)) {
            metadata.set(TikaCoreProperties.RESOURCE_NAME_KEY, file.getOriginalFilename());

            // 类型检测：detect 内部会 mark/reset，不破坏流位置，可继续 parseToString
            String mime = tika.detect(tis, metadata);
            result.setMimeType(mime);

            // 文本抽取：上限 200 万字符，超过抛 TooLongContentException
            String text = tika.parseToString(tis, metadata);
            result.setText(text);

            // 元数据：用常量类引用键名，别硬编码字符串
            result.setTitle(metadata.get(TikaCoreProperties.TITLE));
            result.setAuthor(metadata.get(TikaCoreProperties.CREATOR));
            result.setPageCount(metadata.get(PagedText.N_PAGES));
        } catch (TikaException e) {
            // 解析失败：文件损坏/不支持的格式/超长。不要抛给上传链路，
            // 记录状态即可，索引任务跳过该文档
            result.setParseError(e.getClass().getSimpleName() + ": " + e.getMessage());
        } catch (Exception e) {
            result.setParseError("io: " + e.getMessage());
        }
        return result;
    }

    /** 解析结果 DTO */
    public static class ParsedDocument {
        private String docId;
        private String fileName;
        private long size;
        private String mimeType;
        private String text;
        private String title;
        private String author;
        private String pageCount;
        private String parseError;

        // getter / setter（生产用 Lombok 或 record 风格，此处省略）
        public String getDocId() { return docId; }
        public void setDocId(String docId) { this.docId = docId; }
        public String getFileName() { return fileName; }
        public void setFileName(String fileName) { this.fileName = fileName; }
        public long getSize() { return size; }
        public void setSize(long size) { this.size = size; }
        public String getMimeType() { return mimeType; }
        public void setMimeType(String mimeType) { this.mimeType = mimeType; }
        public String getText() { return text; }
        public void setText(String text) { this.text = text; }
        public String getTitle() { return title; }
        public void setTitle(String title) { this.title = title; }
        public String getAuthor() { return author; }
        public void setAuthor(String author) { this.author = author; }
        public String getPageCount() { return pageCount; }
        public void setPageCount(String pageCount) { this.pageCount = pageCount; }
        public String getParseError() { return parseError; }
        public void setParseError(String parseError) { this.parseError = parseError; }
    }
}
```

配套的批量重试任务（消息队列消费者模式，比如接 RabbitMQ 或本地定时扫描）：

```java
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;

/**
 * 演示：解析失败文档的重试队列。
 * 生产环境一般是 MQ 的 dead-letter + 重试，这里用内存队列演示思路。
 */
@Component
public class ParseRetryJob {

    private final DocumentParseService parseService;
    private final ConcurrentLinkedQueue<RetryItem> retryQueue = new ConcurrentLinkedQueue<>();

    public ParseRetryJob(DocumentParseService parseService) {
        this.parseService = parseService;
    }

    /** 解析失败时由上层调用来登记重试 */
    public void enqueue(String docId, String fileKey) {
        retryQueue.offer(new RetryItem(docId, fileKey));
    }

    @Scheduled(fixedDelay = 60_000)
    public void retryFailedParses() {
        RetryItem item;
        int maxAttempts = 3;
        while ((item = retryQueue.poll()) != null) {
            // 从对象存储按 fileKey 重新取文件流再解析
            // 达到 maxAttempts 则记录最终失败，人工介入
        }
    }

    record RetryItem(String docId, String fileKey) {}
}
```

要点总结：

1. 解析必须在异步线程做——PDF 解析几十上百 MB 的文档可能要几秒到几十秒，放请求线程会把上传接口拖垮；
2. 解析失败要吞掉并记录，不能把上传接口一起带崩——文本抽取是"附加价值"，上传成功本身不该依赖它；
3. `TikaInputStream.get(InputStream, metadata)` 优于直接传 MultipartFile 的流：它支持 mark/reset，检测和解析可以共用一个流（见踩坑 5）；
4. 这个场景依赖 parsers 模块（`tika-parsers-standard-package`），没有它 PDF/Office 解析不了，见踩坑 1。

### 7.3 场景三：自定义魔数检测器接入 Spring

需求：内部系统有一个自定义文件格式 `.lconf`（头部是 `LCFG1`），需要让 Tika 认识它，并且检测逻辑里附加一条业务规则——`LCFG2` 开头的文件属于"已加密配置"，检测为另一个类型。这种动态规则适合编程式实现一个自定义 Detector 接入 Tika 的检测链。

```java
import org.apache.tika.detect.Detector;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.mime.MediaType;

import java.io.IOException;
import java.io.InputStream;

/**
 * 自定义检测器：识别 LCFG1 / LCFG2 开头的内部配置文件。
 * 实现 Detector 接口后，可以组合进默认检测链（见 DetectorConfig），
 * 也可以单独注入使用。
 *
 * 注意两个约定：
 * 1. Tika 3.x 的 Detector 接口签名是 detect(InputStream, Metadata)，
 *    4.0 起才改为带 ParseContext 的三参版本，升级时注意；
 * 2. 读流必须 mark/reset 复位：检测链里多个 detector 轮流读同一条流，
 *    不复位会让后面的 detector 从错误位置开始读，魔数全对不上。
 */
public class LcfgDetector implements Detector {

    private static final byte[] LCFG1 = {'L', 'C', 'F', 'G', '1'};
    private static final byte[] LCFG2 = {'L', 'C', 'F', 'G', '2'};

    public static final MediaType LC_CONFIG = MediaType.application("x-lcfg");
    public static final MediaType LC_CONFIG_ENCRYPTED = MediaType.application("x-lcfg-encrypted");

    @Override
    public MediaType detect(InputStream input, Metadata metadata) throws IOException {
        if (input == null) {
            return MediaType.OCTET_STREAM;
        }
        // 标准写法：mark -> 读 -> reset（MagicDetector 内部就是这么做的）
        input.mark(5);
        try {
            byte[] header = input.readNBytes(5);
            if (startsWith(header, LCFG1)) {
                return LC_CONFIG;
            }
            if (startsWith(header, LCFG2)) {
                return LC_CONFIG_ENCRYPTED;
            }
        } finally {
            input.reset();
        }
        // 不是我们的格式，返回 octet-stream 表示"未命中"，让下游检测器继续
        return MediaType.OCTET_STREAM;
    }

    private boolean startsWith(byte[] data, byte[] prefix) {
        if (data.length < prefix.length) {
            return false;
        }
        for (int i = 0; i < prefix.length; i++) {
            if (data[i] != prefix[i]) {
                return false;
            }
        }
        return true;
    }
}
```

Spring 配置：组装一个"先走自定义检测器、命中不了再走 Tika 默认链"的组合检测器：

```java
import org.apache.tika.config.TikaConfig;
import org.apache.tika.detect.CompositeDetector;
import org.apache.tika.detect.Detector;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class DetectorConfig {

    @Bean
    public LcfgDetector lcfgDetector() {
        return new LcfgDetector();
    }

    /**
     * 组合检测器：先跑自定义规则，再回退到 Tika 默认检测链。
     * 用 List 构造器即可——不要用 MimeTypes 作首参的版本，
     * 那个重载要的是 MediaTypeRegistry。
     */
    @Bean
    public Detector compositeDetector(TikaConfig tikaConfig, LcfgDetector lcfgDetector) {
        return new CompositeDetector(List.of(lcfgDetector, tikaConfig.getDetector()));
    }
}
```

组合好的 Detector 注入业务 Service，用法与直接调 Tika 一致：

```java
import org.apache.tika.detect.Detector;
import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.mime.MediaType;
import org.springframework.stereotype.Service;

import java.io.InputStream;

@Service
public class LcfgDetectionService {

    private final Detector detector;

    public LcfgDetectionService(Detector detector) {
        this.detector = detector;
    }

    public MediaType detect(InputStream in, String fileName) throws Exception {
        Metadata metadata = new Metadata();
        metadata.set(org.apache.tika.metadata.TikaCoreProperties.RESOURCE_NAME_KEY, fileName);
        try (TikaInputStream tis = TikaInputStream.get(in)) {
            return detector.detect(tis, metadata);
        }
    }
}
```

两个约定容易踩，写进团队规范：

1. **未命中返回 `MediaType.OCTET_STREAM`，不能返回 null**。`CompositeDetector.detect` 内部对每个结果调 `registry.isSpecializationOf(detected, type)` 做"谁更具体"的比较，null 传进去直接 NPE。
2. **组合语义不是短路**。`CompositeDetector` 会遍历全部 detector，用"具体程度"（isSpecializationOf）挑最具体的类型覆盖 octet-stream 基线，而不是"第一个非 octet-stream 就停"。所以自定义 detector 返回的类型越具体，越有机会赢过默认链的结果——设计业务类型时要注意它的 MIME 层级关系。

---

## 8. 最佳实践与踩坑记录

### 8.1 最佳实践

1. **类型校验三件套按序执行**：扩展名校验（提示用）-> 魔数检测（主校验）-> 真实解析（兜底）。只做其中任何一层都不够。
2. **Tika 实例全局单例**：`Tika` 和 `TikaConfig` 线程安全，注册成 Spring Bean 注入，不要在每次请求里 new。
3. **区分"检测"和"解析"两个依赖**：只做类型白名单校验引 `tika-core` 就够；要做文本抽取/容器细分再引 `tika-parsers-standard-package`。依赖体积差一个数量级。
4. **文本抽取必须限流**：`BodyContentHandler(writeLimit)` 或 `Tika.setMaxStringLength` 二选一，防止超大文档把内存打爆。默认 10 万字符对长文档偏小，按业务调到百万级。
5. **解析一律异步**：PDF/Office 解析耗时秒级起步，走线程池或 MQ，别占请求线程。解析失败要吞掉记录，不能影响上传主流程。
6. **`TikaInputStream` 统一入口**：传 `InputStream` 时用 `TikaInputStream.get(in)` 包装（自动支持 mark/reset，检测 + 解析共用一条流）；资源名要手动 `metadata.set(TikaCoreProperties.RESOURCE_NAME_KEY, name)`——Tika 3.x 没有 `get(InputStream, Metadata)` 这个二参重载。
7. **文件名只做辅助**：detect 时传文件名是为了让 `text/csv` 这类文本格式精化，不要把文件名当类型依据。
8. **OCR 独立评估**：Tesseract 是外部进程，要装系统包、吃 CPU、耗时长。装了 tesseract 就默认启用，`setSkipOcr(true)` 可显式关闭；必须走异步 + 超时控制。
9. **解析器放独立进程（可选进阶）**：解析量大的系统用 tika-server 做隔离，解析库的内存问题、崩溃不波及其他服务。
10. **版本对齐**：Spring Boot 3.x + Java 17 用 Tika 3.3.x；老项目 Java 8 只能用 2.9.x（2.x 已 EOL，有安全风险，建议升级）。

### 8.2 踩坑记录

坑 1：只引 tika-core 就调 parseToString，报 "No parser available"
结论：tika-core 不含任何解析器实现。
原因：core 只有接口和检测逻辑，解析需要 tika-parsers-standard-package（它内部聚合 PDFBox/POI 等）。
解法：做解析就引 parsers 模块；只检测则不用引。判断标准看 6.1 节决策路径。

坑 2：docx 检测出 application/zip 而不是 Word 类型
结论：容器格式细分需要 parsers 模块的 ContainerDetector。
原因：docx 魔数与 zip 相同，core 只能判到 ZIP 层；细分要打开容器看 [Content_Types].xml。
解法：需要区分 Office 类型就引 tika-parsers-standard-package。

坑 3：MultipartFile 的流只能读一次，检测完解析没内容
结论：一个 InputStream 不能既被 detect 消费又被 parse 消费。
原因：detect 会读取流头；普通流读完即前进，不支持回退。
解法：用 `TikaInputStream.get(in)` 包装（支持 mark/reset），资源名单独 `metadata.set(TikaCoreProperties.RESOURCE_NAME_KEY, name)`；或者先 `Files.copy(file.getInputStream(), tmpPath)` 落临时文件再处理。

坑 4：文件名伪造骗过校验
结论：只按扩展名或 Content-Type 判断类型，等于没校验。
原因：浏览器和客户端可以随意伪造 multipart 的 Content-Type 头和文件名。
解法：以 Tika detect（读内容）为准，扩展名/Content-Type 只做提示。

坑 5：伪造魔数的伪装文件（jpg 头 + 恶意 payload）
结论：魔数校验挡不住精心构造的伪装文件。
原因：文件头几个字节拼成魔数很容易，魔数只能证明"开头像"，不能证明"整个文件是"。
解法：白名单 + 真实解析双保险。图片用 ImageIO.read 解码验证，PDF/Office 用 Tika parse 跑一遍，解析失败即拒绝（7.1 场景的完整做法）。

坑 6：超大文档解析 OOM / 拖垮服务
结论：parseToString 不设上限，恶意大 PDF 能把堆打满。
原因：解析器把整个文档内容读进内存构造文本。
解法：BodyContentHandler(writeLimit) 限流；上传大小在 yml 限；解析放异步线程池；极端场景用 tika-server 进程隔离 + ForkParser。

坑 7：依赖冲突（POI/PDFBox/commons-lang3 版本被覆盖）
结论：引 tika-parsers-standard-package 后，项目里原有第三方库版本可能被 Tika 的传递依赖顶掉，出现 NoSuchMethodError / AbstractMethodError。实测一个必踩组合：Spring Boot 3.3.x（dependencyManagement 把 commons-lang3 锁在 3.14.0）+ Tika 3.3.2（其 commons-compress 1.28.0 需要 commons-lang3 3.15+ 才有的 `SystemProperties.getUserName(String)` 重载）——解析 TAR 时直接抛 `NoSuchMethodError: org.apache.commons.lang3.SystemProperties.getUserName(String)`。
原因：parsers 聚合了大量第三方库（POI/PDFBox/commons-compress/commons-lang3），传递依赖版本与项目 dependencyManagement 锁定的版本冲突，且这种冲突只在解析到特定格式时才爆，运行时才能发现。
解法：`mvn dependency:tree` 查冲突，在 pom 里显式固定正确版本（本例加 `commons-lang3:3.17.0` 即可）；或者干脆全用 Tika 的版本，业务代码不直接依赖 POI/PDFBox API。

坑 8：OCR 报 "tesseract is not installed" / 中文识别乱码
结论：tika-parser-ocr-module 只是 Java 侧封装，真正干活的是系统 tesseract 进程。
原因：OCR 模块通过命令行调用 tesseract，路径不在 PATH 或语言包没装都会失败。
解法：apt 安装 tesseract-ocr + 对应语言包（中文 tesseract-ocr-chi-sim）；不在 PATH 时用 TesseractOCRConfig.setTesseractPath 指定；语言参数写 chi_sim+eng。

坑 9：custom-mimetypes.xml 不生效
结论：文件放错位置，Tika 静默忽略。
原因：Tika 3.x 从 classpath 根目录加载 custom-mimetypes.xml；2.x 是 org/apache/tika/mime/ 下。放错位置不报错，就是没效果。
解法：确认 Tika 版本对应的加载位置；或用 5.6 节的编程式注册，绕开文件路径问题。

坑 10：detect 对纯文本文件总是返回 text/plain，区分不了 csv/json
结论：文本类格式没有魔数特征，靠文件名精化。
原因：txt/csv/json/yaml 文件头都是任意字符，魔数检测只能判定"是文本"。
解法：detect 时传文件名（TikaInputStream.get(file, metadata) 或 detect(in, name)），NameDetector 会按扩展名精化；要更准就用 parse 后按内容判断（尝试 JSON 解析等）。

坑 11：tika-app / tika-server 版本与库版本不一致
结论：命令行和 REST 服务用的 jar 要跟项目里依赖版本一致，否则行为对不上。
原因：检测规则库随版本演进，不同版本对同一文件的判定可能不同。
解法：统一用同一版本；把"用 tika-server 预检 + 本地库校验"这类双通道逻辑做版本对齐，并加集成测试锁行为。

---

## 9. 参考链接

- Apache Tika 官网：https://tika.apache.org/
- Tika Getting Started（构件与 Maven 依赖说明）：https://tika.apache.org/3.3.0/gettingstarted.html
- Tika Content Detection（检测原理与优先级）：https://tika.apache.org/3.3.1/detection.html
- Tika Java API 使用文档：https://tika.apache.org/docs/4.0.0-SNAPSHOT/using-tika/java-api/index.html
- Maven Central: org.apache.tika:tika-core：https://mvnrepository.com/artifact/org.apache.tika/tika-core
- Oracle JDK 文档：FileTypeDetector（Files.probeContentType 的 SPI）：https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/spi/FileTypeDetector.html
- Spring MediaTypeFactory API：https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/http/MediaTypeFactory.html
- Apache POI 官网：https://poi.apache.org/
- Apache PDFBox 官网：https://pdfbox.apache.org/
- file 命令与 libmagic：https://man7.org/linux/man-pages/man5/magic.5.html
