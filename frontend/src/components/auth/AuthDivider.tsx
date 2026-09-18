"use client";

export function AuthDivider({ text = "or" }: { text?: string }) {
  return (
    <div className="relative flex items-center justify-center my-5">
      <div className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-border/80" />
      </div>
      <div className="relative bg-card px-3 text-xs uppercase font-medium text-muted-foreground tracking-wider">
        {text}
      </div>
    </div>
  );
}
