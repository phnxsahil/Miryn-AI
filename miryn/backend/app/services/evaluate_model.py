"""
Evaluation Metrics - Divyadeep Kaur
Computes Precision@K, Recall@K and NDCG for the memory ranking model.
"""
import json
import numpy as np
import pickle
import os

MODEL_FILE = os.path.join(os.path.dirname(__file__), "memory_ranking_model.pkl")
DATA_FILE = os.path.join(os.path.dirname(__file__), "training_data.jsonl")

RELEVANCE_THRESHOLD = 0.5  # score >= 0.5 = relevant


def load_data():
    examples = []
    with open(DATA_FILE, "r") as f:
        for line in f:
            examples.append(json.loads(line.strip()))
    return examples


def extract_features(example: dict) -> list:
    recency_score = max(0.0, 1.0 - (example["days_ago"] / 180.0))
    return [
        recency_score,
        example["emotional_intensity"],
        example["entity_overlap"] / 5.0,
        float(example["identity_alignment"]),
    ]


def precision_at_k(predicted_scores, true_scores, k):
    """Of top K predicted, how many are truly relevant?"""
    top_k_indices = np.argsort(predicted_scores)[::-1][:k]
    relevant = sum(1 for i in top_k_indices if true_scores[i] >= RELEVANCE_THRESHOLD)
    return relevant / k


def recall_at_k(predicted_scores, true_scores, k):
    """Of all truly relevant, how many are in top K?"""
    top_k_indices = np.argsort(predicted_scores)[::-1][:k]
    total_relevant = sum(1 for s in true_scores if s >= RELEVANCE_THRESHOLD)
    if total_relevant == 0:
        return 0.0
    relevant_in_k = sum(1 for i in top_k_indices if true_scores[i] >= RELEVANCE_THRESHOLD)
    return relevant_in_k / total_relevant


def ndcg_at_k(predicted_scores, true_scores, k):
    """Normalized Discounted Cumulative Gain — rewards relevant items ranked higher."""
    top_k_indices = np.argsort(predicted_scores)[::-1][:k]
    dcg = sum(
        true_scores[i] / np.log2(rank + 2)
        for rank, i in enumerate(top_k_indices)
    )
    ideal_indices = np.argsort(true_scores)[::-1][:k]
    idcg = sum(
        true_scores[i] / np.log2(rank + 2)
        for rank, i in enumerate(ideal_indices)
    )
    return dcg / idcg if idcg > 0 else 0.0


def evaluate():
    print("Loading model and data...")
    with open(MODEL_FILE, "rb") as f:
        model = pickle.load(f)

    examples = load_data()

    # Group examples into batches of 10 (simulate ranking 10 memories per query)
    batch_size = 10
    batches = [examples[i:i+batch_size] for i in range(0, len(examples), batch_size)]

    p1_scores, p3_scores, p5_scores = [], [], []
    r1_scores, r3_scores, r5_scores = [], [], []
    ndcg3_scores, ndcg5_scores = [], []

    for batch in batches:
        if len(batch) < batch_size:
            continue

        X = np.array([extract_features(e) for e in batch])
        true_scores = np.array([e["relevance_score"] for e in batch])
        predicted_scores = model.predict(X)

        p1_scores.append(precision_at_k(predicted_scores, true_scores, 1))
        p3_scores.append(precision_at_k(predicted_scores, true_scores, 3))
        p5_scores.append(precision_at_k(predicted_scores, true_scores, 5))

        r1_scores.append(recall_at_k(predicted_scores, true_scores, 1))
        r3_scores.append(recall_at_k(predicted_scores, true_scores, 3))
        r5_scores.append(recall_at_k(predicted_scores, true_scores, 5))

        ndcg3_scores.append(ndcg_at_k(predicted_scores, true_scores, 3))
        ndcg5_scores.append(ndcg_at_k(predicted_scores, true_scores, 5))

    print("\n" + "="*45)
    print("   MEMORY RANKING MODEL — EVALUATION RESULTS")
    print("="*45)
    print(f"\n  Precision@1  : {np.mean(p1_scores):.4f}")
    print(f"  Precision@3  : {np.mean(p3_scores):.4f}")
    print(f"  Precision@5  : {np.mean(p5_scores):.4f}")
    print(f"\n  Recall@1     : {np.mean(r1_scores):.4f}")
    print(f"  Recall@3     : {np.mean(r3_scores):.4f}")
    print(f"  Recall@5     : {np.mean(r5_scores):.4f}")
    print(f"\n  NDCG@3       : {np.mean(ndcg3_scores):.4f}")
    print(f"  NDCG@5       : {np.mean(ndcg5_scores):.4f}")
    print("\n" + "="*45)


if __name__ == "__main__":
    evaluate()