import hashlib
from pathlib import Path


OUTPUT_NAME = "evidence_hashes.txt"
BUFFER_SIZE = 1024 * 1024


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


def wait_for_exit() -> None:
    """Keep the console window open until Enter is pressed."""
    try:
        input("\nPress Enter to exit...")
    except (EOFError, KeyboardInterrupt):
        pass


def main() -> None:
    print("Evidence File SHA-256 Hash Tool")
    print("Output: file name + SHA-256")
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

            if file_path.name == "evidence_hash_chain.txt":
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
    print("Calculating SHA-256 hashes...\n")

    results = []

    for index, file_path in enumerate(files, start=1):
        relative_path = file_path.relative_to(directory).as_posix()
        print(f"[{index}/{len(files)}] {relative_path}")

        try:
            file_hash = sha256_file(file_path)
            results.append((relative_path, file_hash))
        except Exception as exc:
            results.append((relative_path, f"ERROR: {exc}"))

    try:
        with output_file.open("w", encoding="utf-8", newline="\n") as file:
            for relative_path, file_hash in results:
                file.write(f"{relative_path}\n")
                file.write(f"{file_hash}\n\n")
    except Exception as exc:
        print(f"\nError: failed to write the output file: {exc}")
        wait_for_exit()
        return

    print("\nCompleted.")
    print(f"TXT saved to: {output_file}")

    wait_for_exit()


if __name__ == "__main__":
    main()
