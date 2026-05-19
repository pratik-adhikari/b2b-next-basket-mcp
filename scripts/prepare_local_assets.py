from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
VENDOR_DIR = PROJECT_ROOT / "vendor"


def copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing source file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"copied: {src.name} -> {dst}")


def copy_dir(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing source directory: {src}")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"copied: {src.name}/ -> {dst}/")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage:\n"
            "  python scripts/prepare_local_assets.py '/path/to/extracted/Public Hackathon (NDA required)'"
        )

    source_dir = Path(sys.argv[1]).expanduser().resolve()
    if not source_dir.exists():
        raise FileNotFoundError(source_dir)

    DATA_DIR.mkdir(exist_ok=True)
    VENDOR_DIR.mkdir(exist_ok=True)

    copy_file(source_dir / "landing_page_model.onnx", DATA_DIR / "model.onnx")
    copy_file(source_dir / "multi_client_dataset.joblib", DATA_DIR / "dataset.joblib")
    copy_file(source_dir / "alit_backend.py", VENDOR_DIR / "protected_backend.py")
    copy_dir(source_dir / "pyarmor_runtime_000000", VENDOR_DIR / "protected_runtime")

    # The protected backend normally imports a package named pyarmor_runtime_000000.
    # Keep a compatibility copy with the original package name under vendor/.
    compat_runtime = VENDOR_DIR / "pyarmor_runtime_000000"
    if compat_runtime.exists():
        shutil.rmtree(compat_runtime)
    shutil.copytree(VENDOR_DIR / "protected_runtime", compat_runtime)
    print(f"created compatibility runtime: {compat_runtime}/")

    # On Linux, the root runtime may be a macOS binary in the provided package.
    # If linux_x86_64 exists, copy it to the expected root location.
    linux_runtime = compat_runtime / "linux_x86_64" / "pyarmor_runtime.so"
    root_runtime = compat_runtime / "pyarmor_runtime.so"
    if sys.platform.startswith("linux") and linux_runtime.exists():
        shutil.copy2(linux_runtime, root_runtime)
        print("patched Linux pyarmor runtime at root package location")

    print("\nLocal assets prepared. Do not commit data/ or vendor/ to GitHub.")


if __name__ == "__main__":
    main()
