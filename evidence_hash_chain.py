import hashlib
from pathlib import Path


OUTPUT_NAME = "evidence_hash_chain.txt"
BUFFER_SIZE = 1024 * 1024
ZERO_HASH = "0" * 64


def sha256_file(file_path: Path) -> str:
    """Calculate the SHA-256 digest of a file."""
    hasher = hashlib.sha256()

    with file_path.open("rb") as file:
        while True:
            data = file.read(BUFFER_SIZE)

            if not data:
                break

            hasher.update(data)

    return hasher.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Calculate the SHA-256 digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def chain_hash(
    index: int,
    relative_path: str,
    file_hash: str,
    previous_chain_hash: str,
) -> str:
    """Create a chained hash that includes the previous chain state."""
    payload = (
        f"{index}\n"
        f"{relative_path}\n"
        f"{file_hash}\n"
        f"{previous_chain_hash}\n"
    ).encode("utf-8")

    return sha256_bytes(payload)


def merkle_leaf(relative_path: str, file_hash: str) -> bytes:
    """Create a domain-separated Merkle leaf."""
    payload = (
        b"\x00"
        + relative_path.encode("utf-8")
        + b"\x00"
        + bytes.fromhex(file_hash)
    )
    return hashlib.sha256(payload).digest()


def merkle_root(items: list[tuple[str, str]]) -> str:
    """Calculate a SHA-256 Merkle Root for file paths and file hashes."""
    if not items:
        return ZERO_HASH

    level = [merkle_leaf(path, file_hash) for path, file_hash in items]

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])

        next_level = []

        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1]
            parent = hashlib.sha256(b"\x01" + left + right).digest()
            next_level.append(parent)

        level = next_level

    return level[0].hex()


def wait_for_exit() -> None:
    """Keep the console window open until Enter is pressed."""
    try:
        input("\nPress Enter to exit...")
    except (EOFError, KeyboardInterrupt):
        pass


def main() -> None:
    print("Evidence File SHA-256 Chain Integrity Tool")
    print("Output: file hash + previous chain hash + current chain hash + Merkle Root")
    print()

    try:
        directory_input = input("Enter the evidence directory: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return

    directory_input = directory_input.strip('"').strip("'")

    if not directory_input:
        print("\nError: no directory was provided.")
        wait_for_exit()
        return

    try:
        directory = Path(directory_input).expanduser().resolve()
    except Exception as exc:
        print(f"\nError: unable to resolve the directory: {exc}")
        wait_for_exit()
        return

    if not directory.exists():
        print("\nError: the directory does not exist.")
        wait_for_exit()
        return

    if not directory.is_dir():
        print("\nError: the provided path is not a directory.")
        wait_for_exit()
        return

    output_file = directory / OUTPUT_NAME
    files = []

    try:
        for file_path in sorted(
            directory.rglob("*"),
            key=lambda path: str(path.relative_to(directory)).lower(),
        ):
            if not file_path.is_file():
                continue

            if file_path.resolve() == output_file.resolve():
                continue

            if file_path.name == "evidence_hashes.txt":
                continue

            files.append(file_path)
    except Exception as exc:
        print(f"\nError: failed to scan the directory: {exc}")
        wait_for_exit()
        return

    if not files:
        print("\nNo files were found in the directory.")
        wait_for_exit()
        return

    print(f"\nFound {len(files)} file(s).")
    print("Calculating hashes and integrity structures...\n")

    records = []
    previous_chain_hash = ZERO_HASH

    for index, file_path in enumerate(files, start=1):
        relative_path = file_path.relative_to(directory).as_posix()
        print(f"[{index}/{len(files)}] {relative_path}")

        try:
            file_hash = sha256_file(file_path)
        except Exception as exc:
            print(f"\nError: unable to read file: {relative_path}")
            print(f"Reason: {exc}")
            print("Chain mode requires every file to be read successfully.")
            print("No result file was generated.")
            wait_for_exit()
            return

        current_chain_hash = chain_hash(
            index,
            relative_path,
            file_hash,
            previous_chain_hash,
        )

        records.append(
            (
                index,
                relative_path,
                file_hash,
                previous_chain_hash,
                current_chain_hash,
            )
        )

        previous_chain_hash = current_chain_hash

    root = merkle_root(
        [(path, file_hash) for _, path, file_hash, _, _ in records]
    )
    chain_tip = records[-1][4]

    try:
        with output_file.open("w", encoding="utf-8", newline="\n") as file:
            file.write("Evidence File SHA-256 Chain Integrity Manifest\n")
            file.write("=" * 80 + "\n")
            file.write(f"File Count: {len(records)}\n")
            file.write("Hash Algorithm: SHA-256\n")
            file.write(f"Merkle Root: {root}\n")
            file.write(f"Chain Tip: {chain_tip}\n")
            file.write("=" * 80 + "\n\n")

            for index, path, file_hash, previous_hash, current_hash in records:
                file.write(f"[{index}]\n")
                file.write(f"File: {path}\n")
                file.write(f"SHA-256: {file_hash}\n")
                file.write(f"Previous Chain Hash: {previous_hash}\n")
                file.write(f"Current Chain Hash: {current_hash}\n\n")
    except Exception as exc:
        print(f"\nError: failed to write the output file: {exc}")
        wait_for_exit()
        return

    print("\nCompleted.")
    print(f"Merkle Root: {root}")
    print(f"Chain Tip: {chain_tip}")
    print(f"TXT saved to: {output_file}")

    wait_for_exit()


if __name__ == "__main__":
    main()
