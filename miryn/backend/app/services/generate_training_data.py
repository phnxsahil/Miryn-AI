"""
Training Data Generator - Divyadeep Kaur
Generates synthetic training data for memory ranking model.
No API needed - uses hardcoded realistic examples.
"""
import json
import random

OUTPUT_FILE = "training_data.jsonl"
random.seed(42)

# Template messages and memories
MESSAGES = [
    "I'm feeling anxious about my job interview tomorrow",
    "Had a great workout today, feeling energized",
    "My sister called, she's getting married next month",
    "Struggling with the project deadline at work",
    "Feeling lonely today, miss my friends",
    "Started learning guitar, it's going well",
    "Doctor said I need to reduce stress",
    "Had a fight with my manager today",
    "Planning a trip to Paris next summer",
    "Can't sleep, overthinking everything",
    "Mom's birthday is coming up next week",
    "Got promoted today, feeling great",
    "Broke up with my partner last night",
    "Trying to eat healthier, started meal prep",
    "Feeling burned out from work",
    "My dog is sick, going to the vet",
    "Finally finished my thesis draft",
    "Feeling grateful for my friends today",
    "Had a panic attack this morning",
    "Starting a new job next Monday",
]

MEMORIES = [
    ("User mentioned interviewing at Google last week", 7, 0.8, 3, 1),
    ("User loves hiking on weekends", 30, 0.3, 0, 0),
    ("User felt stressed before their exam in March", 60, 0.7, 1, 0),
    ("User's sister is named Priya", 15, 0.4, 2, 1),
    ("User goes to gym every morning", 5, 0.5, 1, 1),
    ("User is working on a machine learning project", 10, 0.6, 2, 1),
    ("User mentioned feeling overwhelmed at work", 3, 0.9, 1, 0),
    ("User likes Italian food", 45, 0.2, 0, 0),
    ("User's therapist recommended meditation", 20, 0.7, 0, 1),
    ("User had argument with manager about deadlines", 8, 0.8, 2, 0),
    ("User wants to visit Japan someday", 90, 0.3, 1, 0),
    ("User mentioned loneliness during lockdown", 180, 0.8, 0, 0),
    ("User started guitar lessons last month", 30, 0.5, 2, 1),
    ("User's mom has diabetes", 60, 0.6, 1, 1),
    ("User got promoted to senior engineer", 14, 0.9, 1, 1),
    ("User broke up with partner 6 months ago", 180, 0.9, 1, 0),
    ("User is meal prepping every Sunday", 7, 0.4, 1, 1),
    ("User complained about burnout last week", 7, 0.8, 1, 0),
    ("User's dog is named Max", 30, 0.5, 2, 1),
    ("User submitted thesis last semester", 120, 0.7, 2, 1),
    ("User has anxiety and sees a therapist", 45, 0.9, 0, 1),
    ("User is moving to a new city next month", 10, 0.6, 0, 1),
    ("User loves reading science fiction", 60, 0.2, 0, 0),
    ("User mentioned panic attacks in stressful times", 30, 0.9, 0, 1),
    ("User is learning Spanish online", 20, 0.3, 0, 0),
]


def compute_relevance(message: str, memory_text: str, days_ago: int,
                      emotional_intensity: float, entity_overlap: int,
                      identity_alignment: int) -> float:
    """Compute a realistic relevance score based on features."""
    # Simple keyword overlap score
    msg_words = set(message.lower().split())
    mem_words = set(memory_text.lower().split())
    overlap = len(msg_words & mem_words)
    text_score = min(overlap / 5.0, 1.0)

    # Recency score (decay)
    recency_score = max(0.0, 1.0 - (days_ago / 180.0))

    # Combined score
    score = (
        0.35 * text_score +
        0.20 * recency_score +
        0.20 * emotional_intensity +
        0.15 * min(entity_overlap / 5.0, 1.0) +
        0.10 * identity_alignment
    )

    # Add small noise
    score += random.uniform(-0.05, 0.05)
    return round(max(0.0, min(1.0, score)), 2)


def generate_examples(n: int = 500):
    examples = []
    for _ in range(n):
        message = random.choice(MESSAGES)
        memory_text, days_ago, emotional_intensity, entity_overlap, identity_alignment = random.choice(MEMORIES)

        # Vary the features slightly
        days_ago = max(1, days_ago + random.randint(-3, 3))
        emotional_intensity = round(max(0.0, min(1.0, emotional_intensity + random.uniform(-0.1, 0.1))), 2)
        entity_overlap = max(0, min(5, entity_overlap + random.randint(-1, 1)))

        relevance_score = compute_relevance(
            message, memory_text, days_ago,
            emotional_intensity, entity_overlap, identity_alignment
        )

        examples.append({
            "current_message": message,
            "memory": memory_text,
            "days_ago": days_ago,
            "emotional_intensity": emotional_intensity,
            "entity_overlap": entity_overlap,
            "identity_alignment": identity_alignment,
            "relevance_score": relevance_score,
        })

    return examples


if __name__ == "__main__":
    print("Generating 500 training examples...")
    examples = generate_examples(500)

    with open(OUTPUT_FILE, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    print(f"Done! Saved {len(examples)} examples to {OUTPUT_FILE}")
    print(f"Sample: {examples[0]}")