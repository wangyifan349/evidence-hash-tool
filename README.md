# Evidence Hash Tool

<p align="center">
  <strong>Local SHA-256 evidence hashing with optional hash chaining and Merkle Root.</strong>
</p>

<p align="center">
  No uploads · No third-party dependencies · Cross-platform · MIT licensed
</p>

---

## Overview

**Evidence Hash Tool** is a small local utility for creating integrity records for evidence files, archives, backups, exports, documents, images, videos, and other data.

It provides two operating modes:

| Mode | Script | Output | Purpose |
|---|---|---|---|
| Simple | `evidence_hash_simple.py` | `evidence_hashes.txt` | File path + SHA-256 |
| Chain | `evidence_hash_chain.py` | `evidence_hash_chain.txt` | SHA-256 + hash chain + Merkle Root |

Both modes:

- run entirely on the local machine;
- recursively scan the selected directory;
- do not upload files;
- do not modify original evidence files;
- do not create one `.sha256` file per item;
- produce only one TXT manifest;
- use only the Python standard library.

---

## Why this project exists

For evidence preservation, file archiving, backup verification, or later timestamp anchoring, it is useful to keep a compact integrity record for every file.

The **Simple mode** creates a readable list containing each relative file path and its SHA-256 digest.

The **Chain mode** additionally links each record to the previous record and calculates a Merkle Root for the entire file set. When compared with a previously preserved result, this makes deletion, insertion, reordering, replacement, or modification easier to detect.

> This project is inspired by hash-chain and Merkle-tree concepts used in cryptographic systems. It is **not** an implementation of the Bitcoin protocol, and its Merkle Root encoding is not intended to match Bitcoin block construction.

---

## Features

### Simple mode

Creates:

```text
evidence_hashes.txt
```

Each entry contains:

```text
relative file path
SHA-256
```

Example:

```text
photos/001.jpg
ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f

video/record.mp4
c0535e4be2b79ffd93291305436bf889314e4a3faec05ecffcbb7df31a71335c
```

### Chain mode

Creates:

```text
evidence_hash_chain.txt
```

Each record contains:

```text
File
SHA-256
Previous Chain Hash
Current Chain Hash
```

The header also contains:

```text
Merkle Root
Chain Tip
```

Conceptually, the chain works like this:

```text
File 1 + SHA-256 + 0000...
          |
          v
      Chain Hash 1

File 2 + SHA-256 + Chain Hash 1
          |
          v
      Chain Hash 2

File 3 + SHA-256 + Chain Hash 2
          |
          v
      Chain Hash 3
```

Each later chain hash therefore commits to the previous chain state.

The final `Chain Tip` represents the ordered chain state of the complete manifest.

The `Merkle Root` represents the complete set of:

```text
relative file path + file SHA-256
```

---

## Requirements

Python 3.8 or newer.

Check your Python version:

```bash
python3 --version
```

On Windows:

```powershell
python --version
```

No `pip install` is required.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/username/evidence-hash-tool.git
cd evidence-hash-tool
```

Replace `username` with your GitHub username.

Repository format:

```text
github.com/username/evidence-hash-tool
```

---

## Usage

### Simple SHA-256 manifest

Linux / macOS:

```bash
python3 evidence_hash_simple.py
```

Windows:

```powershell
python evidence_hash_simple.py
```

The program will ask:

```text
Enter the evidence directory:
```

Example:

```text
D:\Evidence
```

Windows paths copied with quotation marks are also accepted:

```text
"D:\Evidence"
```

The output file will be created inside the selected directory:

```text
D:\Evidence\evidence_hashes.txt
```

---

### Hash chain + Merkle Root

Linux / macOS:

```bash
python3 evidence_hash_chain.py
```

Windows:

```powershell
python evidence_hash_chain.py
```

The output file will be:

```text
D:\Evidence\evidence_hash_chain.txt
```

The program also prints the final:

```text
Merkle Root
Chain Tip
```

Both values are stored in the same TXT manifest.

---

## Project structure

```text
evidence-hash-tool/
├── evidence_hash_simple.py
├── evidence_hash_chain.py
├── README.md
├── SECURITY.md
├── LICENSE
└── .gitignore
```

No database, web service, account system, package manager, or external dependency is required.

---

## How the simple mode works

For each file:

```text
SHA256(file bytes)
```

The manifest stores:

```text
relative path
file SHA-256
```

If even one byte changes, the SHA-256 digest will normally change completely.

---

## How the chain mode works

For every file, the program calculates the normal file SHA-256 first.

It then creates a chain hash from:

```text
record index
relative file path
file SHA-256
previous chain hash
```

The first record uses:

```text
0000000000000000000000000000000000000000000000000000000000000000
```

as the previous chain hash.

Every later record uses the previous record's current chain hash.

This means a later chain state depends on all earlier chain states.

---

## Merkle Root

The chain mode also creates a SHA-256 Merkle Tree.

Each leaf commits to:

```text
relative file path
file SHA-256
```

The leaves are repeatedly combined in pairs until one final root remains:

```text
           Merkle Root
            /       \
           /         \
        Parent      Parent
        /   \       /   \
      Leaf Leaf   Leaf Leaf
```

If a level contains an odd number of nodes, the final node is duplicated for that level.

The final root is stored as:

```text
Merkle Root: ...
```

---

## Chain Tip

The `Chain Tip` is the final current chain hash.

It represents the final ordered state of the chain.

If the file list, file contents, file paths, or ordering changes, the final `Chain Tip` will normally change.

---

## What SHA-256 can verify

A SHA-256 digest can help verify whether a file is byte-for-byte identical to the file that originally produced the stored digest.

This can help detect:

- file modification;
- file corruption;
- backup mismatch;
- replacement with a different file;
- accidental changes during copying or transfer.

The chain mode can additionally help detect changes to the ordered manifest when the current result is compared with a previously preserved `Chain Tip` or `Merkle Root`.

---

## What hashing alone cannot prove

A locally generated hash does **not**, by itself, prove:

- when the file originally existed;
- who created the file;
- whether the file contents are factually true;
- whether the file was modified before the first hash was generated;
- whether the TXT manifest itself was replaced.

If historical existence matters, preserve the final `Merkle Root` or `Chain Tip` independently.

Possible external anchoring methods include:

- trusted timestamp services;
- digital signatures;
- offline signed records;
- append-only public logs;
- Nostr publication;
- Bitcoin-based timestamp anchoring.

The external system only needs to store or commit to the final digest. The original evidence files do not need to be published.

---

## Privacy and security

This tool is intentionally local and minimal.

It:

- does not connect to the Internet;
- does not upload evidence;
- does not delete evidence;
- does not modify evidence contents;
- does not require administrator privileges;
- does not require third-party Python packages.

Only the generated TXT manifest is written into the selected evidence directory.

For highly important evidence, keep:

1. the original files;
2. the generated TXT manifest;
3. at least one independent backup;
4. the final `Merkle Root` or `Chain Tip` in a separate trusted location.

---

## Reproducibility

File paths are stored as relative paths using `/`.

Files are sorted by relative path before hashing.

Repeated runs should therefore produce the same file hashes, Merkle Root, and Chain Tip when:

- the same files are present;
- the same relative paths are used;
- file contents are unchanged;
- the same hashing rules are used.

---

## Notes about generated TXT files

The scripts intentionally exclude each other's generated TXT output:

```text
evidence_hashes.txt
evidence_hash_chain.txt
```

This prevents the generated manifests from being recursively included in the evidence calculation when both modes are used in the same directory.

---

## License

This project is released under the **MIT License**.

See [`LICENSE`](LICENSE) for the complete license text.

---

## Disclaimer

This software is provided for integrity checking and evidence organization.

It is not legal advice, forensic certification, a trusted timestamp service, or a substitute for formal evidence-handling procedures.
