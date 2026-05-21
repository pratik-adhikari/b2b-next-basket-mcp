from __future__ import annotations

import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import joblib
import onnxruntime as ort

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from b2b_next_basket_mcp.backend.predictor import OrderPredictor  # noqa: E402
from b2b_next_basket_mcp.config import DEFAULT_DEMO_CLIENT_ID  # noqa: E402


MAX_KEYS = 30
TOKEN_WINDOW = 50


def type_name(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__name__}"


def file_summary(path: Path) -> str:
    if not path.exists():
        return f"missing: {path}"
    size_mb = path.stat().st_size / (1024 * 1024)
    return f"{path} ({size_mb:.2f} MiB)"


def safe_value_summary(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool | int | float):
        return type(value).__name__
    if isinstance(value, str):
        return f"str(len={len(value)}, tokens={len(value.split())})"
    if isinstance(value, bytes):
        return f"bytes(len={len(value)})"
    if hasattr(value, "shape"):
        dtype = getattr(value, "dtype", None)
        return f"{type_name(value)}(shape={tuple(value.shape)}, dtype={dtype})"
    if isinstance(value, Mapping):
        return f"{type_name(value)}(len={len(value)})"
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return f"{type_name(value)}(len={len(value)})"
    attrs = public_attrs(value)
    if attrs:
        return f"{type_name(value)}(attrs={len(attrs)})"
    return type_name(value)


def public_attrs(value: Any) -> list[str]:
    try:
        names = vars(value).keys()
    except TypeError:
        return []
    return sorted(name for name in names if not name.startswith("_"))


def mapping_summary(value: Mapping[Any, Any], indent: str = "  ") -> list[str]:
    lines = [f"{indent}- keys ({min(len(value), MAX_KEYS)}/{len(value)} shown):"]
    for key in list(value.keys())[:MAX_KEYS]:
        lines.append(f"{indent}  - {key!r}: {safe_value_summary(value[key])}")
    if len(value) > MAX_KEYS:
        lines.append(f"{indent}  - ...")
    return lines


def object_summary(value: Any, indent: str = "  ") -> list[str]:
    attrs = public_attrs(value)
    if not attrs:
        return [f"{indent}- public attrs: none"]

    lines = [f"{indent}- public attrs ({min(len(attrs), MAX_KEYS)}/{len(attrs)} shown):"]
    for name in attrs[:MAX_KEYS]:
        try:
            attr_value = getattr(value, name)
        except Exception as exc:  # pragma: no cover - defensive diagnostics
            lines.append(f"{indent}  - {name}: unavailable ({type(exc).__name__})")
        else:
            lines.append(f"{indent}  - {name}: {safe_value_summary(attr_value)}")
    if len(attrs) > MAX_KEYS:
        lines.append(f"{indent}  - ...")
    return lines


def dataset_summary(dataset_path: Path) -> list[str]:
    lines = ["Dataset asset", f"  path: {file_summary(dataset_path)}"]
    if not dataset_path.exists():
        return lines

    raw = joblib.load(dataset_path)
    lines.append(f"  top-level type: {type_name(raw)}")
    lines.append(f"  top-level summary: {safe_value_summary(raw)}")

    if isinstance(raw, Mapping):
        lines.extend(mapping_summary(raw))
    elif isinstance(raw, Sequence) and not isinstance(raw, str | bytes | bytearray):
        lines.append(f"  sequence length: {len(raw)}")
        if raw:
            first = raw[0]
            lines.append(f"  first item type: {type_name(first)}")
            lines.append(f"  first item summary: {safe_value_summary(first)}")
            if isinstance(first, Mapping):
                lines.extend(mapping_summary(first))
            else:
                lines.extend(object_summary(first))
    else:
        lines.extend(object_summary(raw))

    return lines


def count_estimated_order_events(tokens: list[str]) -> int:
    time_token_count = sum(1 for token in tokens if token.startswith("<dt_"))
    eos_count = tokens.count("<eos>")
    return max(time_token_count, eos_count)


def client_and_history_summary(predictor: OrderPredictor) -> list[str]:
    clients = predictor.list_clients()
    lines = [
        "Clients",
        f"  total: {len(clients)}",
        "  first 30 client IDs:",
    ]
    for client_id in clients[:30]:
        lines.append(f"    - {client_id}")
    if len(clients) > 30:
        lines.append("    - ...")

    if not clients:
        lines.extend(["", "Demo history", "  unavailable: no clients loaded"])
        return lines

    demo_client_id = DEFAULT_DEMO_CLIENT_ID if DEFAULT_DEMO_CLIENT_ID in clients else clients[0]
    history = predictor.get_sample_history(demo_client_id)
    tokens = history.split()
    first_tokens = tokens[:TOKEN_WINDOW]
    last_tokens = tokens[-TOKEN_WINDOW:] if len(tokens) > TOKEN_WINDOW else []

    lines.extend(
        [
            "",
            "Demo history",
            f"  client_id: {demo_client_id}",
            f"  token count: {len(tokens)}",
            f"  estimated order events: {count_estimated_order_events(tokens)}",
            f"  first {len(first_tokens)} tokens: {' '.join(first_tokens)}",
        ]
    )
    if last_tokens:
        lines.append(f"  last {len(last_tokens)} tokens: {' '.join(last_tokens)}")
    else:
        lines.append("  last tokens: same as first window")
    return lines


def shape_summary(meta: Any) -> str:
    shape = getattr(meta, "shape", None)
    shape_text = "unknown" if shape is None else list(shape)
    return f"name={meta.name!r}, type={meta.type!r}, shape={shape_text}"


def onnxruntime_summary(model_path: Path) -> list[str]:
    lines = ["ONNX Runtime asset", f"  path: {file_summary(model_path)}"]
    if not model_path.exists():
        return lines

    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    lines.append("  inputs:")
    for input_meta in session.get_inputs():
        lines.append(f"    - {shape_summary(input_meta)}")
    lines.append("  outputs:")
    for output_meta in session.get_outputs():
        lines.append(f"    - {shape_summary(output_meta)}")
    return lines


def onnx_operator_counts(model_path: Path) -> list[str]:
    lines = ["ONNX operator counts"]
    if not model_path.exists():
        lines.append("  unavailable: model missing")
        return lines

    try:
        import onnx  # type: ignore
    except ModuleNotFoundError:
        lines.append("  unavailable: onnx package is not installed")
        return lines

    model = onnx.load(str(model_path))
    counts = Counter(node.op_type for node in model.graph.node)
    if not counts:
        lines.append("  no operators found")
        return lines
    for op_type, count in counts.most_common():
        lines.append(f"  - {op_type}: {count}")
    return lines


def main() -> None:
    dataset_path = DATA_DIR / "dataset.joblib"
    model_path = DATA_DIR / "model.onnx"

    sections: list[list[str]] = [dataset_summary(dataset_path)]

    predictor = OrderPredictor(dataset_path=dataset_path, model_path=model_path)
    sections.append(client_and_history_summary(predictor))
    sections.append(onnxruntime_summary(model_path))
    sections.append(onnx_operator_counts(model_path))

    for index, section in enumerate(sections):
        if index:
            print()
        print("\n".join(section))


if __name__ == "__main__":
    main()
