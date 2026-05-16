import { apiClient } from "./client";
import {
  QuestionBankCourse,
  QuestionBankQuestion,
  QuestionDifficulty,
  QuestionPurposeType,
} from "@/types";

export interface QuestionBankOptionInput {
  option_text: string;
  is_correct: boolean;
}

export interface QuestionBankQuestionCreateData {
  course_id: string;
  lesson_id?: string | null;
  question_text: string;
  difficulty?: QuestionDifficulty;
  purpose_type?: QuestionPurposeType;
  options: QuestionBankOptionInput[];
}

export interface QuestionBankQuestionUpdateData {
  lesson_id?: string | null;
  question_text: string;
  difficulty: QuestionDifficulty;
  purpose_type: QuestionPurposeType;
  options?: QuestionBankOptionInput[];
}

export interface QuestionBankGenerateData {
  course_id: string;
  lesson_id: string;
  question_count: number;
}

export const questionBankApi = {
  listCourses: async (): Promise<QuestionBankCourse[]> => {
    const response = await apiClient.get("/question-bank/courses");
    return response.data;
  },

  listQuestions: async (params?: { course_id?: string; lesson_id?: string }): Promise<QuestionBankQuestion[]> => {
    const response = await apiClient.get("/question-bank/questions", { params });
    return response.data;
  },

  createQuestion: async (data: QuestionBankQuestionCreateData): Promise<QuestionBankQuestion> => {
    const response = await apiClient.post("/question-bank/questions", data);
    return response.data;
  },

  generateQuestions: async (data: QuestionBankGenerateData): Promise<QuestionBankQuestion[]> => {
    const response = await apiClient.post("/question-bank/generate", data, {
      timeout: 30 * 60 * 1000,
    });
    return response.data;
  },

  updateQuestion: async (questionId: string, data: QuestionBankQuestionUpdateData): Promise<QuestionBankQuestion> => {
    const response = await apiClient.put(`/question-bank/questions/${questionId}`, data);
    return response.data;
  },

  deleteQuestion: async (questionId: string): Promise<void> => {
    await apiClient.delete(`/question-bank/questions/${questionId}`);
  },
};
