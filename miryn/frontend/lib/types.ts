export type Message = {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
};

export type Conversation = {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type EmotionInsight = {
  primary_emotion?: string;
  intensity?: number;
  secondary_emotions?: string[];
};

export type ConversationInsights = {
  entities?: string[];
  emotions?: EmotionInsight;
  topics?: string[];
  patterns?: {
    topic_co_occurrences?: Array<{ topics: string[]; frequency: number; pattern: string }>;
    temporal_emotional_patterns?: Array<{ day: string; emotion: string; frequency: number; pattern: string }>;
  };
  insights?: string;
};

export type ChatResponsePayload = {
  response: string;
  conversation_id: string;
  insights?: ConversationInsights;
  conflicts?: Array<{ statement: string; conflict_with: string; severity?: number }>;
};

export type IdentityBelief = {
  topic: string;
  belief: string;
  confidence?: number;
  evidence?: Record<string, unknown>;
};

export type IdentityOpenLoop = {
  topic: string;
  status?: string;
  importance?: number;
  last_mentioned?: string | null;
};

export type IdentityPattern = {
  pattern_type: string;
  description: string;
  signals?: Record<string, unknown>;
  confidence?: number;
};

export type IdentityEmotion = {
  primary_emotion: string;
  intensity?: number;
  secondary_emotions?: string[];
  context?: Record<string, unknown>;
};

export type IdentityConflict = {
  statement: string;
  conflict_with: string;
  severity?: number;
  resolved?: boolean;
  resolved_at?: string | null;
};

export type Identity = {
  id: string;
  user_id: string;
  version: number;
  state: string;
  traits: Record<string, unknown>;
  values: Record<string, unknown>;
  beliefs: IdentityBelief[];
  open_loops: IdentityOpenLoop[];
  patterns: IdentityPattern[];
  emotions: IdentityEmotion[];
  conflicts: IdentityConflict[];
};

export type IdentityUpdatePayload = {
  state?: string;
  traits?: Record<string, unknown>;
  values?: Record<string, unknown>;
  beliefs?: IdentityBelief[];
  open_loops?: IdentityOpenLoop[];
  patterns?: IdentityPattern[];
  emotions?: IdentityEmotion[];
  conflicts?: IdentityConflict[];
};

export type EvolutionLogEntry = {
  id: string;
  user_id: string;
  identity_id: string;
  field_changed: string;
  old_value: Record<string, unknown> | string | number | boolean | null;
  new_value: Record<string, unknown> | string | number | boolean | null;
  trigger_type: string | null;
  created_at: string;
};

export type MemoryItem = {
  id: string;
  content: string | null;
  memory_tier: string | null;
  importance_score: number | null;
  created_at: string;
};

export type MemorySnapshot = {
  facts: MemoryItem[];
  emotions: MemoryItem[];
  recent: MemoryItem[];
};

export type OnboardingAnswer = {
  question: string;
  answer: string;
};

export type OnboardingPayload = {
  responses: OnboardingAnswer[];
  traits?: Record<string, unknown>;
  values?: Record<string, unknown>;
  preset?: string;
  goals?: string[];
  seed_belief?: string | null;
};

export type ToolRun = {
  id: string;
  name?: string;
  description?: string;
  status: string;
  code?: string;
  result?: string;
  created_at?: string;
};

export type Notification = {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  status: string;
  created_at?: string;
  read_at?: string | null;
};
