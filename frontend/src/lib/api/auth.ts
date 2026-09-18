import apiClient from "./client";
import type { ApiResponse, LoginResponse, RegisterResponse, User } from "@/types/auth";

export const authApi = {
  register: (body: { full_name: string; email: string; password: string; phone?: string }) =>
    apiClient.post<ApiResponse<RegisterResponse>>("/auth/register", body).then(r => r.data),

  login: (body: { email: string; password: string }) =>
    apiClient.post<ApiResponse<LoginResponse>>("/auth/login", body).then(r => r.data),

  googleLogin: (id_token: string) =>
    apiClient.post<ApiResponse<LoginResponse>>("/auth/google", { id_token }).then(r => r.data),

  verifyOtp: (body: { email: string; otp: string }) =>
    apiClient.post<ApiResponse<null>>("/auth/verify-otp", body).then(r => r.data),

  resendOtp: (email: string) =>
    apiClient.post<ApiResponse<null>>("/auth/resend-otp", { email }).then(r => r.data),

  forgotPassword: (email: string) =>
    apiClient.post<ApiResponse<null>>("/auth/forgot-password", { email }).then(r => r.data),

  resetPassword: (body: { email: string; otp: string; new_password: string; confirm_password: string }) =>
    apiClient.post<ApiResponse<null>>("/auth/reset-password", body).then(r => r.data),

  logout: (refresh_token: string) =>
    apiClient.post<ApiResponse<null>>("/auth/logout", { refresh_token }).then(r => r.data),

  getMe: () =>
    apiClient.get<ApiResponse<User>>("/users/me").then(r => r.data),
};
