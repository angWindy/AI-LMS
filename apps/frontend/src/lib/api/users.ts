import { apiClient } from "./client";
import { User, UserRole } from "@/types";

interface CreateUserData {
  email: string;
  full_name: string;
  password: string;
  role: UserRole;
}

export const userApi = {
  // Get all users (admin only)
  getAll: async (): Promise<User[]> => {
    const response = await apiClient.get("/users");
    // API returns { items: [...], total, page, ... } but we just need the items array
    return response.data.items || response.data;
  },

  // Get user by ID
  getById: async (id: string): Promise<User> => {
    const response = await apiClient.get(`/users/${id}`);
    return response.data;
  },

  // Create user (admin only)
  create: async (data: CreateUserData): Promise<User> => {
    const response = await apiClient.post("/users", data);
    return response.data;
  },

  // Update user (admin only)
  update: async (id: string, data: Partial<User>): Promise<User> => {
    const response = await apiClient.put(`/users/${id}`, data);
    return response.data;
  },

  // Delete user (admin only)
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/users/${id}`);
  },
};
