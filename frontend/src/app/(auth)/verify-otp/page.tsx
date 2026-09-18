"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Loader2, ShieldCheck } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { AuthCard } from "@/components/auth/AuthCard";
import { OTPInput } from "@/components/auth/OTPInput";

function OTPContent() {
  const searchParams = useSearchParams();
  const email = searchParams.get("email") ?? "";
  const { verifyOtp, isVerifying, resendOtp, isResending } = useAuth();
  const [completedCode, setCompletedCode] = useState("");

  const handleComplete = (otp: string) => {
    setCompletedCode(otp);
    if (email) {
      verifyOtp({ email, otp });
    }
  };

  const handleResend = () => {
    if (email) {
      resendOtp(email);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (completedCode.length === 6 && email) {
      verifyOtp({ email, otp: completedCode });
    }
  };

  return (
    <AuthCard
      title="Verify your email"
      subtitle={
        email ? (
          <>
            We sent a 6-digit OTP code to <span className="font-semibold text-foreground">{email}</span>
          </>
        ) : (
          "Enter the 6-digit verification code sent to your email"
        )
      }
      icon={
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20">
          <ShieldCheck className="h-7 w-7 text-primary" />
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        <OTPInput
          length={6}
          onComplete={handleComplete}
          onResend={handleResend}
          isResending={isResending}
        />

        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          type="submit"
          disabled={isVerifying || completedCode.length !== 6}
          className="btn-primary w-full py-3 text-sm font-semibold rounded-xl"
        >
          {isVerifying ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Verifying code…
            </>
          ) : (
            "Verify email & activate account"
          )}
        </motion.button>

        <p className="text-center text-sm text-muted-foreground pt-2">
          <Link href="/login" className="font-semibold text-primary hover:underline">
            ← Back to sign in
          </Link>
        </p>
      </form>
    </AuthCard>
  );
}

export default function VerifyOTPPage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <OTPContent />
    </Suspense>
  );
}

