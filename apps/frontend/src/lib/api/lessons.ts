import { apiClient } from "./client";

export interface Lesson {
  id: string;
  course_id: string;
  title: string;
  description?: string;
  content?: string;
  video_url?: string;
  video_duration?: number;
  thumbnail_url?: string;
  order_index: number;
  is_published: boolean;
  is_preview: boolean;
  created_at: string;
  updated_at: string;
  materials?: Material[];
}

export interface Material {
  id: string;
  course_id?: string | null;
  lesson_id?: string | null;
  title: string;
  description?: string;
  type: "video" | "document" | "link" | "quiz";
  file_url?: string;
  file_size?: number;
  mime_type?: string;
  order_index: number;
  created_at: string;
}

export interface CreateLessonData {
  title: string;
  description?: string;
  content?: string;
  order_index?: number;
  is_preview?: boolean;
  video_url?: string;
  video_duration?: number;
}

export interface UpdateLessonData {
  title?: string;
  description?: string;
  content?: string;
  is_preview?: boolean;
  is_published?: boolean;
  video_url?: string | null;
  video_duration?: number;
  thumbnail_url?: string;
}

export interface LessonProgress {
  lesson_id: string;
  watched_seconds: number;
  total_seconds?: number;
  is_completed: boolean;
  last_position: number;
  last_accessed_at: string;
}

export const lessonApi = {
  // Create lesson for a course
  create: async (courseId: string, data: CreateLessonData): Promise<Lesson> => {
    const response = await apiClient.post("/lessons", data, { params: { course_id: courseId } });
    return response.data;
  },

  // Get lesson by ID (includes materials)
  getById: async (lessonId: string): Promise<Lesson> => {
    const response = await apiClient.get(`/lessons/${lessonId}`);
    return response.data;
  },

  // Update lesson
  update: async (lessonId: string, data: UpdateLessonData): Promise<Lesson> => {
    const response = await apiClient.put(`/lessons/${lessonId}`, data);
    return response.data;
  },

  // Delete lesson
  delete: async (lessonId: string): Promise<void> => {
    await apiClient.delete(`/lessons/${lessonId}`);
  },

  // Update lesson order
  updateOrder: async (lessonId: string, orderIndex: number): Promise<Lesson> => {
    const response = await apiClient.patch(`/lessons/${lessonId}/order`, { order_index: orderIndex });
    return response.data;
  },

  // Publish lesson
  publish: async (lessonId: string): Promise<Lesson> => {
    const response = await apiClient.post(`/lessons/${lessonId}/publish`);
    return response.data;
  },

  // Get lessons for a course
  getByCourse: async (courseId: string): Promise<Lesson[]> => {
    const response = await apiClient.get(`/courses/${courseId}/lessons`);
    return response.data;
  },

  // === Materials ===
  
  // Get materials for a lesson
  getMaterials: async (lessonId: string): Promise<Material[]> => {
    const response = await apiClient.get(`/lessons/${lessonId}/materials`);
    return response.data;
  },

  // Upload material (file upload)
  uploadMaterial: async (
    lessonId: string,
    data: { title?: string; description?: string; type: string; file?: File; external_url?: string }
  ): Promise<Material> => {
    const formData = new FormData();
    if (data.title?.trim()) formData.append("title", data.title.trim());
    formData.append("type", data.type);
    if (data.description) formData.append("description", data.description);
    if (data.file) formData.append("file", data.file);
    if (data.external_url) formData.append("external_url", data.external_url);

    const response = await apiClient.post(`/lessons/${lessonId}/materials`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  // Delete material
  deleteMaterial: async (materialId: string): Promise<void> => {
    await apiClient.delete(`/lessons/materials/${materialId}`);
  },

  // === Progress ===
  
  // Update progress
  updateProgress: async (
    lessonId: string,
    data: { watched_seconds: number; last_position: number; is_completed?: boolean }
  ): Promise<LessonProgress> => {
    const response = await apiClient.post(`/lessons/${lessonId}/progress`, data);
    return response.data;
  },

  // Get progress
  getProgress: async (lessonId: string): Promise<LessonProgress | null> => {
    try {
      const response = await apiClient.get(`/lessons/${lessonId}/progress`);
      return response.data;
    } catch {
      return null;
    }
  },
};
