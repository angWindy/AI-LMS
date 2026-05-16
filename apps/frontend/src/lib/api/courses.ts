import { apiClient } from "./client";
import { Course, CourseDetail, PaginatedResponse } from "@/types";
import { Material } from "./lessons";

export const courseApi = {
  // Get all courses (paginated)
  getAll: async (params?: { status?: string; page?: number; per_page?: number }): Promise<PaginatedResponse<Course>> => {
    const response = await apiClient.get("/courses", { params });
    return response.data;
  },

  // Get course by slug
  getBySlug: async (slug: string): Promise<CourseDetail> => {
    const response = await apiClient.get(`/courses/slug/${slug}`);
    return response.data;
  },

  // Get course by ID
  getById: async (id: string): Promise<CourseDetail> => {
    const response = await apiClient.get(`/courses/${id}`);
    return response.data;
  },

  // Get my courses (instructor) - /courses/my/teaching
  getMyCourses: async (): Promise<Course[]> => {
    const response = await apiClient.get("/courses/my/teaching");
    return response.data;
  },

  // Create course
  create: async (data: Partial<Course>): Promise<Course> => {
    const response = await apiClient.post("/courses", data);
    return response.data;
  },

  // Update course
  update: async (id: string, data: Partial<Course>): Promise<Course> => {
    const response = await apiClient.put(`/courses/${id}`, data);
    return response.data;
  },

  // Delete course
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/courses/${id}`);
  },

  // Publish course
  publish: async (id: string): Promise<Course> => {
    const response = await apiClient.post(`/courses/${id}/publish`);
    return response.data;
  },

  // Archive course
  archive: async (id: string): Promise<Course> => {
    const response = await apiClient.post(`/courses/${id}/archive`);
    return response.data;
  },

  // Get course lessons
  getLessons: async (courseId: string) => {
    const response = await apiClient.get(`/courses/${courseId}/lessons`);
    return response.data;
  },

  // Get materials attached directly to the course
  getMaterials: async (courseId: string): Promise<Material[]> => {
    const response = await apiClient.get(`/courses/${courseId}/materials`);
    return response.data;
  },

  // Upload course-level material
  uploadMaterial: async (
    courseId: string,
    data: { title: string; description?: string; type: string; file?: File; external_url?: string }
  ): Promise<Material> => {
    const formData = new FormData();
    formData.append("title", data.title);
    formData.append("type", data.type);
    if (data.description) formData.append("description", data.description);
    if (data.file) formData.append("file", data.file);
    if (data.external_url) formData.append("external_url", data.external_url);

    const response = await apiClient.post(`/courses/${courseId}/materials`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  // Delete course-level material
  deleteMaterial: async (materialId: string): Promise<void> => {
    await apiClient.delete(`/courses/materials/${materialId}`);
  },
};
