"""
This tool is designed to batch-calculate and verify SHA-256 hashes for files within a directory. It recursively records each file’s name, relative path, and corresponding hash value, and writes the results to a hash manifest. New records are appended without overwriting existing entries, while verification reads both the manifest and target files in read-only mode, recalculates their hashes, and identifies files that are unchanged, modified, missing, or unreadable. Large files are processed in chunks to avoid loading the entire file into memory.
"""
import hashlib
import os
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

CHUNK_SIZE = 1024 * 1024  # 1 MiB


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:  # 始终只读证据文件
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


class HashSumApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HashSum")
        self.root.geometry("900x620")
        self.folder = tk.StringVar()

        top = ttk.Frame(root, padding=12)
        top.pack(fill="x")

        ttk.Entry(top, textvariable=self.folder).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(top, text="选择目录", command=self.choose_folder).pack(
            side="left", padx=6
        )
        ttk.Button(top, text="生成 / 追加哈希", command=self.start_generate).pack(
            side="left", padx=3
        )
        ttk.Button(top, text="校验", command=self.start_verify).pack(
            side="left", padx=3
        )

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log = tk.Text(notebook, font=("Consolas", 10))
        self.result = tk.Text(notebook, font=("Consolas", 10))

        notebook.add(self.log, text="运行日志")
        notebook.add(self.result, text="校验结果")

        self.status = tk.StringVar(value="就绪")
        ttk.Label(root, textvariable=self.status, anchor="w").pack(
            fill="x", padx=12, pady=(0, 8)
        )

    def choose_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder.set(path)

    def write_log(self, text):
        self.root.after(0, lambda: (
            self.log.insert("end", text + "\n"),
            self.log.see("end")
        ))

    def write_result(self, text):
        self.root.after(0, lambda: (
            self.result.insert("end", text + "\n"),
            self.result.see("end")
        ))

    def set_status(self, text):
        self.root.after(0, self.status.set, text)

    def files(self, folder, manifest):
        for root, _, names in os.walk(folder):
            for name in names:
                path = Path(root) / name

                # 清单文件本身不参与哈希
                if path.resolve() == manifest.resolve():
                    continue

                if path.is_file():
                    yield path

    def start_generate(self):
        folder = self.folder.get().strip()
        if not folder:
            messagebox.showwarning("提示", "请先选择目录")
            return

        manifest = filedialog.asksaveasfilename(
            title="选择或创建哈希清单",
            defaultextension=".sha256",
            filetypes=[("SHA256 清单", "*.sha256"), ("文本文件", "*.txt")]
        )

        if manifest:
            threading.Thread(
                target=self.generate,
                args=(Path(folder), Path(manifest)),
                daemon=True
            ).start()

    def generate(self, folder, manifest):
        self.set_status("正在计算哈希...")
        self.write_log("=" * 60)
        self.write_log(f"目录：{folder}")

        count = 0
        batch = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 只使用追加模式，不覆盖原有记录
        with open(manifest, "a", encoding="utf-8", newline="\n") as out:
            out.write(f"\n# HASH-BATCH {batch}\n")
            out.write(f"# ROOT {folder.resolve()}\n")

            for path in self.files(folder, manifest):
                try:
                    digest = sha256_file(path)
                    relative = path.relative_to(folder).as_posix()

                    out.write(f"{digest}\t{relative}\n")
                    out.flush()

                    count += 1
                    self.write_log(f"[{count}] {relative}")
                except OSError as e:
                    self.write_log(f"[读取失败] {path}: {e}")

        self.set_status(f"完成，共记录 {count} 个文件")

        self.root.after(
            0,
            lambda: messagebox.showinfo(
                "完成",
                f"哈希计算完成\n\n文件数量：{count}\n清单：{manifest}"
            )
        )

    def start_verify(self):
        folder = self.folder.get().strip()
        if not folder:
            messagebox.showwarning("提示", "请先选择证据目录")
            return

        manifest = filedialog.askopenfilename(
            title="选择哈希清单",
            filetypes=[("哈希清单", "*.sha256 *.txt"), ("所有文件", "*.*")]
        )

        if manifest:
            threading.Thread(
                target=self.verify,
                args=(Path(folder), Path(manifest)),
                daemon=True
            ).start()

    def read_latest_batch(self, manifest):
        # 清单只读
        with open(manifest, "r", encoding="utf-8") as f:
            lines = f.readlines()

        start = 0

        # 找最后一次批次
        for i, line in enumerate(lines):
            if line.startswith("# HASH-BATCH "):
                start = i + 1

        records = []

        for line in lines[start:]:
            line = line.rstrip("\n")

            if not line or line.startswith("#"):
                continue

            if "\t" not in line:
                continue

            digest, relative = line.split("\t", 1)
            records.append((digest, relative))

        return records

    def verify(self, folder, manifest):
        self.set_status("正在校验...")
        self.root.after(0, lambda: self.result.delete("1.0", "end"))

        records = self.read_latest_batch(manifest)

        success = 0
        modified = 0
        missing = 0
        errors = 0

        self.write_result("SHA-256 校验结果")
        self.write_result("=" * 70)

        for expected, relative in records:
            path = folder / relative

            if not path.exists():
                missing += 1
                self.write_result(f"[文件丢失] {relative}")
                continue

            try:
                actual = sha256_file(path)

                if actual.lower() == expected.lower():
                    success += 1
                    self.write_result(f"[校验成功] {relative}")
                else:
                    modified += 1
                    self.write_result(
                        f"[文件被修改] {relative}\n"
                        f"  记录值：{expected}\n"
                        f"  当前值：{actual}"
                    )

            except OSError as e:
                errors += 1
                self.write_result(f"[读取失败] {relative}: {e}")

        total = len(records)

        summary = (
            "\n" + "=" * 70 +
            f"\n总记录数：{total}"
            f"\n校验成功：{success}"
            f"\n内容变化：{modified}"
            f"\n文件丢失：{missing}"
            f"\n读取失败：{errors}"
        )

        self.write_result(summary)
        self.set_status("校验完成")

        self.root.after(
            0,
            lambda: messagebox.showinfo(
                "校验完成",
                f"总计：{total}\n"
                f"成功：{success}\n"
                f"修改：{modified}\n"
                f"丢失：{missing}\n"
                f"失败：{errors}"
            )
        )


root = tk.Tk()
HashSumApp(root)
root.mainloop()


