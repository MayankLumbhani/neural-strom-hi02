import { LoaderCircle } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const buttonStyles = cva(
  "inline-flex min-h-touch items-center justify-center gap-2 rounded-sm px-4 py-2 text-body font-semibold transition-colors duration-fast ease-civic disabled:pointer-events-none disabled:opacity-60",
  {
    variants: {
      variant: {
        primary: "bg-primary text-on-primary hover:bg-primary-hover",
        secondary:
          "border border-strong bg-surface text-ink hover:bg-surface-muted",
        ghost: "bg-transparent text-ink hover:bg-surface-muted",
        danger: "bg-danger text-surface hover:bg-danger-hover",
      },
    },
    defaultVariants: {
      variant: "primary",
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonStyles> {
  loading?: boolean;
}

export function Button({
  className,
  variant,
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(buttonStyles({ variant }), className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? (
        <LoaderCircle aria-hidden="true" className="icon animate-spin" />
      ) : null}
      {children}
    </button>
  );
}
