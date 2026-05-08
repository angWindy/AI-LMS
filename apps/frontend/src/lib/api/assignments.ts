import { apiClient } from "./client";
import { Assignment } from "@/types";

export interface AssignmentOptionInput {
  option_text: string;
  is_correct: boolean;
}

export interface AssignmentQuestionInput {
  question_text: string;
  explanation?: string;
  options: AssignmentOptionInput[];
}

export interface AssignmentCreateData {
  lesson_id?: string;
  title: string;
  questions: AssignmentQuestionInput[];
}

export interface AssignmentUpdateData {
  title?: string;
  is_published?: boolean;
  questions?: AssignmentQuestionInput[];
}

export interface AssignmentGenerateDraftData {
  lesson_id: string;
  question_count: number;
  title?: string;
}

export const assignmentApi = {
  create: async (courseId: string, data: AssignmentCreateData): Promise<Assignment> => {
    const response = await apiClient.post("/assignments", data, { params: { course_id: courseId } });
    return response.data;
  },

  generateDraft: async (courseId: string, data: AssignmentGenerateDraftData): Promise<Assignment> => {
    const response = await apiClient.post("/assignments/generate-draft", data, {
      params: { course_id: courseId },
      timeout: 30 * 60 * 1000,
    });
    return response.data;
  },

  listByCourse: async (courseId: string, includeUnpublished = false): Promise<Assignment[]> => {
    const response = await apiClient.get("/assignments", {
      params: { course_id: courseId, include_unpublished: includeUnpublished },
    });
    return response.data;
  },

  getById: async (assignmentId: string): Promise<Assignment> => {
    const response = await apiClient.get(`/assignments/${assignmentId}`);
    return response.data;
  },

  update: async (assignmentId: string, data: AssignmentUpdateData): Promise<Assignment> => {
    const response = await apiClient.put(`/assignments/${assignmentId}`, data);
    return response.data;
  },

  publish: async (assignmentId: string): Promise<Assignment> => {
    const response = await apiClient.post(`/assignments/${assignmentId}/publish`);
    return response.data;
  },

  delete: async (assignmentId: string): Promise<void> => {
    await apiClient.delete(`/assignments/${assignmentId}`);
  },
};
