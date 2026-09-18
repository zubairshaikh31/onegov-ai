"use client";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { authApi } from "@/lib/api/auth";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/lib/utils";

export function useAuth() {
  const router = useRouter();
  const { setAuth, clearAuth, isAuthenticated, user, isAdmin, refreshToken } = useAuthStore();

  const loginMutation = useMutation({
    mutationFn: async (data: { email: string; password: string }) => {
      const loginRes = await authApi.login(data);
      if (!loginRes.success || !loginRes.data) {
        throw new Error(loginRes.message || "Login failed");
      }

      useAuthStore.getState().setTokens(
        loginRes.data.access_token,
        loginRes.data.refresh_token
      );

      const me = await authApi.getMe();
      if (!me.success || !me.data) {
        throw new Error(me.message || "Failed to fetch profile");
      }

      useAuthStore.getState().setAuth(
        me.data,
        loginRes.data.access_token,
        loginRes.data.refresh_token
      );

      return me;
    },
    onSuccess: (me) => {
      if (!me.data) return;
      const isAdminUser = me.data.roles.some((r) => r.name === "admin");
      toast.success(`Welcome back, ${me.data.full_name.split(" ")[0]}!`);
      router.push(isAdminUser ? "/admin" : "/dashboard");
    },
    onError: (error: unknown) => {
      const msg = (error as { response?: { data?: { message?: string } } })?.response?.data?.message ?? getErrorMessage(error);
      toast.error(msg);
    },
  });

  const googleLoginMutation = useMutation({
    mutationFn: async (idToken: string) => {
      const loginRes = await authApi.googleLogin(idToken);
      if (!loginRes.success || !loginRes.data) {
        throw new Error(loginRes.message || "Google sign-in failed");
      }

      useAuthStore.getState().setTokens(
        loginRes.data.access_token,
        loginRes.data.refresh_token
      );

      const me = await authApi.getMe();
      if (!me.success || !me.data) {
        throw new Error(me.message || "Failed to fetch profile");
      }

      useAuthStore.getState().setAuth(
        me.data,
        loginRes.data.access_token,
        loginRes.data.refresh_token
      );

      return me;
    },
    onSuccess: (me) => {
      if (!me.data) return;
      const isAdminUser = me.data.roles.some((r) => r.name === "admin");
      toast.success(`Welcome back, ${me.data.full_name.split(" ")[0]}!`);
      router.push(isAdminUser ? "/admin" : "/dashboard");
    },
    onError: (error: unknown) => {
      const msg = (error as { response?: { data?: { message?: string } } })?.response?.data?.message ?? getErrorMessage(error);
      toast.error(msg);
    },
  });

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (res) => {
      if (!res.success) { toast.error(res.message); return; }
      toast.success("Account created! Check your email for the verification code.");
      router.push(`/verify-otp?email=${encodeURIComponent(res.data?.email ?? "")}`);
    },
    onError: (error: unknown) => {
      const msg = (error as { response?: { data?: { message?: string } } })?.response?.data?.message ?? getErrorMessage(error);
      toast.error(msg);
    },
  });

  const verifyOtpMutation = useMutation({
    mutationFn: authApi.verifyOtp,
    onSuccess: (res) => {
      if (!res.success) { toast.error(res.message); return; }
      toast.success("Email verified! You can now sign in.");
      router.push("/login");
    },
    onError: (error: unknown) => {
      const msg = (error as { response?: { data?: { message?: string } } })?.response?.data?.message ?? "Invalid or expired code.";
      toast.error(msg);
    },
  });

  const resendOtpMutation = useMutation({
    mutationFn: authApi.resendOtp,
    onSuccess: () => toast.success("A new verification code has been sent."),
    onError: () => toast.error("Could not resend code. Please try again."),
  });

  const forgotPasswordMutation = useMutation({
    mutationFn: authApi.forgotPassword,
    onSuccess: (res) => toast.success(res.message),
    onError: () => toast.error("Something went wrong. Please try again."),
  });

  const resetPasswordMutation = useMutation({
    mutationFn: authApi.resetPassword,
    onSuccess: (res) => {
      if (!res.success) { toast.error(res.message); return; }
      toast.success("Password reset successfully. Please sign in.");
      router.push("/login");
    },
    onError: (error: unknown) => {
      const msg = (error as { response?: { data?: { message?: string } } })?.response?.data?.message ?? "Reset failed. Please try again.";
      toast.error(msg);
    },
  });

  const logoutMutation = useMutation({
    mutationFn: (rt: string) => authApi.logout(rt),
    onSettled: () => { clearAuth(); router.push("/login"); toast.success("Logged out successfully."); },
  });

  const logout = () => {
    if (refreshToken) logoutMutation.mutate(refreshToken);
    else { clearAuth(); router.push("/login"); }
  };

  return {
    user, isAuthenticated, isAdmin,
    login: loginMutation.mutate,           isLoggingIn: loginMutation.isPending,
    googleLogin: googleLoginMutation.mutate, isLoggingInGoogle: googleLoginMutation.isPending,
    register: registerMutation.mutate,     isRegistering: registerMutation.isPending,
    verifyOtp: verifyOtpMutation.mutate,   isVerifying: verifyOtpMutation.isPending,
    resendOtp: resendOtpMutation.mutate,   isResending: resendOtpMutation.isPending,
    forgotPassword: forgotPasswordMutation.mutate, isSendingReset: forgotPasswordMutation.isPending,
    resetPassword: resetPasswordMutation.mutate,   isResettingPassword: resetPasswordMutation.isPending,
    logout,                                isLoggingOut: logoutMutation.isPending,
  };
}

