# Local proprietary assets

This project is GitHub-safe only if you do not commit proprietary files.

Expected local files after running `scripts/prepare_local_assets.py`:

```text
data/model.onnx
data/dataset.joblib
vendor/protected_backend.py
vendor/protected_runtime/
vendor/pyarmor_runtime_000000/
```

The compatibility runtime folder keeps the original PyArmor package name because the protected backend may import that exact package internally.

## Prepare command

```bash
python scripts/prepare_local_assets.py "/path/to/extracted/Public Hackathon (NDA required)"
```

Copies and renames the local assets into neutral names.
