import sys
from pathlib import Path

import joblib
from sentence_transformers import SentenceTransformer

MODEL_PATH = Path(__file__).parent / "model.pkl"
EMBEDDER_NAME = "all-MiniLM-L6-v2"

_clf = joblib.load(MODEL_PATH)
_embedder = SentenceTransformer(EMBEDDER_NAME)


def classify(prompt: str):
    embedding = _embedder.encode([prompt])
    label = _clf.predict(embedding)[0]
    probs = _clf.predict_proba(embedding)[0]
    scores = dict(zip(_clf.classes_, probs))
    return label, scores


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]) or "Explain how a hash map works."
    label, scores = classify(prompt)
    print(f"Prompt: {prompt}")
    print(f"Predicted difficulty: {label}")
    print(f"Scores: {scores}")