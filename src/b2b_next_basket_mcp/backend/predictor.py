from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import onnxruntime as ort

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
VENDOR_DIR = PROJECT_ROOT / "vendor"

# The proprietary backend is intentionally kept under vendor/ and ignored by Git.
sys.path.insert(0, str(VENDOR_DIR))

try:
    from protected_backend import SimulationDataset  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - user setup error
    raise ModuleNotFoundError(
        "Could not import vendor/protected_backend.py. Run:\n"
        "  python scripts/prepare_local_assets.py '/path/to/extracted/Public Hackathon (NDA required)'\n"
        "or manually place protected_backend.py under vendor/."
    ) from exc

VECTOR_SIZE = 128
MAX_CATALOG_SIZE = 256
MAX_SEQ_LEN = 512
CURRENT_SEQ_LEN = MAX_SEQ_LEN - 1


def simple_tokenize(text: str) -> list[str]:
    return text.split()


class OrderPredictor:
    """
    Clean adapter around the provided dataset and ONNX model.

    First-principles role:
    - Hide backend/model loading details.
    - Expose simple Python functions to the MCP layer.
    """

    def __init__(
        self,
        dataset_path: Path | None = None,
        model_path: Path | None = None,
        seed: int = 42,
    ) -> None:
        self.dataset_path = dataset_path or DATA_DIR / "dataset.joblib"
        self.model_path = model_path or DATA_DIR / "model.onnx"
        self.seed = seed

        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {self.dataset_path}. "
                "Run scripts/prepare_local_assets.py first."
            )
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {self.model_path}. "
                "Run scripts/prepare_local_assets.py first."
            )

        self.datasets = self._load_multi_client_dataset(self.dataset_path)
        self.dataset_map = {ds.client_name: ds for ds in self.datasets}

        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=["CPUExecutionProvider"],
        )

    def _load_multi_client_dataset(self, file_path: Path) -> list[SimulationDataset]:
        raw_data_list = joblib.load(file_path)
        return [SimulationDataset(preloaded_data=item) for item in raw_data_list]

    def list_clients(self) -> list[str]:
        return sorted(self.dataset_map.keys())

    def get_sample_history(self, client_id: str) -> str:
        dataset = self._get_dataset(client_id)
        rng = random.Random(self.seed)
        return rng.choice(dataset.sentences)

    def predict_next_basket(
        self,
        client_id: str,
        start_text: str,
        max_generate: int = 30,
        temperature: float = 1.0,
        top_k: int = 20,
        sensor_size: int = 128,
    ) -> dict[str, Any]:
        if not start_text.strip():
            raise ValueError("start_text cannot be empty.")
        if max_generate < 1 or max_generate > 100:
            raise ValueError("max_generate must be between 1 and 100.")
        if top_k < 1 or top_k > 100:
            raise ValueError("top_k must be between 1 and 100.")
        if temperature <= 0:
            raise ValueError("temperature must be positive.")

        dataset = self._get_dataset(client_id)

        generated_text = smart_inference_onnx(
            onnx_session=self.session,
            dataset=dataset,
            start_text=start_text,
            max_generate=max_generate,
            temperature=temperature,
            top_k=top_k,
            sensor_size=sensor_size,
            seed=self.seed,
        )

        tokens = generated_text.split()
        return {
            "client_id": client_id,
            "input_history": start_text,
            "predicted_text": generated_text,
            "predicted_tokens": tokens,
            "generation_parameters": {
                "max_generate": max_generate,
                "temperature": temperature,
                "top_k": top_k,
                "sensor_size": sensor_size,
                "seed": self.seed,
            },
        }

    def _get_dataset(self, client_id: str) -> SimulationDataset:
        if client_id not in self.dataset_map:
            examples = ", ".join(self.list_clients()[:10])
            raise ValueError(
                f"Unknown client_id '{client_id}'. Example available clients: {examples}"
            )
        return self.dataset_map[client_id]


def smart_inference_onnx(
    onnx_session: ort.InferenceSession,
    dataset: SimulationDataset,
    start_text: str,
    max_generate: int = 40,
    temperature: float = 1.0,
    top_k: int = 5,
    sensor_size: int = 128,
    seed: int = 42,
) -> str:
    """
    Next-basket generation logic adapted from the provided hackathon notebook.

    It treats customer order history as a token sequence. The first generated token
    is a timing token. Later tokens are product tokens selected from the aligned
    client catalog.
    """
    rng = np.random.RandomState(seed)

    word_to_int = dataset.word_to_int
    vocab = dataset.vocab
    raw_vectors = dataset.all_vectors
    time_tokens = dataset.master_w2v.time_order
    vector_size = raw_vectors.shape[1]

    # 1. Prepare a client/catalog sensor input.
    valid_indices = [i for i, word in enumerate(vocab) if word in word_to_int]
    if not valid_indices:
        raise ValueError("Dataset vocabulary contains no valid indices.")

    replace_flag = len(valid_indices) < sensor_size
    sensor_indices = rng.choice(valid_indices, size=sensor_size, replace=replace_flag)

    sensor_input = np.zeros((1, sensor_size, vector_size), dtype=np.float32)
    for k, idx in enumerate(sensor_indices):
        sensor_input[0, k] = raw_vectors[idx]

    # 2. Prepare and align product candidates.
    product_mask = np.array(
        [not (word.startswith("<dt_") or word == "<unk>") or word == "<eos>" for word in vocab]
    )
    product_indices = np.where(product_mask)[0]
    raw_candidates = raw_vectors[product_indices]

    dummy_seq = np.zeros((1, CURRENT_SEQ_LEN, vector_size), dtype=np.float32)
    dummy_cat = np.zeros((1, MAX_CATALOG_SIZE, vector_size), dtype=np.float32)

    outputs = onnx_session.run(
        None,
        {
            "sentence_input": dummy_seq,
            "catalog_input": dummy_cat,
            "sensor_input": sensor_input,
        },
    )
    transform = outputs[3][0]
    aligned_candidates = np.dot(raw_candidates, transform)

    tokens = simple_tokenize(start_text)
    generated: list[str] = []
    generated_product_indices: set[int] = set()

    # 3. Generate one token at a time.
    for i in range(max_generate):
        s_input = np.zeros((1, CURRENT_SEQ_LEN, vector_size), dtype=np.float32)
        recent = tokens[-CURRENT_SEQ_LEN:]
        for j, tok in enumerate(recent):
            if tok in word_to_int:
                s_input[0, j] = raw_vectors[word_to_int[tok]]

        loop_outputs = onnx_session.run(
            None,
            {
                "sentence_input": s_input,
                "catalog_input": dummy_cat,
                "sensor_input": sensor_input,
            },
        )
        time_probs_seq = loop_outputs[1]
        query_seq = loop_outputs[2]

        last_idx = len(recent) - 1
        time_probs = time_probs_seq[0, last_idx, :]

        # Step 1: force the first generated token to be a time token.
        if i == 0:
            specific_time_dist = time_probs[1:]
            best_time_idx = np.argmax(specific_time_dist)
            first_time_token = time_tokens[best_time_idx]

            tokens.append(first_time_token)
            generated.append(first_time_token)
            continue

        # Step 2: generate product tokens using query/product-vector similarity.
        target_query = query_seq[0, last_idx, :]
        product_logits = np.dot(aligned_candidates, target_query)

        # Hard uniqueness constraint: prevent duplicate product tokens in one generated basket.
        for generated_idx in generated_product_indices:
            local_locs = np.where(product_indices == generated_idx)[0]
            if len(local_locs) > 0:
                product_logits[local_locs[0]] = -1e10

        product_logits /= max(temperature, 1e-6)
        exp_logits = np.exp(product_logits - np.max(product_logits))
        probs = exp_logits / np.sum(exp_logits)

        effective_top_k = min(top_k, len(probs))
        top_k_idx = np.argsort(probs)[-effective_top_k:]
        top_probs = probs[top_k_idx] / np.sum(probs[top_k_idx])
        selected_local_idx = rng.choice(top_k_idx, p=top_probs)

        global_idx = product_indices[selected_local_idx]
        next_word = vocab[global_idx]

        # Step 3: stop if end-of-sequence is predicted.
        if next_word == "<eos>":
            specific_time_dist = time_probs[1:]
            best_time_idx = np.argmax(specific_time_dist)
            final_time_token = time_tokens[best_time_idx]
            generated.append(final_time_token)
            break

        tokens.append(next_word)
        generated.append(next_word)
        generated_product_indices.add(int(global_idx))

    # Remove trailing time token if generation ended by predicting timing after basket.
    if generated and generated[-1].startswith("<dt_"):
        generated.pop()

    return " ".join(generated)
