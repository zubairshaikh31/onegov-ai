import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { z } from "zod";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
}

export function formatINR(paise: number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0 }).format(paise / 100);
}

export function truncate(str: string, max: number): string {
  return str.length <= max ? str : str.slice(0, max - 1) + "…";
}

export function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "response" in error) {
    const resData = (error as { response?: { data?: { message?: string; errors?: Array<{ message: string }> } } }).response?.data;
    if (resData?.message) return resData.message;
    if (resData?.errors?.[0]?.message) return resData.errors[0].message;
  }
  if (error instanceof Error) {
    if (error.message === "Network Error") {
      return "Unable to connect to backend server (http://localhost:8000). Please verify backend is running.";
    }
    return error.message;
  }
  if (typeof error === "string") return error;
  return "An unexpected error occurred.";
}

const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .max(64, "Password must be under 64 characters")
  .regex(/[A-Z]/, "Must include at least one uppercase letter")
  .regex(/[a-z]/, "Must include at least one lowercase letter")
  .regex(/[0-9]/, "Must include at least one number")
  .regex(/[@$!%*?&]/, "Must include at least one special character (@$!%*?&)");

export const registerSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters").max(150),
  email: z.string().email("Enter a valid email address"),
  password: passwordSchema,
  confirm_password: z.string(),
  phone: z.string().regex(/^\+?[1-9]\d{9,14}$/, "Enter a valid phone number").optional().or(z.literal("")),
}).refine(d => d.password === d.confirm_password, { message: "Passwords do not match", path: ["confirm_password"] });

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export const otpSchema = z.object({
  otp: z.string().length(6, "Enter the 6-digit code").regex(/^\d{6}$/, "Code must be 6 digits"),
});

export const forgotPasswordSchema = z.object({
  email: z.string().email("Enter a valid email address"),
});

export const resetPasswordSchema = z.object({
  new_password: passwordSchema,
  confirm_password: z.string(),
}).refine(d => d.new_password === d.confirm_password, { message: "Passwords do not match", path: ["confirm_password"] });

export type RegisterFormValues = z.infer<typeof registerSchema>;
export type LoginFormValues = z.infer<typeof loginSchema>;
export type OTPFormValues = z.infer<typeof otpSchema>;
export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;
