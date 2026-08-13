---
title: NIO
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, nio, buffer, channel, selector, non-blocking]
---

# NIO

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [IO vs NIO](#io-vs-nio)
- [Buffer 缓冲区](#buffer-缓冲区)
- [Channel 通道](#channel-通道)
- [FileChannel 文件通道](#filechannel-文件通道)
- [SocketChannel 与 ServerSocketChannel](#socketchannel-与-serversocketchannel)
- [Selector 多路复用](#selector-多路复用)
- [非阻塞 IO 实战](#非阻塞-io-实战)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

NIO（New IO / Non-blocking IO）是 JDK 1.4 引入的 IO API，解决传统 BIO 的两个核心问题：

1. **面向流 vs 面向块**：传统 IO 按字节流读写，NIO 按 Buffer 块操作
2. **阻塞 vs 非阻塞 + 多路复用**：传统 IO 一个线程只能处理一个连接；NIO 用 Selector 让一个线程管理多个 Channel

NIO 三大核心组件：

```
Channel ←→ Buffer ←→ Selector
  通道      缓冲区    选择器

Channel：双向数据传输管道（可读可写）
Buffer： 数据容器（一块内存，读写都通过它）
Selector：多路复用器（监控多个 Channel 的事件）
```

## IO vs NIO

| 维度 | BIO（传统 IO） | NIO |
|------|----------------|-----|
| 数据流向 | 单向流（InputStream / OutputStream） | 双向通道（Channel 可读可写） |
| 数据单位 | 字节/字符 | Buffer 数据块 |
| 处理方式 | 阻塞（线程必须等 IO 完成） | 非阻塞 + 多路复用（一个线程管多个连接） |
| 适用场景 | 连接数少、数据量大 | 连接数多（万级）、每个连接数据量少 |
| 编程复杂度 | 简单 | 较复杂 |

## Buffer 缓冲区

Buffer 是一块连续内存，用于在 Channel 之间传递数据。它不是字节数组的薄包装——有自己的内部状态机：

### Buffer 的核心属性

```java
// 所有 Buffer 子类都有这四个核心属性
capacity   // 总容量（不变）
limit      // 可读/可写的上限位置
position   // 当前读写位置
mark       // 标记位置（用于 reset）

// 关系：0 ≤ mark ≤ position ≤ limit ≤ capacity
```

### Buffer 的操作模式

```java
// Buffer 有两个模式：写模式 和 读模式

// 1. 初始：写模式
//    position=0   limit=capacity
//    [ _ _ _ _ _ _ _ _ ]
//      ↑           ↑
//    position     limit

// 2. 写入 3 字节后
//    [A B C _ _ _ _ _ ]
//              ↑     ↑
//          position  limit

// 3. flip() —— 切换到读模式
//    [A B C _ _ _ _ _ ]
//      ↑     ↑
//   position limit (position 回 0，limit 设为原 position)

// 4. 读取 2 字节后
//    [A B C _ _ _ _ _ ]
//          ↑ ↑
//     position limit

// 5. compact() —— 把未读数据移到开头，切换到写模式
//    [C _ _ _ _ _ _ _ ]    limit 回到 capacity
//      ↑                   position 在未读数据之后
//    position
```

### ByteBuffer 核心操作

```java
// 创建 ByteBuffer
ByteBuffer buf1 = ByteBuffer.allocate(1024);        // 堆内存
ByteBuffer buf2 = ByteBuffer.allocateDirect(1024);  // 直接内存（堆外）

// 写入数据
buf1.put((byte) 65);               // 'A'
buf1.put("hello".getBytes());      // 字节数组
buf1.putInt(42);                   // 4 字节整数

// 翻转——写模式切换到读模式
buf1.flip();

// 读取数据
byte b = buf1.get();               // 读一个字节
byte[] dst = new byte[5];
buf1.get(dst);                     // 读多个
int i = buf1.getInt();             // 读 4 字节整数

// 其它操作
buf1.rewind();                     // 重读：position 回 0
buf1.clear();                      // 清空：position=0, limit=capacity（数据还在，只是"忘掉了"）
buf1.compact();                    // 压缩：未读数据移到开头
buf1.mark();                       // 标记当前位置
buf1.reset();                      // 回到标记位置

boolean has = buf1.hasRemaining(); // 还有数据可读？
int remain = buf1.remaining();     // 剩余可读字节数
```

### 直接内存 vs 堆内存

```java
// 堆内存 Buffer —— 数据在 JVM 堆中
ByteBuffer heapBuf = ByteBuffer.allocate(1024);
// I/O 操作时数据需要多拷贝一次（堆 → 直接内存 → 内核）

// 直接内存 Buffer —— 数据在堆外（不受 GC 管理）
ByteBuffer directBuf = ByteBuffer.allocateDirect(1024);
// I/O 操作零拷贝（直接内存 → 内核）
// 创建和销毁成本高于堆 Buffer
```

## Channel 通道

Channel 是双向数据传输管道——和 Stream 的关键区别：

```
Stream：单向（InputStream 只读，OutputStream 只写）
Channel：双向（可同时读写）
```

主要 Channel 实现：

```java
FileChannel              // 文件读写
SocketChannel            // TCP 客户端
ServerSocketChannel      // TCP 服务端（接受连接）
DatagramChannel          // UDP
```

Channel 操作必须通过 Buffer：

```java
// 从 Channel 读入 Buffer
int bytesRead = channel.read(buffer);

// 从 Buffer 写入 Channel
int bytesWritten = channel.write(buffer);
```

## FileChannel 文件通道

通过 `FileInputStream` / `FileOutputStream` / `RandomAccessFile` 获取文件通道：

```java
// 只读
try (FileChannel channel = FileChannel.open(Path.of("data.txt"),
         StandardOpenOption.READ)) {
    ByteBuffer buf = ByteBuffer.allocate(1024);
    int bytesRead;
    while ((bytesRead = channel.read(buf)) != -1) {
        buf.flip();
        // 处理数据...
        buf.clear();
    }
}

// 读写
try (FileChannel channel = FileChannel.open(Path.of("data.bin"),
         StandardOpenOption.READ, StandardOpenOption.WRITE,
         StandardOpenOption.CREATE)) {
    // 写入
    ByteBuffer buf = ByteBuffer.wrap("hello".getBytes(StandardCharsets.UTF_8));
    channel.write(buf);

    // 读回
    channel.position(0);  // 回到开头
    buf.clear();
    channel.read(buf);
    buf.flip();
    // 处理读出的数据...
}
```

### 零拷贝传输

```java
// transferTo / transferFrom —— 直接在两个 Channel 之间传输，不经过用户空间
try (FileChannel src = FileChannel.open(Path.of("source.bin"), StandardOpenOption.READ);
     FileChannel dst = FileChannel.open(Path.of("target.bin"),
         StandardOpenOption.WRITE, StandardOpenOption.CREATE)) {
    
    long position = 0;
    long size = src.size();
    while (position < size) {
        position += src.transferTo(position, size - position, dst);
    }
    // 或 src.transferFrom(dst, 0, size);
}
```

### 内存映射文件

```java
// MappedByteBuffer —— 把文件的一部分映射到内存
try (FileChannel channel = FileChannel.open(Path.of("large.bin"),
         StandardOpenOption.READ)) {
    
    MappedByteBuffer mapped = channel.map(
        FileChannel.MapMode.READ_ONLY,  // 只读
        0,                               // 起始位置
        channel.size()                   // 映射长度
    );
    
    // 像操作内存一样操作文件（操作系统负责页面换入换出）
    byte b = mapped.get(1000);
    int i = mapped.getInt(2000);
}
```

## SocketChannel 与 ServerSocketChannel

```java
// SocketChannel —— TCP 客户端
SocketChannel client = SocketChannel.open();
client.configureBlocking(false);               // 非阻塞模式
client.connect(new InetSocketAddress("localhost", 8080));

// 非阻塞 connect —— 需要等连接完成
while (!client.finishConnect()) {
    // 可以在此期间做其他事
}

// 读写
ByteBuffer buf = ByteBuffer.allocate(1024);
int bytesRead = client.read(buf);              // 非阻塞：没数据时返回 0
buf.flip();
client.write(buf);

// ServerSocketChannel —— TCP 服务端
ServerSocketChannel server = ServerSocketChannel.open();
server.configureBlocking(false);               // 非阻塞模式
server.bind(new InetSocketAddress(8080));

while (true) {
    SocketChannel conn = server.accept();       // 非阻塞：没连接时返回 null
    if (conn != null) {
        conn.configureBlocking(false);
        // 处理连接...
    }
}
```

## Selector 多路复用

Selector 是 NIO 的精华——一个线程通过一个 Selector 监控多个 Channel 的 IO 事件：

```java
// 创建 Selector
Selector selector = Selector.open();

// 注册 Channel 到 Selector（必须是非阻塞模式）
ServerSocketChannel server = ServerSocketChannel.open();
server.configureBlocking(false);
server.bind(new InetSocketAddress(8080));
server.register(selector, SelectionKey.OP_ACCEPT);  // 注册"接受连接"事件

// 事件循环
while (true) {
    selector.select();  // 阻塞直到有就绪的事件

    Iterator<SelectionKey> it = selector.selectedKeys().iterator();
    while (it.hasNext()) {
        SelectionKey key = it.next();
        it.remove();  // 关键：必须手动移除！

        if (key.isAcceptable()) {
            // 有新的连接
            ServerSocketChannel ssc = (ServerSocketChannel) key.channel();
            SocketChannel client = ssc.accept();
            client.configureBlocking(false);
            client.register(selector, SelectionKey.OP_READ);
            
        } else if (key.isReadable()) {
            // 有数据可读
            SocketChannel client = (SocketChannel) key.channel();
            ByteBuffer buf = ByteBuffer.allocate(1024);
            int bytesRead = client.read(buf);
            if (bytesRead == -1) {
                client.close();  // 连接关闭
            } else {
                buf.flip();
                // 处理 buf 中的数据...
            }
            
        } else if (key.isWritable()) {
            // 可以写入（通常不用注册，直接写）
        }
    }
}
```

### SelectionKey 事件类型

```java
SelectionKey.OP_ACCEPT   // 有连接可接受（ServerSocketChannel）
SelectionKey.OP_CONNECT  // 连接已建立（SocketChannel）
SelectionKey.OP_READ     // 有数据可读
SelectionKey.OP_WRITE    // 可以写入数据
```

## 非阻塞 IO 实战

```java
// 简单的 NIO Echo Server
public class NioEchoServer {
    public static void main(String[] args) throws IOException {
        Selector selector = Selector.open();
        
        ServerSocketChannel server = ServerSocketChannel.open();
        server.configureBlocking(false);
        server.bind(new InetSocketAddress(8080));
        server.register(selector, SelectionKey.OP_ACCEPT);
        System.out.println("Echo Server started on port 8080");

        ByteBuffer buf = ByteBuffer.allocate(256);

        while (true) {
            selector.select();
            
            for (Iterator<SelectionKey> it = selector.selectedKeys().iterator(); it.hasNext(); ) {
                SelectionKey key = it.next();
                it.remove();

                try {
                    if (key.isAcceptable()) {
                        ServerSocketChannel ssc = (ServerSocketChannel) key.channel();
                        SocketChannel client = ssc.accept();
                        client.configureBlocking(false);
                        client.register(selector, SelectionKey.OP_READ);
                        System.out.println("Client connected: " + client.getRemoteAddress());
                        
                    } else if (key.isReadable()) {
                        SocketChannel client = (SocketChannel) key.channel();
                        buf.clear();
                        int bytesRead = client.read(buf);
                        if (bytesRead == -1) {
                            client.close();
                            continue;
                        }
                        buf.flip();
                        client.write(buf);  // echo 回去
                    }
                } catch (IOException e) {
                    key.cancel();
                    key.channel().close();
                }
            }
        }
    }
}
```

## 应用场景实战

### 场景一：大文件复制（零拷贝）

```java
public static void fastCopy(Path source, Path target) throws IOException {
    try (FileChannel src = FileChannel.open(source, StandardOpenOption.READ);
         FileChannel dst = FileChannel.open(target,
             StandardOpenOption.WRITE, StandardOpenOption.CREATE)) {
        src.transferTo(0, src.size(), dst);
    }
}
```

### 场景二：批量 IO 的 Scatter/Gather

```java
// Scatter：从一个 Channel 读到多个 Buffer
ByteBuffer header = ByteBuffer.allocate(128);
ByteBuffer body = ByteBuffer.allocate(1024);
ByteBuffer[] buffers = {header, body};
channel.read(buffers);  // 先填满 header，再填 body

// Gather：从多个 Buffer 写入一个 Channel
header.flip();
body.flip();
channel.write(new ByteBuffer[]{header, body});
```

### 场景三：内存映射大文件搜索

```java
public static List<Long> searchInFile(Path file, byte[] pattern) throws IOException {
    List<Long> positions = new ArrayList<>();
    try (FileChannel channel = FileChannel.open(file, StandardOpenOption.READ)) {
        MappedByteBuffer mapped = channel.map(
            FileChannel.MapMode.READ_ONLY, 0, channel.size());
        
        // 遍历内存映射区域查找
        for (int i = 0; i <= mapped.limit() - pattern.length; i++) {
            boolean found = true;
            for (int j = 0; j < pattern.length; j++) {
                if (mapped.get(i + j) != pattern[j]) {
                    found = false;
                    break;
                }
            }
            if (found) positions.add((long) i);
        }
    }
    return positions;
}
```

## 最佳实践与踩坑记录

### Channel 操作流程

```
1. 打开 Channel — FileChannel.open()
2. 分配 Buffer — ByteBuffer.allocate()
3. 读：channel.read(buffer)
4. flip() — 切换读模式
5. 处理 Buffer 数据
6. clear() — 清空/compact() — 压缩
7. 写：buffer.put() → flip() → channel.write(buffer)
8. 关闭 Channel
```

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| Selector.selectedKeys() 不清理 | Iterator 遍历完没 remove | 每次处理完一个 key 立即 `it.remove()` |
| NIO read 返回 0 | 非阻塞模式下没有数据 | 正常行为，不做处理即可 |
| 读完数据后缓冲区还有旧数据 | 没调 clear/compact | flip 读完后调 clear 或 compact |
| MappedByteBuffer 超过 2GB | 单次 map 限制 | 分多次映射 |
| DirectBuffer OOM | 直接内存超过 `-XX:MaxDirectMemorySize` | 增加限制或释放 Buffer（GC 触发） |

### 选型指南

| 场景 | 推荐 |
|------|------|
| 简单文件读写 | BIO + Buffered Stream |
| 大文件复制 | FileChannel.transferTo（零拷贝） |
| 超大文件随机访问 | MappedByteBuffer |
| 万级并发连接（IM/推送） | NIO + Selector |
| 更复杂的网络 IO | Netty 框架（封装了 NIO） |

## 总结

- NIO 三大组件：Channel（双向通道）、Buffer（数据容器）、Selector（多路复用）
- Buffer 是状态机：allocate → put → flip → get → clear/compact
- FileChannel.transferTo 实现零拷贝，比传统复制快 2-3 倍
- Selector 让一个线程管理数千个连接——单线程模型的理论基础
- 非阻塞模式 read/write 返回 0 是正常的，不等于 IO 异常
- 直接 Buffer（allocateDirect）省一次内存拷贝但创建成本高，适合长生命周期场景
- 实际开发中网络 IO 优先考虑 Netty——Java NIO 的 API 太底层
