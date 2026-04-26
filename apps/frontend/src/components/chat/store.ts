import { create } from "zustand";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
}

interface ChatbotStore {
  messages: ChatMessage[];
  input: string;
  isLoading: boolean;
  conversationId: string | undefined;
  setMessages: (fn: (prev: ChatMessage[]) => ChatMessage[] | ChatMessage[]) => void;
  setInput: (val: string) => void;
  setIsLoading: (val: boolean) => void;
  setConversationId: (val: string | undefined) => void;
  addMessage: (msg: ChatMessage) => void;
  reset: () => void;
}

export const useChatbotStore = create<ChatbotStore>((set) => ({
  messages: [],
  input: "",
  isLoading: false,
  conversationId: undefined,
  setMessages: (fn) =>
    set((state) => ({
      messages: typeof fn === "function" ? fn(state.messages) : fn,
    })),
  setInput: (input) => set({ input }),
  setIsLoading: (isLoading) => set({ isLoading }),
  setConversationId: (conversationId) => set({ conversationId }),
  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),
  reset: () =>
    set({
      messages: [],
      input: "",
      isLoading: false,
      conversationId: undefined,
    }),
}));