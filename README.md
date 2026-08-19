# 🔐 Evidence Hash Tool

<p align="center">
  <strong>Local SHA-256 file integrity verification with optional hash chaining and Merkle Root support.</strong>
</p>

<p align="center">
  🖥️ Local only · 🔒 No uploads · 📦 No third-party dependencies · 🌍 Cross-platform · 📄 MIT License
</p>

---

## 📌 Overview

**Evidence Hash Tool** is a lightweight local utility for generating integrity records for files.

It is designed for evidence preservation, archives, backups, exports, documents, images, videos, and other files where you want a reproducible SHA-256 record.

The project provides two modes:

| Mode | Script | Output | Purpose |
|---|---|---|---|
| 🔹 Simple | `evidence_hash_simple.py` | `evidence_hashes.txt` | File path + SHA-256 |
| 🔗 Chain | `evidence_hash_chain.py` | `evidence_hash_chain.txt` | SHA-256 + hash chain + Merkle Root |

Both modes:

- ✅ run entirely on your local computer;
- ✅ recursively scan the selected directory;
- ✅ calculate SHA-256 using Python's built-in `hashlib`;
- ✅ do not upload any file;
- ✅ do not modify the original files;
- ✅ do not create one `.sha256` file for every file;
- ✅ generate only one TXT manifest;
- ✅ require no third-party Python packages.

---

## ✨ Features

### 🔹 Simple SHA-256 Mode

The simple mode creates:

```text
evidence_hashes.txt
```

For every file, it records:

```text
relative file path
SHA-256
```

This mode is useful when you only want a clean and readable list of file hashes.

### 🔗 Hash Chain + Merkle Root Mode

The chain mode creates:

```text
evidence_hash_chain.txt
```

For every file, it records:

```text
File
SHA-256
Previous Chain Hash
Current Chain Hash
```

The same TXT file also stores:

```text
Merkle Root
Chain Tip
```

Conceptually:

```text
File 1 + File Hash + 0000...
              │
              ▼
          Chain Hash 1

File 2 + File Hash + Chain Hash 1
              │
              ▼
          Chain Hash 2

File 3 + File Hash + Chain Hash 2
              │
              ▼
          Chain Hash 3
```

Each later chain hash indirectly commits to all earlier chain states.

The final `Chain Tip` represents the final ordered state of the manifest.

The `Merkle Root` represents the complete set of file paths and file hashes.

> The design is inspired by cryptographic hash chains and Merkle trees used in systems such as Bitcoin. This project is not an implementation of the Bitcoin protocol, and its Merkle Root format is not intended to reproduce a Bitcoin block Merkle Root.

---

## 🚀 Usage

```bash
git clone https://github.com/username/evidence-hash-tool.git

cd evidence-hash-tool

python evidence_hash_simple.py
```

Replace `username` with your GitHub username.

After startup, enter the directory that contains the files you want to hash.

Example:

```text
D:\Evidence
```

The program will create:

```text
evidence_hashes.txt
```

inside that directory.

---

## 📄 Example: Final TXT Output

Assume the directory contains:

```text
Evidence/
├── screenshots/
│   ├── account-page.png
│   └── message-001.png
├── videos/
│   └── screen-recording.mp4
└── documents/
    └── export.pdf
```

The generated `evidence_hashes.txt` may look like this:

```text
documents/export.pdf
0b9d8b9d15e7f3a9c31c4eac3cd20f1da6b60986396ea68ab32dbab5830a6a46

screenshots/account-page.png
1a94c9ec8f7899d3451bf8ef10ee6e391f344db406960ca5766645058b42db75

screenshots/message-001.png
fc479ccf74b58fdd60a373963efd07130c9f4aac0bde4912f47e88f841ec9f37

videos/screen-recording.mp4
839f83338cb0e778f3215ee2f06b8168118ac02f64323131694669173d0d1c8d
```

The format is intentionally simple:

```text
FILE NAME
SHA-256

FILE NAME
SHA-256
```

No separate `.sha256` files are created.

---

## 📄 Example: Chain TXT Output

Running `evidence_hash_chain.py` creates:

```text
evidence_hash_chain.txt
```

A final file may look like this:

```text
Evidence File SHA-256 Chain Integrity Manifest
================================================================================
File Count: 3
Hash Algorithm: SHA-256
Merkle Root: 9742010e059bd82fe5ca4fe1c5f2864790562af87bd4366630bfd60c51421b7b
Chain Tip: 7d4f626239df224f96cd6662812471789098544809fd98a34328ea3e99e46020
================================================================================

[1]
File: documents/export.pdf
SHA-256: 0b9d8b9d15e7f3a9c31c4eac3cd20f1da6b60986396ea68ab32dbab5830a6a46
Previous Chain Hash: 0000000000000000000000000000000000000000000000000000000000000000
Current Chain Hash: b1f4304277f02448068351c133f97570756e14a27108c1ecebddbb6bab2ee39b

[2]
File: screenshots/account-page.png
SHA-256: 1a94c9ec8f7899d3451bf8ef10ee6e391f344db406960ca5766645058b42db75
Previous Chain Hash: b1f4304277f02448068351c133f97570756e14a27108c1ecebddbb6bab2ee39b
Current Chain Hash: f880eef735952049d59df5e9f49a34d13886efea3d88c45f43b575bc82c8e574

[3]
File: screenshots/message-001.png
SHA-256: fc479ccf74b58fdd60a373963efd07130c9f4aac0bde4912f47e88f841ec9f37
Previous Chain Hash: f880eef735952049d59df5e9f49a34d13886efea3d88c45f43b575bc82c8e574
Current Chain Hash: 7d4f626239df224f96cd6662812471789098544809fd98a34328ea3e99e46020
```

The values above are examples showing the final file format.

Actual hashes depend on the exact contents and paths of your files.

---

## 🧱 Project Structure

```text
evidence-hash-tool/
├── evidence_hash_simple.py
├── evidence_hash_chain.py
├── README.md
├── SECURITY.md
├── LICENSE
└── .gitignore
```

---

## 🧮 How Simple Mode Works

For each file:

```text
SHA256(file bytes)
```

The manifest stores:

```text
relative file path
file SHA-256
```

If even one byte changes, the SHA-256 value will normally change completely.

---

## 🔗 How Chain Mode Works

For each file, the program first calculates the file SHA-256.

It then calculates a chain hash from:

```text
record index
relative file path
file SHA-256
previous chain hash
```

The first record uses 64 zeroes as its previous chain hash.

Every later record uses the previous record's current chain hash.

A change to an earlier record will normally change that record's chain hash and all later chain hashes.

---

## 🌳 Merkle Root

The chain mode also creates a SHA-256 Merkle Tree.

Each leaf commits to:

```text
relative file path + file SHA-256
```

The leaves are combined in pairs until only one final hash remains:

```text
               Merkle Root
                /       \
               /         \
           Parent       Parent
           /   \         /   \
        Leaf   Leaf   Leaf   Leaf
```

That final hash is stored as the `Merkle Root`.

---

## 🧾 What SHA-256 Can Verify

A SHA-256 digest can help verify whether a file is byte-for-byte identical to the file that originally produced the stored digest.

It can help detect:

- modification;
- corruption;
- accidental editing;
- replacement;
- incomplete copying;
- backup mismatch.

The chain mode additionally provides a single `Chain Tip` and `Merkle Root` that can be preserved separately for later comparison.

---

## ⚠️ What Hashing Alone Cannot Prove

A local SHA-256 hash does not, by itself, prove:

- when a file originally existed;
- who created the file;
- whether the content is factually true;
- whether the file was modified before the first hash was generated;
- whether the local TXT manifest was later replaced.

For important records, preserve the final `Merkle Root` or `Chain Tip` in an independent location.

Possible external anchoring methods include trusted timestamp services, digital signatures, append-only public logs, Nostr publication, or Bitcoin-based timestamp anchoring.

Only the digest needs to be anchored externally. The original evidence files do not need to be published.

---

## 🔒 Privacy

The program:

- 🚫 does not connect to the Internet;
- 🚫 does not upload evidence;
- 🚫 does not delete evidence;
- 🚫 does not modify original file contents;
- 🚫 does not require an account;
- 🚫 does not require administrator privileges;
- 🚫 does not require third-party Python packages.

All hashing is performed locally.

---

## ♻️ Reproducibility

Files are sorted by relative path before hashing.

Relative paths are written using `/`.

Repeated runs should produce the same file hashes, Merkle Root, and Chain Tip when the same files, paths, contents, and hashing rules are used.

The generated output files are excluded from later scans:

```text
evidence_hashes.txt
evidence_hash_chain.txt
```

This prevents the manifests from hashing themselves.

---

## 📄 License

This project is released under the **MIT License**.

See [`LICENSE`](LICENSE) for the complete license text.

---

## ⚖️ Disclaimer

This software is provided for integrity checking and evidence organization.

It is not legal advice, forensic certification, a trusted timestamp service, or a substitute for formal evidence-handling procedures.
