# Chapter 8: Security, Privacy, and Ethical Considerations

## 8.1 The Privacy Imperative in Identity-First AI
As Miryn AI transitions from a stateless utility to an Identity-First companion, the volume and intimacy of the data it collects grow exponentially. Traditional stateless LLMs process user inputs ephemerally; once the context window is cleared, the data is theoretically discarded by the application layer (barring provider-level data retention policies). Miryn, however, intentionally records, analyzes, and persists the user's deep psychological traits, emotional vulnerabilities, and core beliefs. 

This introduces a severe privacy imperative. If the `identities` or `messages` tables were compromised, a malicious actor would gain access to a highly structured psychological profile of the user. Consequently, the architecture incorporates multiple layers of cryptographic and logical isolation.

## 8.2 Cryptographic Implementation: Encryption at Rest
To mitigate the risk of database exfiltration, Miryn AI employs **Advanced Encryption Standard (AES-256-GCM)** for all sensitive episodic memory and identity records.

### 8.2.1 Application-Layer Encryption
Rather than relying solely on disk-level encryption provided by cloud providers (which protects against physical drive theft but not against database access via compromised credentials), Miryn implements application-layer encryption. 
- The `content_encrypted` column in the `messages` table stores the ciphertext. 
- The master `ENCRYPTION_KEY` is injected as a 32-byte Base64 environment variable directly into the FastAPI application memory.
- When the Hybrid Retrieval system fetches relevant messages via `pgvector` similarity search, the backend dynamically decrypts the payload *in memory* before assembling the prompt context for the LLM. 

```python
# Conceptual representation of the dynamic decryption pipeline
def fetch_and_decrypt_messages(conversation_id: str):
    rows = db.execute("SELECT content_encrypted FROM messages WHERE conversation_id = %s", [conversation_id])
    decrypted_history = [aes_gcm_decrypt(row['content_encrypted'], ENCRYPTION_KEY) for row in rows]
    return decrypted_history
```

This ensures that even if a bad actor obtains a full SQL dump of the PostgreSQL database, the conversational history remains entirely opaque.

## 8.3 Authentication and Logical Isolation
Access control is governed by a rigorous JSON Web Token (JWT) architecture.
- **HS256 Signatures**: Tokens are signed using an HMAC SHA-256 algorithm.
- **Short-Lived Expiration**: Access tokens are hard-coded to expire after 7 days, enforcing periodic re-authentication.
- **Tenant Isolation**: Every API endpoint fetching memory or identity data strictly validates the `user_id` extracted from the JWT against the `user_id` of the requested resource. The database queries inherently enforce multi-tenant isolation (e.g., `WHERE user_id = :user_id`).

Furthermore, to prevent brute-force attacks against user accounts, a Redis-backed rate-limiting guard is implemented. If more than 5 failed login attempts occur within a 15-minute window for a specific email or IP address, the system triggers an HTTP 429 (Too Many Requests) block.

## 8.4 Ethical Considerations in Psychometric Profiling
Beyond standard data security, building an AI that actively profiles users raises complex ethical questions regarding emotional manipulation and algorithmic bias.

1. **Transparency**: The Identity Dashboard was specifically engineered to address the "black box" problem. By allowing the user to visually inspect their `openness` score or read the exact `core_beliefs` the AI has inferred, Miryn ensures cognitive transparency. The user is always aware of the lens through which the AI views them.
2. **Conflict Resolution Agency**: When the Reflection Engine detects a contradiction between a new statement and an old belief, it does not silently override the data. Instead, it pushes an `identity.conflict` SSE event to the client, asking the user to manually resolve the discrepancy. This guarantees that the human remains the ultimate arbiter of their digital identity.
3. **Data Portability and Deletion**: Following GDPR and CCPA principles, the backend features hard-delete cascades. When a user deletes their account, the `ON DELETE CASCADE` constraint on the PostgreSQL `users` table guarantees the total annihilation of all associated identities, beliefs, and encrypted messages.
