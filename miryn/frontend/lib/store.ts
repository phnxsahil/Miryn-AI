import { create } from 'zustand';
import type { Message, ConversationInsights, ToolRun, Notification } from './types';

interface ChatState {
  messages: Message[];
  loading: boolean;
  streaming: boolean;
  conversationId: string | null;
  status: string | null;
  insights: ConversationInsights | null;
  conflicts: Array<{ statement: string; conflict_with: string; severity?: number }>;
  pendingTools: ToolRun[];
  notifications: Notification[];
  secondaryPanelsReady: boolean;
  streamingIndex: number | null;

  // Actions
  setMessages: (messages: Message[] | ((prev: Message[]) => Message[])) => void;
  appendMessage: (message: Message) => void;
  updateStreamingMessage: (chunk: string) => void;
  setLoading: (loading: boolean) => void;
  setStreaming: (streaming: boolean) => void;
  setConversationId: (id: string | null) => void;
  setStatus: (status: string | null) => void;
  setInsights: (insights: ConversationInsights | null) => void;
  setConflicts: (conflicts: Array<{ statement: string; conflict_with: string; severity?: number }>) => void;
  setPendingTools: (tools: ToolRun[] | ((prev: ToolRun[]) => ToolRun[])) => void;
  setNotifications: (notifications: Notification[] | ((prev: Notification[]) => Notification[])) => void;
  setSecondaryPanelsReady: (ready: boolean) => void;
  setStreamingIndex: (index: number | null) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  loading: false,
  streaming: false,
  conversationId: null,
  status: null,
  insights: null,
  conflicts: [],
  pendingTools: [],
  notifications: [],
  secondaryPanelsReady: false,
  streamingIndex: null,

  setMessages: (messages) => set((state) => ({
    messages: typeof messages === 'function' ? messages(state.messages) : messages
  })),

  appendMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  updateStreamingMessage: (chunk) => set((state) => {
    if (state.streamingIndex === null || !state.messages[state.streamingIndex]) return state;
    const newMessages = [...state.messages];
    newMessages[state.streamingIndex] = {
      ...newMessages[state.streamingIndex],
      content: newMessages[state.streamingIndex].content + chunk
    };
    return { messages: newMessages };
  }),

  setLoading: (loading) => set({ loading }),
  setStreaming: (streaming) => set({ streaming }),
  setConversationId: (id) => set({ conversationId: id }),
  setStatus: (status) => set({ status }),
  setInsights: (insights) => set({ insights }),
  setConflicts: (conflicts) => set({ conflicts }),

  setPendingTools: (tools) => set((state) => ({
    pendingTools: typeof tools === 'function' ? tools(state.pendingTools) : tools
  })),

  setNotifications: (notifications) => set((state) => ({
    notifications: typeof notifications === 'function' ? notifications(state.notifications) : notifications
  })),

  setSecondaryPanelsReady: (ready) => set({ secondaryPanelsReady: ready }),
  setStreamingIndex: (index) => set({ streamingIndex: index }),
}));
