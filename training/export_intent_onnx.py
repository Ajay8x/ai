"""Export AJAX AI's trained intent checkpoint to an ONNX inference model.

The exported graph keeps the existing bag-of-words input contract. The
runtime vocabulary and intent labels remain in models/vocab_metadata.json.
"""

import argparse
import json
import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
MODELS_DIR = BASE_DIR / "models"
PT_PATH = MODELS_DIR / "ajax_neural_intent.pt"
META_PATH = MODELS_DIR / "vocab_metadata.json"
DEFAULT_ONNX_PATH = MODELS_DIR / "ajax_neural_intent.onnx"


def export(output_path: Path) -> Path:
    try:
        import torch
        import onnx
    except ImportError as exc:
        raise RuntimeError(
            "ONNX export needs torch and onnx. Install requirements-optional.txt first."
        ) from exc

    from ai.neural.intent_classifier import NeuralIntentNet

    if not PT_PATH.exists() or not META_PATH.exists():
        raise FileNotFoundError("The PyTorch checkpoint and vocabulary metadata are required.")

    with META_PATH.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    vocab_size = int(metadata["vocab_size"])
    num_classes = int(metadata["num_classes"])
    model = NeuralIntentNet(vocab_size=vocab_size, hidden_dim=128, num_classes=num_classes)
    state_dict = torch.load(PT_PATH, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sample = torch.zeros((1, vocab_size), dtype=torch.float32)
    torch.onnx.export(
        model,
        sample,
        str(output_path),
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
        do_constant_folding=True,
        dynamo=False,
    )

    onnx_model = onnx.load(str(output_path))
    onnx.checker.check_model(onnx_model)
    print(f"Exported ONNX intent model: {output_path}")
    print(f"Input shape: [batch, {vocab_size}] | Output classes: {num_classes}")
    print(f"Size: {output_path.stat().st_size / 1024:.2f} KB")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export AJAX AI intent model to ONNX")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_ONNX_PATH),
        help="Output .onnx path (default: models/ajax_neural_intent.onnx)",
    )
    args = parser.parse_args()
    export(Path(args.output).expanduser().resolve())


if __name__ == "__main__":
    main()
