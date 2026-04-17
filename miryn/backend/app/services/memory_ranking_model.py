"""
Memory Ranking Model - Divyadeep Kaur
Trains an XGBoost model to score memory relevance.
Input: 5 features per memory
Output: relevance score 0-1
"""
import json
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import pickle
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "training_data.jsonl")
MODEL_FILE = os.path.join(os.path.dirname(__file__), "memory_ranking_model.pkl")


def load_data(filepath: str):
    examples = []
    with open(filepath, "r") as f:
        for line in f:
            examples.append(json.loads(line.strip()))
    return examples


def extract_features(example: dict) -> list:
    """Extract feature vector from a single example."""
    recency_score = max(0.0, 1.0 - (example["days_ago"] / 180.0))
    return [
        recency_score,
        example["emotional_intensity"],
        example["entity_overlap"] / 5.0,
        float(example["identity_alignment"]),
    ]


def train():
    print("Loading data...")
    examples = load_data(DATA_FILE)
    print(f"Loaded {len(examples)} examples")

    X = np.array([extract_features(e) for e in examples])
    y = np.array([e["relevance_score"] for e in examples])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    print("\nTraining XGBoost model...")
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)

    print(f"\nModel Performance:")
    print(f"  RMSE : {rmse:.4f}")
    print(f"  MAE  : {mae:.4f}")

    print(f"\nFeature Importances:")
    features = ["recency", "emotional_intensity", "entity_overlap", "identity_alignment"]
    for name, score in zip(features, model.feature_importances_):
        print(f"  {name:25s}: {score:.4f}")

    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)
    print(f"\nModel saved to {MODEL_FILE}")


def rank_memories(current_message_features: dict, memories: list) -> list:
    """
    Rank a list of memories for a given message.
    Each memory must have: days_ago, emotional_intensity, entity_overlap, identity_alignment
    Returns memories sorted by relevance score descending.
    """
    with open(MODEL_FILE, "rb") as f:
        model = pickle.load(f)

    for memory in memories:
        features = np.array([extract_features(memory)]).reshape(1, -1)
        memory["relevance_score"] = round(float(model.predict(features)[0]), 4)

    return sorted(memories, key=lambda x: x["relevance_score"], reverse=True)


if __name__ == "__main__":
    train()