# Chapter 9: Use Cases and Application Scenarios

## 9.1 Mental Health Companion
The primary intended use case for Miryn-AI is as a mental health and emotional wellness companion. The system's persistent memory, emotion detection, and identity tracking capabilities are directly aligned with the needs of users seeking continuous emotional support.

In this use case, a user interacts with the AI companion over several weeks or months. The system tracks the user's emotional trajectory, detects patterns such as persistent sadness or increasing anxiety volatility, and proactively incorporates relevant past context.

## 9.2 The Comparative Interaction (User A vs User B)

To demonstrate the "Identity-First" capability in action, we present a comparative interaction between the system and two distinct users. This comparison highlights how Miryn-AI adapts its response style and updates its internal psychological model based on differing inputs.

### 9.2.1 Interaction 1: User A (Creative / "Riya")
User A focuses on creative pursuits, emotional exploration, and abstract concepts.

*(Please insert the actual chat screenshot below)*
> ![Screenshot: Chat interface showing User A (Riya) discussing creative concepts](file:///d:/Projects/MirynAI-Production/Miryn-AI/reports/thesis/images/chat_user_a.png)

When User A engages the system, the Identity Engine immediately begins mapping traits such as *empathetic* and *artistic*. Over multiple sessions, the system tracks the semantic drift (as shown in Chapter 6) and adjusts its generative LLM prompts to mirror User A's associative flexibility.

### 9.2.2 Interaction 2: User B (Technical / Analytical)
User B engages the system primarily for technical problem-solving, optimization, and logical deductions.

*(Please insert the actual chat screenshot below)*
> ![Screenshot: Chat interface showing User B discussing technical implementations](file:///d:/Projects/MirynAI-Production/Miryn-AI/reports/thesis/images/chat_user_b.png)

In response to User B, the system restricts associative jumps and focuses on precise, factual responses. The Identity Dashboard reflects traits such as *logical* and *optimization-oriented*.

*(Please insert the Identity Dashboard screenshot below)*
> ![Screenshot: Frontend Identity Dashboard showing User B's traits and active beliefs](file:///d:/Projects/MirynAI-Production/Miryn-AI/reports/thesis/images/dashboard_identity.png)

## 9.3 Long-Term Relationship and Life Journal
Users can use Miryn-AI as a long-term life journal: a record of their experiences, relationships, emotions, and growth. The identity version timeline provides a quantitative narrative of how the user has changed over months or years.

---

# Chapter 10: Testing and Results

## 10.1 API Testing via Swagger
All API endpoints are tested using the interactive Swagger UI documentation served at `http://localhost:8000/docs`. The Swagger interface allows end-to-end testing of each endpoint with authentication, request body construction, and response inspection. All 10 implemented endpoints have been verified to return correct responses with valid JWT authentication.

## 10.2 Memory Ranking Endpoint Test
The `POST /memory/ranked` endpoint was tested with a set of three memories of varying relevance. The system correctly ranked the memories:

| Rank | Memory | Predicted Score |
| :--- | :--- | :--- |
| **1st** | User mentioned interviewing at Google last week | 0.5378 |
| **2nd** | User felt stressed before their exam | 0.2991 |
| **3rd** | User loves Italian food | 0.1906 |
*Table 10.1: Memory Ranking Endpoint Test Results*

The ranking correctly identifies the Google interview memory as most relevant (high recency + high emotional intensity + identity alignment = 1) and Italian food preference as least relevant.

## 10.3 DS Service Inference Test
The DS service was tested by submitting messages with clearly defined emotional content. The emotion detection model correctly classified:
- *'I am so excited about my promotion!'* $\rightarrow$ **joy** (0.94)
- *'I can't stop crying, everything feels hopeless.'* $\rightarrow$ **sadness** (0.91)
- *'The project deadline is in 2 hours and nothing works.'* $\rightarrow$ **fear** (0.78), **anger** (0.15)

---

# Chapter 11: Conclusion and Future Work

## 11.1 Summary of Contributions
This capstone project successfully designed and implemented a production-grade backend for an AI companion with persistent memory, real-time emotion and entity extraction, identity tracking, and ML-powered memory ranking. The key contributions of this work are:
1. A complete FastAPI backend with 10 REST API endpoints, JWT authentication, rate limiting, and Swagger documentation.
2. A Data Science service layer that runs emotion detection (7-class DistilRoBERTa), NER (spaCy), and sentence embedding (`all-MiniLM-L6-v2`) inference concurrently with LLM calls.
3. An emotion and identity analytics system computing mood score, volatility, stability score, and semantic drift.
4. An XGBoost memory ranking model achieving RMSE 0.054, NDCG@5 0.99, and Recall@5 0.72.
5. Implementation of a robust SQLite Thread-Locking mechanism to simulate the production Identity Engine locally.

## 11.2 Limitations
- The memory ranking model is trained on synthetic data. Performance on real user data may differ.
- The DS service loads models into memory at startup, which requires approximately 2GB of RAM.
- The emotion detection model was trained on English text and may underperform on code-switched or non-English input.

## 11.3 Future Work
- Re-train the memory ranking model on real user interaction data as the system accumulates users.
- Implement a learned identity shift detector that uses the DS service's NER and embedding outputs to automatically trigger identity version creation when semantic drift exceeds a learned threshold.
- Add multi-modal memory support: allow users to store images, voice notes, and documents as memories.

---

# References
[1] Packer, C., Wooders, S., Lin, K., Fang, V., Patil, S. G., Stoica, I., & Gonzalez, J. E. (2023). MemGPT: Towards LLMs as Operating Systems. *arXiv preprint arXiv:2310.08560*.
[2] Hartmann, J. (2022). emotion-english-distilroberta-base. *Hugging Face*.
[3] Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP*.
[4] Honnibal, M., & Montani, I. (2017). spaCy 2: Natural language understanding with Bloom embeddings.
[5] Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *KDD*.
[6] Demszky, D. et al. (2020). GoEmotions: A Dataset of Fine-Grained Emotions. *ACL*.
[7] Johnson, J., Douze, M., & Jégou, H. (2019). Billion-scale similarity search with GPUs. *IEEE*.

---

# Appendix A: Sample Training Data
The following is a sample of the synthetic training data generated for XGBoost:
```json
{"current_message": "Struggling with the project deadline at work", "memory": "User mentioned interviewing at Google last week", "days_ago": 9, "emotional_intensity": 0.76, "entity_overlap": 2, "identity_alignment": 1, "relevance_score": 0.54}
{"current_message": "I'm feeling anxious about my job interview tomorrow", "memory": "User has anxiety and sees a therapist", "days_ago": 45, "emotional_intensity": 0.88, "entity_overlap": 0, "identity_alignment": 1, "relevance_score": 0.71}
```

# Appendix B: Evaluation Script Output
Complete output of `app/services/evaluate_model.py`:
```text
Loading model and data...
=============================================
  MEMORY RANKING MODEL — EVALUATION RESULTS
=============================================
 Precision@1  : 0.6200
 Precision@3  : 0.3600
 Precision@5  : 0.2400
 Recall@1     : 0.4333
 Recall@3     : 0.6783
 Recall@5     : 0.7200
 NDCG@3       : 0.9800
 NDCG@5       : 0.9855
=============================================
```
