import { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "dark" | "light";
}

export default function Card({
  variant = "dark",
  className = "",
  children,
  ...props
}: CardProps) {
  const base =
    "rounded-2xl border transition-colors duration-200";

  const variants = {
    dark: "bg-[#1a2035] border-[#2d3a52]",
    light: "bg-white border-gray-200 text-gray-800",
  };

  return (
    <div
      className={[base, variants[variant], className].filter(Boolean).join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}
