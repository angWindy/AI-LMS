import { apiClient } from "./client";
import { SlideDeck } from "@/types";

export interface SlideDeckGenerateDraftData {
  lesson_id: string;
  slide_count: number;
  title?: string;
}

export const slideDeckApi = {
  generateDraft: async (
    courseId: string,
    data: SlideDeckGenerateDraftData
  ): Promise<SlideDeck> => {
    const response = await apiClient.post("/slides/generate-draft", data, {
      params: { course_id: courseId },
      timeout: 30 * 60 * 1000,
    });
    return response.data;
  },

  listByCourse: async (
    courseId: string,
    includeUnpublished = false,
    lessonId?: string
  ): Promise<SlideDeck[]> => {
    const response = await apiClient.get("/slides", {
      params: {
        course_id: courseId,
        include_unpublished: includeUnpublished,
        lesson_id: lessonId,
      },
    });
    return response.data;
  },

  getById: async (slideDeckId: string): Promise<SlideDeck> => {
    const response = await apiClient.get(`/slides/${slideDeckId}`);
    return response.data;
  },

  publish: async (slideDeckId: string): Promise<SlideDeck> => {
    const response = await apiClient.post(`/slides/${slideDeckId}/publish`);
    return response.data;
  },

  delete: async (slideDeckId: string): Promise<void> => {
    await apiClient.delete(`/slides/${slideDeckId}`);
  },
};
