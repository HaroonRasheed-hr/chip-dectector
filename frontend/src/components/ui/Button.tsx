"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "infer";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  fullWidth?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-[#4dd4f0] hover:bg-[#38c4e0] text-[#0d1117] font-semibold",
  secondary:
    "bg-transparent border border-[#2d3a52] text-white hover:border-[#4dd4f0] hover:text-[#4dd4f0]",
  ghost:
    "bg-transparent text-[#4dd4f0] hover:bg-[#4dd4f0]/10",
  infer:
    "btn-infer text-white font-semibold shadow-lg shadow-cyan-500/20",
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      fullWidth = false,
      className = "",
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={[
          "inline-flex items-center justify-center gap-2",
          "rounded-lg px-5 py-2.5 text-sm",
          "transition-all duration-200 ease-in-out",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-[#4dd4f0]",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          fullWidth ? "w-full" : "",
          variantStyles[variant],
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
