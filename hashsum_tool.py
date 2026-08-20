import hashlib
import hmac
from pathlib import Path


OUTPUT_NAME = "evidence_hashes.txt"
CHAIN_OUTPUT_NAME = "evidence_hash_chain.txt"
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


def get_directory() -> Path | None:
    """Read and validate the evidence directory."""
    try:
        directory_input = input("Enter the evidence directory: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return None

    directory_input = directory_input.strip('"').strip("'")
    if not directory_input:
        print("\nError: no directory was provided.")
        return None

    try:
        directory = Path(directory_input).expanduser().resolve()
    except Exception as exc:
        print(f"\nError: unable to resolve the directory: {exc}")
        return None

    if not directory.exists():
        print("\nError: the directory does not exist.")
        return None
    if not directory.is_dir():
        print("\nError: the provided path is not a directory.")
        return None

    return directory


def collect_files(directory: Path) -> list[Path]:
    """Return files in stable relative-path order, excluding tool manifests."""
    excluded_names = {OUTPUT_NAME, CHAIN_OUTPUT_NAME}
    files = []

    for file_path in sorted(
        directory.rglob("*"),
        key=lambda path: path.relative_to(directory).as_posix(),
    ):
        if not file_path.is_file():
            continue
        if file_path.name in excluded_names:
            continue
        files.append(file_path)

    return files


def generate_manifest(directory: Path) -> None:
    """Append new path + SHA-256 records without inserting exact duplicates."""
    output_file = directory / OUTPUT_NAME

    try:
        files = collect_files(directory)
        existing_records = load_manifest(output_file) if output_file.is_file() else []
    except Exception as exc:
        print(f"\nError: failed to scan or read the existing manifest: {exc}")
        return

    if not files:
        print("\nNo files were found in the directory.")
        return

    existing_pairs = set(existing_records)
    print(f"\nFound {len(files)} file(s).")
    print(f"Loaded {len(existing_pairs)} unique existing record(s).")
    print("Calculating SHA-256 hashes...\n")

    new_records = []
    skipped_count = 0
    error_count = 0

    for index, file_path in enumerate(files, start=1):
        relative_path = file_path.relative_to(directory).as_posix()
        print(f"[{index}/{len(files)}] {relative_path}", end=": ")
        try:
            file_hash = sha256_file(file_path)
            record = (relative_path, file_hash)
            if record in existing_pairs:
                skipped_count += 1
                print("SKIPPED (already recorded)")
                continue

            new_records.append(record)
            existing_pairs.add(record)
            print("APPEND")
        except Exception as exc:
            error_count += 1
            print(f"ERROR ({exc})")

    try:
        if new_records:
            needs_separator = output_file.is_file() and output_file.stat().st_size > 0
            with output_file.open("a", encoding="utf-8", newline="\n") as file:
                if needs_separator:
                    file.write("\n")
                for relative_path, file_hash in new_records:
                    file.write(f"{relative_path}\n{file_hash}\n\n")
    except Exception as exc:
        print(f"\nError: failed to append to the output file: {exc}")
        return

    print("\nCompleted.")
    print(f"Scanned:  {len(files)}")
    print(f"Appended: {len(new_records)}")
    print(f"Skipped:  {skipped_count}")
    print(f"Errors:   {error_count}")
    print(f"TXT saved to: {output_file}")


def load_manifest(manifest_file: Path) -> list[tuple[str, str]]:
    """Load and validate the simple two-line manifest format."""
    lines = [
        line
        for line in manifest_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if not lines:
        raise ValueError("the manifest is empty")
    if len(lines) % 2 != 0:
        raise ValueError("the manifest has an incomplete path/hash pair")

    records = []
    seen = set()
    for index in range(0, len(lines), 2):
        relative_path = lines[index]
        expected_hash = lines[index + 1].strip().lower()

        if len(expected_hash) != 64:
            raise ValueError(f"invalid SHA-256 value for: {relative_path}")
        try:
            int(expected_hash, 16)
        except ValueError as exc:
            raise ValueError(f"invalid SHA-256 value for: {relative_path}") from exc

        record = (relative_path, expected_hash)
        if record not in seen:
            seen.add(record)
            records.append(record)

    return records


def latest_records(records: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Keep the latest hash for each relative path while preserving final path order."""
    latest = {}
    for relative_path, expected_hash in records:
        latest[relative_path] = expected_hash
    return list(latest.items())


def resolve_manifest_path(directory: Path, relative_path: str) -> Path:
    """Resolve a manifest path and reject paths outside the evidence directory."""
    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError("absolute path is not allowed")

    resolved = (directory / path).resolve()
    try:
        resolved.relative_to(directory)
    except ValueError as exc:
        raise ValueError("path escapes the evidence directory") from exc

    return resolved


def verify_manifest(directory: Path) -> None:
    """Verify files against the existing SHA-256 manifest."""
    manifest_file = directory / OUTPUT_NAME

    if not manifest_file.is_file():
        print(f"\nError: {OUTPUT_NAME} was not found in the selected directory.")
        return

    try:
        records = latest_records(load_manifest(manifest_file))
    except Exception as exc:
        print(f"\nError: failed to read the manifest: {exc}")
        return

    print(f"\nLoaded {len(records)} record(s).")
    print("Verifying SHA-256 hashes...\n")

    ok_count = 0
    modified_count = 0
    missing_count = 0
    error_count = 0
    expected_paths = set()

    for index, (relative_path, expected_hash) in enumerate(records, start=1):
        print(f"[{index}/{len(records)}] {relative_path}", end=": ")

        try:
            file_path = resolve_manifest_path(directory, relative_path)
            expected_paths.add(file_path)
        except Exception as exc:
            error_count += 1
            print(f"ERROR ({exc})")
            continue

        if not file_path.exists() or not file_path.is_file():
            missing_count += 1
            print("MISSING")
            continue

        try:
            actual_hash = sha256_file(file_path)
        except Exception as exc:
            error_count += 1
            print(f"ERROR ({exc})")
            continue

        if hmac.compare_digest(actual_hash, expected_hash):
            ok_count += 1
            print("OK")
        else:
            modified_count += 1
            print("MODIFIED")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {actual_hash}")

    new_files = []
    try:
        for file_path in collect_files(directory):
            resolved = file_path.resolve()
            if resolved not in expected_paths:
                new_files.append(file_path.relative_to(directory).as_posix())
    except Exception as exc:
        error_count += 1
        print(f"\nERROR while checking for new files: {exc}")

    if new_files:
        print("\nNew files not present in the manifest:")
        for relative_path in new_files:
            print(f"NEW: {relative_path}")

    print("\nVerification summary")
    print("-" * 40)
    print(f"OK:       {ok_count}")
    print(f"MODIFIED: {modified_count}")
    print(f"MISSING:  {missing_count}")
    print(f"NEW:      {len(new_files)}")
    print(f"ERROR:    {error_count}")

    if modified_count == 0 and missing_count == 0 and not new_files and error_count == 0:
        print("\nResult: PASSED")
    else:
        print("\nResult: FAILED")


def main() -> None:
    print("Evidence File SHA-256 Hash Tool")
    print("Generate and verify file hashes")
    print()
    print("[1] Generate hash manifest")
    print("[2] Verify existing manifest")
    print()

    try:
        mode = input("Select mode [1/2]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return

    if mode not in {"1", "2"}:
        print("\nError: please select 1 or 2.")
        wait_for_exit()
        return

    directory = get_directory()
    if directory is None:
        wait_for_exit()
        return

    if mode == "1":
        generate_manifest(directory)
    else:
        verify_manifest(directory)

    wait_for_exit()


if __name__ == "__main__":
    main()
