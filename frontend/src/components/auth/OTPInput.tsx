"use client";

import { useEffect, useState, useRef } from "react";
import { RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

interface OTPInputProps {
  length?: number;
  onComplete: (otp: string) => void;
  onResend?: () => void;
  isResending?: boolean;
}

export function OTPInput({ length = 6, onComplete, onResend, isResending = false }: OTPInputProps) {
  const [digits, setDigits] = useState<string[]>(Array(length).fill(""));
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (countdown <= 0) {
      setCanResend(true);
      return;
    }
    const timer = setInterval(() => setCountdown((c) => c - 1), 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  const handleChange = (index: number, val: string) => {
    const cleanVal = val.replace(/\D/g, "");
    if (!cleanVal && val !== "") return;
    const newDigits = [...digits];
    newDigits[index] = cleanVal.slice(-1);
    setDigits(newDigits);

    const fullCode = newDigits.join("");
    if (fullCode.length === length && !newDigits.includes("")) {
      onComplete(fullCode);
    } else if (cleanVal && index < length - 1) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, length);
    if (!pasted) return;
    const newDigits = Array(length).fill("");
    for (let i = 0; i < pasted.length; i++) {
      newDigits[i] = pasted[i];
    }
    setDigits(newDigits);
    if (pasted.length === length) {
      onComplete(pasted);
      inputsRef.current[length - 1]?.focus();
    } else {
      inputsRef.current[pasted.length]?.focus();
    }
  };

  const handleResendClick = () => {
    if (onResend) {
      onResend();
      setCountdown(60);
      setCanResend(false);
      setDigits(Array(length).fill(""));
      inputsRef.current[0]?.focus();
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex gap-2.5 justify-center" onPaste={handlePaste}>
        {digits.map((digit, i) => (
          <input
            key={i}
            ref={(el) => { inputsRef.current[i] = el; }}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            className={cn(
              "h-14 w-12 rounded-xl border border-border bg-secondary/40 text-center text-xl font-bold text-foreground transition-all duration-150 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30 shadow-inner",
              digit ? "border-primary/60 bg-primary/5" : ""
            )}
            autoFocus={i === 0}
          />
        ))}
      </div>

      {onResend && (
        <div className="text-center text-sm">
          {canResend ? (
            <button
              type="button"
              onClick={handleResendClick}
              disabled={isResending}
              className="inline-flex items-center gap-1.5 font-medium text-primary hover:underline disabled:opacity-50"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              {isResending ? "Sending code..." : "Resend OTP code"}
            </button>
          ) : (
            <span className="text-muted-foreground font-medium">
              Resend OTP in <span className="text-foreground font-bold tabular-nums">{countdown}s</span>
            </span>
          )}
        </div>
      )}
    </div>
  );
}
