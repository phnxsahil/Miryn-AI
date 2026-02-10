export type SharedIdentity = {
  id: string;
  user_id: string;
  version: number;
  state: string;
  traits: Record<string, any>;
  values: Record<string, any>;
  beliefs: any[];
  open_loops: any[];
};

export type SharedMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};
