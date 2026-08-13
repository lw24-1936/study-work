#!/usr/bin/env python3
"""前端知识库进度管理脚本

用法:
  progress.py next                    # 找下一篇待编写文档，输出 JSON
  progress.py done <path> <summary>   # 标记完成：更新 README/index/log，清理空目录，释放锁

自然排序：按 (篇章号, 子序号) 数字排序，避免 "01.10" 排在 "01.2" 前面。
"""
import os, re, sys, json, time, datetime

ROOT = "/opt/study-work/frontend-fullstack"
INDEX = "/opt/study-work/index.md"
LOG = "/opt/study-work/log.md"
LOCK = "/tmp/frontend-doc-writer.lock"
LOCK_TIMEOUT = 1800  # 30 分钟，超时视为残留锁

def today():
    return datetime.date.today().isoformat()

def natural_key(fname):
    m = re.match(r'^(\d+)\.(\d+)-', fname)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return (9999, 9999)

def find_next():
    cands = []
    for dirpath, _, filenames in os.walk(ROOT):
        for fn in filenames:
            if fn == "README.md" or not fn.endswith(".md"):
                continue
            full = os.path.join(dirpath, fn)
            try:
                with open(full, encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            if "状态：待编写" in content:
                cands.append(full)
    if not cands:
        return None
    cands.sort(key=lambda p: natural_key(os.path.basename(p)))
    return cands[0]

def cmd_next():
    # 锁检查
    if os.path.exists(LOCK):
        if time.time() - os.path.getmtime(LOCK) < LOCK_TIMEOUT:
            print(json.dumps({"skip": True, "message": "上一个任务仍在进行"}, ensure_ascii=False))
            return
        os.remove(LOCK)  # 残留锁，清除
    p = find_next()
    if p is None:
        print(json.dumps({"done": True, "message": "全部完成"}, ensure_ascii=False))
        return
    chapter = os.path.basename(os.path.dirname(p))
    fname = os.path.basename(p)
    with open(p, encoding="utf-8") as f:
        first_lines = f.read(500)
    m = re.search(r'^title: (.+)$', first_lines, re.M)
    title = m.group(1).strip() if m else fname
    with open(LOCK, "w") as f:
        f.write(p)
    print(json.dumps({
        "done": False, "path": p, "filename": fname,
        "chapter": chapter, "title": title
    }, ensure_ascii=False))

def clean_empty_dirs():
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=False):
        for d in dirnames:
            full = os.path.join(dirpath, d)
            try:
                os.rmdir(full)
            except OSError:
                pass

def update_readme(chapter):
    readme = os.path.join(ROOT, "README.md")
    with open(readme, encoding="utf-8") as f:
        content = f.read()
    old = f"| {chapter} | 待编写 | - |"
    new = f"| {chapter} | 已完成 | {today()} |"
    if old in content:
        content = content.replace(old, new)
        with open(readme, "w", encoding="utf-8") as f:
            f.write(content)

def update_index(fname, summary, chapter):
    with open(INDEX, encoding="utf-8") as f:
        content = f.read()
    marker = "## 前端知识库"
    if marker not in content:
        print("index.md 缺少「前端知识库」节", file=sys.stderr)
        return
    wiki = fname.replace(".md", "")
    entry = f"- [[{wiki}]] — {summary}"
    section = f"### {chapter}"
    start = content.index(marker)
    nxt = content.find("\n## ", start + len(marker))
    if nxt == -1:
        nxt = len(content)
    seg = content[start:nxt]
    if section in seg:
        # 已有该篇章小节，追加到条目列表末尾（该小节内最后一个条目之后）
        sec_start = seg.index(section)
        after_sec = seg[sec_start:]
        # 找到下一小节或节尾
        m = re.search(r'\n### ', after_sec[len(section):])
        if m:
            insert_pos = sec_start + len(section) + m.start()
        else:
            insert_pos = len(seg)
        new_seg = seg[:insert_pos].rstrip() + "\n" + entry + "\n" + seg[insert_pos:]
    else:
        new_seg = seg.rstrip() + f"\n\n{section}\n\n{entry}\n"
    content = content[:start] + new_seg + content[nxt:]
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(content)

def update_log(fname, title, summary):
    entry = f"\n## [{today()}] create | 前端文档 {title}\n\n- 文件名：{fname}\n- 摘要：{summary}\n"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(entry)

def cmd_done(path, summary):
    chapter = os.path.basename(os.path.dirname(path))
    fname = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'^title: (.+)$', content, re.M)
    title = m.group(1).strip() if m else fname
    update_readme(chapter)
    update_index(fname, summary, chapter)
    update_log(fname, title, summary)
    clean_empty_dirs()
    if os.path.exists(LOCK):
        os.remove(LOCK)
    print(json.dumps({"ok": True, "chapter": chapter, "title": title}, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "next":
        cmd_next()
    elif sys.argv[1] == "done" and len(sys.argv) >= 4:
        cmd_done(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
