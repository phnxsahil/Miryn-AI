export type Message = {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
  importance_score?: number;
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

export type DemoPersonaCard = {
  user_id: string;
  key: string;
  label: string;
  subtitle: string;
  email: string;
  goal: string;
};

export type IdentityMetrics = {
  stability_score: number | null;
  drift: number | null;
  total_versions: number;
  version_timeline: Array<{
    version: number;
    state?: string;
    belief_count: number;
    open_loop_count: number;
    drift_score: number;
    created_at: string;
  }>;
};

export type EmotionMetrics = {
  mood_score: number | null;
  volatility: number | null;
  trend: string;
  entropy: number | null;
  dominant_emotions: Array<{ emotion: string; count: number }>;
};

export type MemoryMetrics = {
  total_messages: number;
  core_count: number;
  episodic_count: number;
  transient_count: number;
  emotion_tagged_count: number;
  average_importance: number;
  distribution: Array<{ tier: string; count: number }>;
};

export type DemoConversation = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
};

export type DemoPersonaDetail = {
  profile: {
    user_id: string;
    label: string;
    subtitle: string;
    email: string;
    goal: string;
    report_summary: string;
  };
  identity: Identity;
  identity_metrics: IdentityMetrics;
  emotion_metrics: EmotionMetrics;
  memory_metrics: MemoryMetrics;
  memory_snapshot: {
    recent: Message[];
    facts: Message[];
    emotions: Message[];
  };
  conversations: DemoConversation[];
};

export type DifferenceMetrics = {
  shared_belief_topics: string[];
  left_only_belief_topics: string[];
  right_only_belief_topics: string[];
  shared_open_loops: string[];
  left_only_open_loops: string[];
  right_only_open_loops: string[];
  shared_pattern_types: string[];
  left_only_pattern_types: string[];
  right_only_pattern_types: string[];
  left_conflict_count: number;
  right_conflict_count: number;
};

export type ComparePayload = {
  generated_at: string;
  left: DemoPersonaDetail;
  right: DemoPersonaDetail;
  difference_metrics: DifferenceMetrics;
  charts: {
    drift_timeline: Array<{ version: number; left: number; right: number }>;
    emotion_distribution: {
      left: Array<{ emotion: string; count: number }>;
      right: Array<{ emotion: string; count: number }>;
    };
    memory_distribution: {
      left: Array<{ tier: string; count: number }>;
      right: Array<{ tier: string; count: number }>;
    };
    identity_counts: {
      left: Array<{ label: string; count: number }>;
      right: Array<{ label: string; count: number }>;
    };
  };
  report_sections: {
    introduction: string;
    comparison_dimensions: Array<{ title: string; body: string }>;
    drift_analysis: string;
    memory_observations: string;
    miryn_standout: string;
    conclusion: string;
  };
};

export type CompareReport = {
  generated_at: string;
  left_user_id: string;
  right_user_id: string;
  markdown: string;
  sections: ComparePayload["report_sections"];
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

export type Session = {
  ip: string;
  timestamp: string;
};

export type NotificationPreferences = {
  checkin_reminders: boolean;
  weekly_digest: boolean;
  browser_push: boolean;
  data_retention: string;
};

export type User = {
  id: string;
  email: string;
  has_password: boolean;
  notification_preferences: NotificationPreferences;
  data_retention: string;
  encryption_enabled: boolean;
};

export type ImportStatus = {
  status: "none" | "processing" | "complete" | "error";
  progress?: number;
  message?: string;
  conversations_processed?: number;
  memories_added?: number;
};
