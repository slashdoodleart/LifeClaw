import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      className={cn(
        "flex h-10 w-full rounded-lg border border-lc-muted/30 bg-lc-surface px-3 py-2 text-sm text-lc-text placeholder:text-lc-muted focus:outline-none focus:ring-2 focus:ring-lc-primary/50 focus:border-lc-primary transition-all",
        className
      )}
      ref={ref}
      {...props}
    />
  )
);
Input.displayName = "Input";

export { Input };
