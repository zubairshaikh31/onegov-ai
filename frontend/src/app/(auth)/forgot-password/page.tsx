"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, KeyRound, Lock } from "lucide-react";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { AuthCard } from "@/components/auth/AuthCard";
import { OTPInput } from "@/components/auth/OTPInput";
import { PasswordStrength } from "@/components/auth/PasswordStrength";

const emailSchema = z.object({ email: z.string().email("Enter a valid email address") });
const resetSchema = z
  .object({
    otp: z.string().length(6, "Enter the 6-digit OTP code").regex(/^\d{6}$/),
    new_password: z
      .string()
      .min(8, "Minimum 8 characters")
      .regex(/[A-Z]/, "Requires uppercase letter")
      .regex(/[a-z]/, "Requires lowercase letter")
      .regex(/[0-9]/, "Requires number")
      .regex(/[@$!%*?&]/, "Requires special character"),
    confirm_password: z.string(),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type EmailForm = z.infer<typeof emailSchema>;
type ResetForm = z.infer<typeof resetSchema>;

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<"email" | "reset">("email");
  const [pendingEmail, setPendingEmail] = useState("");
  const { forgotPassword, isSendingReset, resetPassword, isResettingPassword } = useAuth();

  const emailForm = useForm<EmailForm>({ resolver: zodResolver(emailSchema) });
  const resetForm = useForm<ResetForm>({
    resolver: zodResolver(resetSchema),
    mode: "onChange",
  });

  const newPasswordVal = resetForm.watch("new_password", "");

  const onEmailSubmit = (data: EmailForm) => {
    setPendingEmail(data.email);
    forgotPassword(data.email);
    setTimeout(() => setStep("reset"), 600);
  };

  const onResetSubmit = (data: ResetForm) => {
    resetPassword({
      email: pendingEmail,
      otp: data.otp,
      new_password: data.new_password,
      confirm_password: data.confirm_password,
    });
  };

  return (
    <AuthCard
      title={step === "email" ? "Reset your password" : "Set new password"}
      subtitle={
        step === "email"
          ? "Enter your account email to receive a 6-digit recovery OTP"
          : `Enter the code sent to ${pendingEmail}`
      }
      icon={
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-500/10 border border-amber-500/20">
          <KeyRound className="h-7 w-7 text-amber-500" />
        </div>
      }
    >
      <div className="space-y-6">
        {/* Progress indicator */}
        <div className="flex justify-center gap-2 mb-2">
          {["email", "reset"].map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div
                className={cn(
                  "h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold transition-all",
                  step === s || (i === 0 && step === "reset")
                    ? "bg-primary text-primary-foreground shadow-md"
                    : "bg-secondary text-muted-foreground"
                )}
              >
                {i + 1}
              </div>
              {i < 1 && (
                <div
                  className={cn(
                    "w-12 h-0.5 transition-all duration-300",
                    step === "reset" ? "bg-primary" : "bg-border"
                  )}
                />
              )}
            </div>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {step === "email" ? (
            <motion.form
              key="email"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              onSubmit={emailForm.handleSubmit(onEmailSubmit)}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">Email address</label>
                <input
                  type="email"
                  placeholder="you@example.com"
                  className={cn("input-premium", emailForm.formState.errors.email && "border-destructive")}
                  {...emailForm.register("email")}
                />
                {emailForm.formState.errors.email && (
                  <p className="text-xs text-destructive">{emailForm.formState.errors.email.message}</p>
                )}
              </div>

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={isSendingReset}
                className="btn-primary w-full py-3 text-sm font-semibold rounded-xl"
              >
                {isSendingReset ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Sending OTP…
                  </>
                ) : (
                  "Send recovery code"
                )}
              </motion.button>
            </motion.form>
          ) : (
            <motion.form
              key="reset"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              onSubmit={resetForm.handleSubmit(onResetSubmit)}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">6-Digit OTP Code</label>
                <OTPInput
                  length={6}
                  onComplete={(val) => resetForm.setValue("otp", val)}
                  onResend={() => forgotPassword(pendingEmail)}
                  isResending={isSendingReset}
                />
                {resetForm.formState.errors.otp && (
                  <p className="text-xs text-destructive text-center">{resetForm.formState.errors.otp.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">New password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    type="password"
                    placeholder="Enter new password"
                    className="input-premium pl-10"
                    {...resetForm.register("new_password")}
                  />
                </div>
                {resetForm.formState.errors.new_password && (
                  <p className="text-xs text-destructive">{resetForm.formState.errors.new_password.message}</p>
                )}
                <PasswordStrength password={newPasswordVal} />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">Confirm new password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    type="password"
                    placeholder="Repeat new password"
                    className="input-premium pl-10"
                    {...resetForm.register("confirm_password")}
                  />
                </div>
                {resetForm.formState.errors.confirm_password && (
                  <p className="text-xs text-destructive">{resetForm.formState.errors.confirm_password.message}</p>
                )}
              </div>

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={isResettingPassword}
                className="btn-primary w-full py-3 text-sm font-semibold rounded-xl"
              >
                {isResettingPassword ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Resetting password…
                  </>
                ) : (
                  "Reset password"
                )}
              </motion.button>

              <button
                type="button"
                onClick={() => setStep("email")}
                className="w-full text-xs text-muted-foreground hover:text-foreground transition-colors pt-1"
              >
                ← Change email address
              </button>
            </motion.form>
          )}
        </AnimatePresence>

        <p className="text-center text-sm text-muted-foreground pt-2 border-t border-border/40">
          <Link href="/login" className="font-semibold text-primary hover:underline">
            ← Back to sign in
          </Link>
        </p>
      </div>
    </AuthCard>
  );
}

