import { apiClient } from "./client";
import { AuthResponse, LoginRequest, RegisterRequest, User, TokenResponse } from "@/types";

export const authApi = {
  // Register new user
  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post("/auth/register", data);
    return response.data;
  },

  // Login
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post("/auth/login", data);
    return response.data;
  },

  // Refresh token
  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  // Logout
  logout: async (): Promise<void> => {
    await apiClient.post("/auth/logout");
  },

  // Get current user
  me: async (): Promise<User> => {
    const response = await apiClient.get("/auth/me");
    return response.data;
  },

  // Update current user
  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await apiClient.put("/auth/me", data);
    return response.data;
  },

  // Change password
  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await apiClient.put("/auth/me/password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};
