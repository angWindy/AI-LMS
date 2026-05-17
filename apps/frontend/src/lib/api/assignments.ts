import { apiClient } from "./client";
import {
  Assignment,
  AssignmentQuestionType,
  AssignmentType,
  QuestionDifficulty,
  QuestionPurposeType,
  Submission,
} from "@/types";

export interface AssignmentOptionInput {
  option_text: string;
  is_correct: boolean;
}

export interface AssignmentQuestionInput {
  question_text: string;
  question_type?: AssignmentQuestionType;
  correct_answer_text?: string;
  difficulty?: QuestionDifficulty;
  purpose_type?: QuestionPurposeType;
  options: AssignmentOptionInput[];
}

export interface AssignmentCreateData {
  lesson_id?: string;
  assignment_type?: AssignmentType;
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

export interface AssignmentGenerateFromBankData {
  lesson_id?: string;
  question_count: number;
  title?: string;
}

export interface AssignmentGenerateTestData {
  lesson_ids: string[];
  question_count: number;
  title?: string;
}

export interface AssignmentSubmitAnswerData {
  question_id: string;
  selected_option_id?: string;
  answer_text?: string;
}

export interface AssignmentSubmitData {
  answers: AssignmentSubmitAnswerData[];
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

  generateFromBank: async (courseId: string, data: AssignmentGenerateFromBankData): Promise<Assignment> => {
    const response = await apiClient.post("/assignments/generate-from-bank", data, {
      params: { course_id: courseId },
    });
    return response.data;
  },

  generateTest: async (courseId: string, data: AssignmentGenerateTestData): Promise<Assignment> => {
    const response = await apiClient.post("/assignments/generate-test", data, {
      params: { course_id: courseId },
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

  submit: async (assignmentId: string, data: AssignmentSubmitData): Promise<Submission> => {
    const response = await apiClient.post(`/assignments/${assignmentId}/submit`, data, {
      timeout: 30 * 60 * 1000,
    });
    return response.data;
  },

  getMySubmission: async (assignmentId: string): Promise<Submission> => {
    const response = await apiClient.get(`/assignments/${assignmentId}/submission`);
    return response.data;
  },

  resetMySubmission: async (assignmentId: string): Promise<void> => {
    await apiClient.delete(`/assignments/${assignmentId}/submission`);
  },

  delete: async (assignmentId: string): Promise<void> => {
    await apiClient.delete(`/assignments/${assignmentId}`);
  },
};
