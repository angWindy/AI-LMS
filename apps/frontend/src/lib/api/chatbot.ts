import { apiClient } from "./client";

const CHATBOT_REQUEST_TIMEOUT_MS = 4 * 60 * 1000;

export interface ChatMessagePayload {
  role: string | "system" | "user" | "assistant";
  content: string;
}

export interface TeachingImagePayload {
  mime_type: "image/png" | "image/jpeg" | "image/webp" | "image/gif";
  data_base64: string;
  description?: string;
  source?: string;
}

export interface ChatbotAskRequest {
  question: string;
  conversation_id?: string;
  conversation_title?: string;
  course_id?: string;
  lesson_id?: string;
  history?: ChatMessagePayload[];
  context_docs?: string[];
  image_contexts?: string[];
  teaching_images?: TeachingImagePayload[];
  temperature?: number;
  max_output_tokens?: number;
  thinking_level?: "low" | "medium" | "high";
}

export interface AssignmentChatbotAskRequest {
  question: string;
  assignment_id: string;
  conversation_id?: string;
  history?: ChatMessagePayload[];
  temperature?: number;
  max_output_tokens?: number;
  thinking_level?: "low" | "medium" | "high";
}

export interface AssignmentChatbotPreloadRequest {
  assignment_id: string;
}

export interface AssignmentChatbotPreloadResponse {
  assignment_id: string;
  question_count: number;
  context_length: number;
}

export interface ChatbotAskResponse {
  answer: string;
  conversation_id: string;
  conversation_title?: string;
  provider: string;
  model: string;
  finish_reason?: string;
  usage?: Record<string, number>;
  messages?: ChatMessagePayload[];
}

export interface ConversationSummaryPayload {
  id: string;
  title?: string;
  course_id?: string;
  lesson_id?: string;
  is_active: boolean;
  updated_at: string;
}

export interface ConversationMessagePayload {
  id: string;
  role: string;
  content: string;
  model_version?: string;
  tokens_used?: number;
  created_at: string;
}

export interface ConversationMessagesResponse {
  conversation_id: string;
  messages: ConversationMessagePayload[];
}

export const chatbotApi = {
  ask: async (data: ChatbotAskRequest): Promise<ChatbotAskResponse> => {
    const response = await apiClient.post<ChatbotAskRequest, any>("/chatbot/ask", data, {
      timeout: CHATBOT_REQUEST_TIMEOUT_MS,
    });
    return response.data;
  },

  askAssignment: async (data: AssignmentChatbotAskRequest): Promise<ChatbotAskResponse> => {
    const response = await apiClient.post<AssignmentChatbotAskRequest, any>("/chatbot/assignment/ask", data, {
      timeout: CHATBOT_REQUEST_TIMEOUT_MS,
    });
    return response.data;
  },

  preloadAssignment: async (data: AssignmentChatbotPreloadRequest): Promise<AssignmentChatbotPreloadResponse> => {
    const response = await apiClient.post<AssignmentChatbotPreloadRequest, any>("/chatbot/assignment/preload", data);
    return response.data;
  },

  getConversations: async (limit: number = 20): Promise<ConversationSummaryPayload[]> => {
    const response = await apiClient.get<ConversationSummaryPayload[]>(`/chatbot/conversations?limit=${limit}`);
    return response.data;
  },

  getConversationMessages: async (conversationId: string): Promise<ConversationMessagesResponse> => {
    const response = await apiClient.get<ConversationMessagesResponse>(`/chatbot/conversations/${conversationId}/messages`);
    return response.data;
  },

  getProviders: async (): Promise<any> => {
    const response = await apiClient.get<any>("/chatbot/providers");
    return response.data;
  },
};
