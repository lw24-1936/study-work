---
title: Excel
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [excel, apache-poi, easyexcel, excel导入, excel导出, 大文件excel, 流式excel, excel模板]
---

# Excel

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [Apache POI](#apache-poi)
- [EasyExcel](#easyexcel)
- [Excel 导入](#excel-导入)
- [Excel 导出](#excel-导出)
- [大文件 Excel 处理](#大文件-excel-处理)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Java 处理 Excel 是办公自动化的常见需求，核心是导入（读）和导出（写）。

```text
两大方案：
1. Apache POI —— 底层 API，功能全，内存占用高
2. EasyExcel（阿里）—— 封装 POI，内存占用低，适合大文件
```

```text
POI vs EasyExcel：
POI —— 灵活但繁琐，大文件 OOM 风险
EasyExcel —— 简单易用，流式处理，大文件推荐
```

## Apache POI

Apache POI 是 Java 操作 Office 文档的标准库。

### 依赖

```xml
<dependency>
    <groupId>org.apache.poi</groupId>
    <artifactId>poi-ooxml</artifactId>
    <version>5.2.5</version>
</dependency>
```

### 基本概念

```text
Workbook（工作簿）—— 一个 Excel 文件
Sheet（工作表）—— 工作簿中的一页
Row（行）—— 一行数据
Cell（单元格）—— 一个格子
```

### 读取 Excel

```java
try (FileInputStream fis = new FileInputStream("data.xlsx");
     Workbook workbook = new XSSFWorkbook(fis)) {

    Sheet sheet = workbook.getSheetAt(0);   // 第一个 sheet

    for (Row row : sheet) {
        for (Cell cell : row) {
            String value = getCellValue(cell);
            System.out.print(value + "\t");
        }
        System.out.println();
    }
}
```

### 写入 Excel

```java
try (Workbook workbook = new XSSFWorkbook()) {
    Sheet sheet = workbook.createSheet("用户数据");

    // 表头
    Row header = sheet.createRow(0);
    header.createCell(0).setCellValue("姓名");
    header.createCell(1).setCellValue("年龄");

    // 数据
    Row row1 = sheet.createRow(1);
    row1.createCell(0).setCellValue("张三");
    row1.createCell(1).setCellValue(20);

    try (FileOutputStream fos = new FileOutputStream("out.xlsx")) {
        workbook.write(fos);
    }
}
```

### 单元格类型处理

```java
private String getCellValue(Cell cell) {
    if (cell == null) return "";
    switch (cell.getCellType()) {
        case STRING: return cell.getStringCellValue();
        case NUMERIC:
            if (DateUtil.isCellDateFormatted(cell)) {
                return cell.getDateCellValue().toString();  // 日期
            }
            return String.valueOf(cell.getNumericCellValue());
        case BOOLEAN: return String.valueOf(cell.getBooleanCellValue());
        case FORMULA: return cell.getCellFormula();
        default: return "";
    }
}
```

### POI 的局限

```text
1. 内存占用高 —— XSSFWorkbook 全量加载到内存
2. 大文件 OOM —— 几万行数据可能内存溢出
3. API 繁琐 —— 手动处理每个单元格
```

## EasyExcel

EasyExcel 是阿里的 Excel 处理库，基于 POI 封装，内存占用极低。

### 依赖

```xml
<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>easyexcel</artifactId>
    <version>3.3.4</version>
</dependency>
```

### 实体类 + 注解

```java
@Data
public class UserExcel {
    @ExcelProperty("姓名")     // 对应 Excel 列
    private String name;

    @ExcelProperty("年龄")
    private Integer age;

    @ExcelProperty(value = "创建时间", format = "yyyy-MM-dd HH:mm:ss")
    private Date createTime;

    @ExcelIgnore               // 忽略该字段
    private String password;
}
```

### 读取 Excel

```java
// 方式 1：读所有（小文件）
List<UserExcel> list = EasyExcel.read("data.xlsx")
    .head(UserExcel.class)
    .sheet()
    .doReadSync();

// 方式 2：监听器（大文件流式读）
EasyExcel.read("data.xlsx", UserExcel.class,
    new ReadListener<UserExcel>() {
        @Override
        public void invoke(UserExcel data, AnalysisContext context) {
            // 每读一行处理一行（不全部加载内存）
            process(data);
        }

        @Override
        public void doAfterAllAnalysed(AnalysisContext context) {
            // 读取完成
        }
    }).sheet().doRead();
```

### 写入 Excel

```java
List<UserExcel> users = getUsers();

EasyExcel.write("out.xlsx", UserExcel.class)
    .sheet("用户数据")
    .doWrite(users);
```

### 大文件写入（流式）

```java
try (ExcelWriter writer = EasyExcel.write("out.xlsx", UserExcel.class).build()) {
    WriteSheet sheet = EasyExcel.writerSheet("用户数据").build();

    // 分批写入（每次 1000 条）
    for (int i = 0; i < totalBatches; i++) {
        List<UserExcel> batch = getBatch(i, 1000);
        writer.write(batch, sheet);
    }
}
```

## Excel 导入

Excel 导入是读取 Excel 数据写入数据库。

### 导入流程

```text
1. 上传 Excel 文件
2. 解析 Excel（EasyExcel 流式读）
3. 数据校验（格式、必填、唯一性）
4. 写入数据库（批量）
5. 返回导入结果（成功/失败统计）
```

### 完整导入实现

```java
@PostMapping("/import")
public ImportResult importExcel(MultipartFile file) throws IOException {
    List<UserExcel> list = new ArrayList<>();
    List<String> errors = new ArrayList<>();

    EasyExcel.read(file.getInputStream(), UserExcel.class,
        new ReadListener<UserExcel>() {
            @Override
            public void invoke(UserExcel data, AnalysisContext context) {
                // 校验
                if (StringUtils.isEmpty(data.getName())) {
                    errors.add("第 " + context.readRowHolder().getRowIndex() + " 行姓名不能为空");
                    return;
                }
                list.add(data);
            }

            @Override
            public void doAfterAllAnalysed(AnalysisContext context) {
                // 批量入库
                userService.batchInsert(list);
            }
        }).sheet().doRead();

    ImportResult result = new ImportResult();
    result.setSuccessCount(list.size());
    result.setErrors(errors);
    return result;
}
```

### 导入的常见问题

```text
1. 数据校验 —— 必填、格式、唯一性
2. 批量入库 —— 分批（1000 条一批）
3. 错误反馈 —— 返回哪行出错
4. 重复导入 —— 唯一键去重
```

## Excel 导出

Excel 导出是查询数据写入 Excel 下载。

### 导出流程

```text
1. 查询数据（分页查询，避免一次加载全部）
2. 写入 Excel（EasyExcel 流式写）
3. 响应下载（设置 Content-Disposition）
```

### 完整导出实现

```java
@GetMapping("/export")
public void export(HttpServletResponse response) throws IOException {
    response.setContentType("application/vnd.ms-excel");
    response.setCharacterEncoding("utf-8");
    String fileName = URLEncoder.encode("用户数据", "UTF-8");
    response.setHeader("Content-Disposition",
        "attachment;filename=" + fileName + ".xlsx");

    try (ExcelWriter writer = EasyExcel.write(response.getOutputStream(), UserExcel.class).build()) {
        WriteSheet sheet = EasyExcel.writerSheet("用户数据").build();

        // 分页查询 + 分批写入
        int page = 0;
        int size = 1000;
        while (true) {
            List<User> users = userService.listByPage(page++, size);
            if (users.isEmpty()) break;
            writer.write(convertToExcel(users), sheet);
        }
    }
}
```

## 大文件 Excel 处理

大文件（几万到几十万行）用流式处理，避免 OOM。

### 大文件读取

```java
// 流式读：逐行处理，不全部加载内存
EasyExcel.read(file, UserExcel.class, new ReadListener<UserExcel>() {
    @Override
    public void invoke(UserExcel data, AnalysisContext context) {
        process(data);   // 逐行处理
    }

    @Override
    public void doAfterAllAnalysed(AnalysisContext context) { }
}).sheet().doRead();
```

### 大文件写入

```java
// 流式写：分批写入
try (ExcelWriter writer = EasyExcel.write("out.xlsx", UserExcel.class).build()) {
    WriteSheet sheet = EasyExcel.writerSheet().build();
    // 分批，每批 1000 条
    for (List<UserExcel> batch : batches) {
        writer.write(batch, sheet);
    }
}
```

### POI 的大文件处理

```java
// POI 的 SAX 模式（SXSSFWorkbook）流式写
SXSSFWorkbook workbook = new SXSSFWorkbook(100);   // 内存中保留 100 行
// 超过 100 行写临时文件，避免 OOM
```

```text
大文件处理原则：
1. 读：EasyExcel 监听器（逐行）或 POI SAX
2. 写：EasyExcel 流式写或 POI SXSSF
3. 不要一次性加载全部数据到内存
```

## 应用场景实战

### 场景 1：用户数据导入导出

```java
@RestController
@RequestMapping("/api/users")
public class UserExcelController {

    @PostMapping("/import")
    public Result importExcel(MultipartFile file) {
        // 导入（含校验 + 批量入库）
        List<User> users = excelService.importUsers(file);
        return Result.success("导入成功 " + users.size() + " 条");
    }

    @GetMapping("/export")
    public void export(HttpServletResponse response) {
        // 导出（分页查询 + 流式写）
        excelService.exportUsers(response);
    }
}
```

### 场景 2：Excel 模板导出

```java
// 用模板填充数据
// 1. 准备模板文件（带样式）
// 2. 读取模板，填充数据
String templatePath = "template.xlsx";

try (InputStream in = new FileInputStream(templatePath);
     Workbook workbook = new XSSFWorkbook(in)) {
    Sheet sheet = workbook.getSheetAt(0);
    // 填充数据
    sheet.getRow(2).getCell(0).setCellValue("张三");
    // 写出
    workbook.write(new FileOutputStream("out.xlsx"));
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **大文件用 EasyExcel**。POI 全量加载会 OOM，EasyExcel 流式处理。

2. **导入要校验**。必填、格式、唯一性校验，返回错误明细。

3. **批量入库**。分批（1000 条），不用逐条 insert。

4. **导出分页查询**。避免一次查询全部数据。

5. **日期格式处理**。@ExcelProperty 指定 format，或统一日期处理。

### 踩坑记录

**坑 1：POI 大文件 OOM**

```java
XSSFWorkbook workbook = new XSSFWorkbook(fis);   // 全量加载，几万行 OOM
```

大文件用 EasyExcel 或 POI SXSSF/SAX 模式。

**坑 2：数字变科学计数法**

```text
长数字（如身份证号、手机号）被 Excel 显示为科学计数法
```

用字符串类型，或加文本格式前缀。

**坑 3：日期格式混乱**

```text
POI 读日期得到数字（天数），需要判断 DateUtil.isCellDateFormatted
```

用 EasyExcel 的 @ExcelProperty(format = "yyyy-MM-dd")。

**坑 4：中文文件名乱码**

```java
response.setHeader("Content-Disposition", "attachment;filename=" + fileName);
// 中文文件名乱码
```

用 URLEncoder.encode(fileName, "UTF-8") 编码。

**坑 5：导入没做数据校验**

```text
导入脏数据（空值、格式错误）直接入库，污染数据库
```

导入必须校验 + 错误反馈。

**坑 6：EasyExcel 实体字段顺序**

```text
@ExcelProperty("姓名") 的字段顺序和 Excel 列不对应
```

用 @ExcelProperty(index = 0) 指定列索引，或保证顺序一致。
