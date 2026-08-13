---
title: NIO.2
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, nio2, files, path, watchservice, asynchronous-io]
---

# NIO.2

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Path 与 Files 回顾](#path-与-files-回顾)
- [WatchService 文件监控](#watchservice-文件监控)
- [FileVisitor 遍历文件树](#filevisitor-遍历文件树)
- [AsynchronousFileChannel 异步 IO](#asynchronousfilechannel-异步-io)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

NIO.2 是 JDK 7 (Java 7) 引入的增强 IO API——`java.nio.file` 包。它不是 NIO 的替代，而是补充：NIO.2 带来了三大能力：

1. **增强的文件系统 API**：`Path`、`Files`（已在 34-文件操作 展开）
2. **文件变更监控**：`WatchService` —— 无需轮询，文件变化自动通知
3. **异步 IO**：`AsynchronousFileChannel` —— 回调驱动的文件读写

NIO.2 和 NIO 的关系：

```
NIO (JDK 1.4)          NIO.2 (JDK 7)
───────────            ──────────────
Buffer                 Path (替代 File)
Channel                Files (文件操作工具)
Selector               WatchService (目录监控)
                        FileVisitor (文件树遍历)
                        AsynchronousFileChannel
```

## Path 与 Files 回顾

这部分在 34-文件操作 已详细讲解，这里只做速查：

```java
// 创建路径
Path p = Path.of("/home/user/data.txt");

// 常见文件操作
Files.createFile(p);
Files.createDirectories(p.getParent());
Files.copy(src, target, StandardCopyOption.REPLACE_EXISTING);
Files.move(src, target, StandardCopyOption.ATOMIC_MOVE);
Files.delete(p);
Files.deleteIfExists(p);

// 读取
String content = Files.readString(p, StandardCharsets.UTF_8);
List<String> lines = Files.readAllLines(p, StandardCharsets.UTF_8);
try (Stream<String> stream = Files.lines(p)) { ... }

// 写入
Files.writeString(p, "hello", StandardCharsets.UTF_8);
Files.write(p, lines, StandardCharsets.UTF_8);

// 遍历
try (Stream<Path> entries = Files.list(dir)) { ... }
try (Stream<Path> tree = Files.walk(dir, 3)) { ... }
try (Stream<Path> found = Files.find(dir, 10, predicate)) { ... }
```

## WatchService 文件监控

`WatchService` 利用操作系统底层的文件系统事件通知机制（Linux 的 inotify、Mac 的 kqueue、Windows 的 ReadDirectoryChangesW）来监测目录变化——比轮询高效得多：

```java
import java.nio.file.*;

// 创建 WatchService
WatchService watcher = FileSystems.getDefault().newWatchService();

// 注册要监控的目录和事件类型
Path dir = Path.of("/path/to/watch");
dir.register(watcher,
    StandardWatchEventKinds.ENTRY_CREATE,   // 文件/目录创建
    StandardWatchEventKinds.ENTRY_MODIFY,   // 文件修改
    StandardWatchEventKinds.ENTRY_DELETE    // 文件/目录删除
);

// 事件循环
while (true) {
    WatchKey key = watcher.take();  // 阻塞等待事件（或用 poll 超时）
    
    for (WatchEvent<?> event : key.pollEvents()) {
        WatchEvent.Kind<?> kind = event.kind();
        Path filename = (Path) event.context();  // 相对于被监控目录的文件名
        Path fullPath = dir.resolve(filename);
        
        if (kind == StandardWatchEventKinds.ENTRY_CREATE) {
            System.out.println("创建: " + fullPath);
        } else if (kind == StandardWatchEventKinds.ENTRY_MODIFY) {
            System.out.println("修改: " + fullPath);
        } else if (kind == StandardWatchEventKinds.ENTRY_DELETE) {
            System.out.println("删除: " + fullPath);
        } else if (kind == StandardWatchEventKinds.OVERFLOW) {
            System.out.println("事件丢失（溢出）");
        }
    }
    
    // 重置 WatchKey —— 必须！否则不再接收后续事件
    boolean valid = key.reset();
    if (!valid) {
        break;  // 目录被删除，不再可用
    }
}
```

### 递归监控

WatchService 只监控注册的那个目录——子目录的变化不会被自动监控：

```java
public static void registerRecursive(WatchService watcher, Path dir) throws IOException {
    // 注册当前目录
    dir.register(watcher,
        StandardWatchEventKinds.ENTRY_CREATE,
        StandardWatchEventKinds.ENTRY_MODIFY,
        StandardWatchEventKinds.ENTRY_DELETE);

    // 递归注册子目录
    try (Stream<Path> entries = Files.list(dir)) {
        entries.filter(Files::isDirectory)
               .forEach(subDir -> {
                   try {
                       registerRecursive(watcher, subDir);
                   } catch (IOException e) {
                       throw new UncheckedIOException(e);
                   }
               });
    }
}
```

### 注意事项

- **不保证实时**：事件可能有轻微延迟
- **OVERFLOW**：事件积压太多时发生，表示部分事件丢失
- **reset() 是必须的**：不 reset 不会收到后续事件
- **跨平台差异**：有些 OS 的 modify 事件可能触发多次（编辑器保存时会先写临时文件再重命名）

## FileVisitor 遍历文件树

`FileVisitor` 提供了比 `Files.walk()` 更精细的目录遍历控制——每一步都有回调：

```java
import java.nio.file.*;
import java.nio.file.attribute.*;

public class MyFileVisitor extends SimpleFileVisitor<Path> {

    @Override
    public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) {
        // 进入目录前调用
        System.out.println("进入: " + dir);
        return FileVisitResult.CONTINUE;  // 继续遍历
    }

    @Override
    public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
        // 访问文件时调用
        System.out.printf("  %s (%d bytes)%n", file.getFileName(), attrs.size());
        return FileVisitResult.CONTINUE;
    }

    @Override
    public FileVisitResult visitFileFailed(Path file, IOException exc) {
        // 文件访问失败时调用
        System.err.println("无法访问: " + file + " - " + exc.getMessage());
        return FileVisitResult.CONTINUE;
    }

    @Override
    public FileVisitResult postVisitDirectory(Path dir, IOException exc) {
        // 离开目录后调用
        return FileVisitResult.CONTINUE;
    }
}

// 使用
Path startDir = Path.of("/home/user");
Files.walkFileTree(startDir, new MyFileVisitor());

// 带选项的遍历
Files.walkFileTree(startDir, 
    EnumSet.of(FileVisitOption.FOLLOW_LINKS),  // 跟踪符号链接
    3,                                          // 最大深度
    new MyFileVisitor()
);
```

### FileVisitResult 控制选项

```java
FileVisitResult.CONTINUE       // 继续遍历
FileVisitResult.TERMINATE      // 立即终止遍历
FileVisitResult.SKIP_SUBTREE   // 跳过当前目录（只在 preVisitDirectory 中有效）
FileVisitResult.SKIP_SIBLINGS  // 跳过兄弟节点（不遍历同级的后续条目）
```

### 实战示例：查找并删除空目录

```java
public class EmptyDirCleaner extends SimpleFileVisitor<Path> {
    @Override
    public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
        // 离开目录时检查是否为空
        try (Stream<Path> entries = Files.list(dir)) {
            if (entries.findAny().isEmpty()) {
                Files.delete(dir);
                System.out.println("删除空目录: " + dir);
            }
        }
        return FileVisitResult.CONTINUE;
    }
}
```

### 实战示例：按扩展名收集文件

```java
public class FileCollector extends SimpleFileVisitor<Path> {
    private final String extension;
    private final List<Path> files = new ArrayList<>();

    public FileCollector(String extension) {
        this.extension = extension;
    }

    @Override
    public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
        if (file.toString().endsWith(extension)) {
            files.add(file);
        }
        return FileVisitResult.CONTINUE;
    }

    public List<Path> getFiles() { return files; }
}

// 用法
FileCollector collector = new FileCollector(".java");
Files.walkFileTree(Path.of("src"), collector);
List<Path> javaFiles = collector.getFiles();
```

## AsynchronousFileChannel 异步 IO

`AsynchronousFileChannel` 提供非阻塞的文件读写——两种模型：

1. **Future 模式**：提交操作，返回 Future，你轮询或阻塞等待结果
2. **回调模式**：提交操作 + CompletionHandler，操作完成后回调

### Future 模式

```java
import java.nio.channels.AsynchronousFileChannel;
import java.util.concurrent.Future;

Path file = Path.of("data.txt");

try (AsynchronousFileChannel channel = AsynchronousFileChannel.open(
         file, StandardOpenOption.READ)) {
    
    ByteBuffer buf = ByteBuffer.allocate(1024);
    long position = 0;
    
    Future<Integer> future = channel.read(buf, position);
    
    // 在等待 IO 完成时可以干别的事
    while (!future.isDone()) {
        // 做其他工作...
    }
    
    int bytesRead = future.get();  // 获取结果（阻塞直到完成）
    buf.flip();
    String content = StandardCharsets.UTF_8.decode(buf).toString();
    System.out.println(content);
}
```

### 回调模式

```java
import java.nio.channels.CompletionHandler;

try (AsynchronousFileChannel channel = AsynchronousFileChannel.open(
         file, StandardOpenOption.READ)) {
    
    ByteBuffer buf = ByteBuffer.allocate(1024);
    
    channel.read(buf, 0, buf, new CompletionHandler<Integer, ByteBuffer>() {
        @Override
        public void completed(Integer bytesRead, ByteBuffer attachment) {
            // IO 完成，在异步线程中回调
            attachment.flip();
            String content = StandardCharsets.UTF_8.decode(attachment).toString();
            System.out.println("读取完成: " + content);
        }

        @Override
        public void failed(Throwable exc, ByteBuffer attachment) {
            System.err.println("读取失败: " + exc.getMessage());
        }
    });
    
    // 主线程可以继续做其他事
    Thread.sleep(1000);  // 防止主线程退出（实际中应该在 CompletionHandler 中协调）
}
```

### 异步写入

```java
try (AsynchronousFileChannel channel = AsynchronousFileChannel.open(
         file, StandardOpenOption.WRITE, StandardOpenOption.CREATE)) {
    
    ByteBuffer buf = ByteBuffer.wrap("异步写入的数据".getBytes(StandardCharsets.UTF_8));
    
    channel.write(buf, 0, null, new CompletionHandler<Integer, Void>() {
        @Override
        public void completed(Integer bytesWritten, Void attachment) {
            System.out.println("写入完成: " + bytesWritten + " 字节");
        }

        @Override
        public void failed(Throwable exc, Void attachment) {
            System.err.println("写入失败: " + exc.getMessage());
        }
    });
}
```

### 适用场景

- 大文件读写不阻塞主线程
- 需要同时处理多个文件的场景
- GUI 应用中避免界面卡顿
- 实际项目中通常被更高级的框架封装（Spring WebFlux、Vert.x 等）

## 应用场景实战

### 场景一：文件热加载

```java
public class FileWatcher {
    private final WatchService watcher;
    private final Path watchedFile;
    private final Runnable onChange;

    public FileWatcher(Path file, Runnable onChange) throws IOException {
        this.watchedFile = file;
        this.onChange = onChange;
        this.watcher = FileSystems.getDefault().newWatchService();
        file.getParent().register(watcher, StandardWatchEventKinds.ENTRY_MODIFY);
    }

    public void start() {
        new Thread(() -> {
            try {
                while (true) {
                    WatchKey key = watcher.take();
                    for (WatchEvent<?> event : key.pollEvents()) {
                        Path changed = (Path) event.context();
                        if (changed.equals(watchedFile.getFileName())) {
                            onChange.run();
                        }
                    }
                    key.reset();
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "file-watcher").start();
    }
}

// 用法：监控配置文件变化
new FileWatcher(Path.of("config.properties"), () -> reloadConfig()).start();
```

### 场景二：目录大小统计

```java
public class DirectorySize extends SimpleFileVisitor<Path> {
    private long totalSize = 0;

    @Override
    public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
        totalSize += attrs.size();
        return FileVisitResult.CONTINUE;
    }

    @Override
    public FileVisitResult visitFileFailed(Path file, IOException exc) {
        return FileVisitResult.CONTINUE;  // 跳过无法访问的文件
    }

    public static long calculate(Path dir) throws IOException {
        DirectorySize visitor = new DirectorySize();
        Files.walkFileTree(dir, visitor);
        return visitor.totalSize;
    }
}
```

### 场景三：备份指定扩展名的文件

```java
public class BackupCollector extends SimpleFileVisitor<Path> {
    private final Path targetDir;
    private final String extension;

    public BackupCollector(Path targetDir, String extension) {
        this.targetDir = targetDir;
        this.extension = extension;
    }

    @Override
    public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
        if (file.toString().endsWith(extension)) {
            Path target = targetDir.resolve(file.getFileName());
            Files.copy(file, target, StandardCopyOption.REPLACE_EXISTING);
            System.out.println("备份: " + file + " → " + target);
        }
        return FileVisitResult.CONTINUE;
    }
}
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| WatchService 不触发事件 | 没调 key.reset() | 每个事件循环后必须 reset |
| 文件监控收不到子目录事件 | WatchService 只监控注册的目录 | 递归注册子目录 |
| `walkFileTree` 无限递归 | 符号链接成环 | 不传 FOLLOW_LINKS 或限制深度 |
| AsynchronousFileChannel 的回调不执行 | 主线程退出太快 | 用 CountDownLatch 或线程池等待 |
| modify 事件触发多次 | 编辑器保存时多步操作 | 用防抖（debounce）延迟处理 |

### 选型指南

| 需求 | 推荐 |
|------|------|
| 监控单个目录变化 | `WatchService` |
| 递归遍历 + 每个节点精确控制 | `FileVisitor` + `Files.walkFileTree` |
| 简单遍历（不需粒度控制） | `Files.walk()` / `Files.list()` |
| 异步读写大文件 | `AsynchronousFileChannel` |
| 高性能网络 IO | Netty（基于 NIO 之上） |

## 总结

- NIO.2 带来三大新能力：`Files` + `Path` 增强、`WatchService` 文件监控、`AsynchronousFileChannel` 异步 IO
- `WatchService` 原理是 OS 级文件事件通知（inotify/kqueue），远优于轮询
- `FileVisitor` 提供目录遍历的完整回调生命周期（进入/访问/失败/离开）
- `AsynchronousFileChannel` 支持 Future 和 CompletionHandler 两种异步模式
- 文件监控的关键操作：`key.reset()` 必须调用，否则不再接收事件
- 回调模式注意主线程不要提前退出
