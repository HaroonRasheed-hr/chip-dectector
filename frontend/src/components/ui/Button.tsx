"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "infer";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  fullWidth?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-[#079FF2] hover:bg-[#078BD7] text-white font-semibold",
  secondary:
    "bg-transparent border border-[#086CAF] text-white hover:border-[#079FF2] hover:text-[#079FF2]",
  ghost:
    "bg-transparent text-[#079FF2] hover:bg-[#079FF2]/10",
  infer:
    "btn-infer text-white font-semibold shadow-lg shadow-blue-800/20",
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
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-[#079FF2]",
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
