"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Input from "@/components/ui/Input";

// Default to the same origin the page was served from, so the app works on
// http://localhost:8000 and http://127.0.0.1:8000 alike (Django serves both
// the static frontend and the API). Override with NEXT_PUBLIC_API_URL only
// when the backend runs on a different host.
const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/+$/, "");

interface FormState {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

function validate(values: FormState): FormErrors {
  const errors: FormErrors = {};
  if (!values.name) {
    errors.name = "Name is required";
  } else if (values.name.trim().length < 2) {
    errors.name = "Name must be at least 2 characters";
  }
  if (!values.email) {
    errors.email = "Email is required";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
    errors.email = "Enter a valid email address";
  }
  if (!values.password) {
    errors.password = "Password is required";
  } else if (values.password.length < 6) {
    errors.password = "Password must be at least 6 characters";
  }
  if (!values.confirmPassword) {
    errors.confirmPassword = "Please confirm your password";
  } else if (values.confirmPassword !== values.password) {
    errors.confirmPassword = "Passwords do not match";
  }
  return errors;
}

export default function SignupForm() {
  const [form, setForm] = useState<FormState>({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [emailExists, setEmailExists] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const router = useRouter();

  function handleChange(field: keyof FormState) {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
      if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
      // Clear email-exists banner as soon as the user edits the email field
      if (field === "email" && emailExists) setEmailExists(false);
      if (apiError) setApiError(null);
    };
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const validationErrors = validate(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsLoading(true);
    setEmailExists(false);
    setApiError(null);

    try {
      const res = await fetch(`${API_BASE}/api/auth/register/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: form.email,
          full_name: form.name,
          password: form.password,
          confirm_password: form.confirmPassword,
        }),
      });

      if (res.ok) {
        setSuccess(true);
        setTimeout(() => router.push("/login"), 2500);
        return;
      }

      // Parse error body — keep this in its own try/catch so a JSON
      // parse failure (e.g. CORS-blocked body) is handled separately
      let data: Record<string, unknown> = {};
      try {
        data = await res.json();
      } catch {
        setApiError("Something went wrong. Please try again.");
        return;
      }

      // DRF returns field errors as {"email": ["msg", ...]}
      // Use `in` so we catch the key even if the value is an empty array
      if ("email" in data) {
        setEmailExists(true);
      } else if (typeof data.detail === "string") {
        setApiError(data.detail);
      } else {
        // Collect first field error from any key
        const firstVal = Object.values(data)[0];
        const msg = Array.isArray(firstVal) ? firstVal[0] : firstVal;
        setApiError(
          typeof msg === "string" ? msg : "Something went wrong. Please try again."
        );
      }
    } catch {
      setApiError("Cannot connect to server. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      aria-label="Sign up form"
      className="flex flex-col gap-3"
    >
      <Input
        id="name"
        type="text"
        label="Name"
        placeholder="Your full name"
        autoComplete="name"
        value={form.name}
        onChange={handleChange("name")}
        error={errors.name}
      />

      <Input
        id="email"
        type="email"
        label="Email"
        placeholder="username@gmail.com"
        autoComplete="email"
        value={form.email}
        onChange={handleChange("email")}
        error={errors.email}
      />

      <Input
        id="password"
        type="password"
        label="Password"
        placeholder="Password"
        autoComplete="new-password"
        value={form.password}
        onChange={handleChange("password")}
        error={errors.password}
      />

      <Input
        id="confirmPassword"
        type="password"
        label="Confirm Password"
        placeholder="Confirm your password"
        autoComplete="new-password"
        value={form.confirmPassword}
        onChange={handleChange("confirmPassword")}
        error={errors.confirmPassword}
      />

      {/* ── Email already exists ── */}
      {emailExists && (
        <div
          role="alert"
          aria-live="assertive"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
            padding: "12px 16px",
            borderRadius: "10px",
            background: "rgba(251, 191, 36, 0.12)",
            border: "1px solid rgba(251, 191, 36, 0.5)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
              <circle cx="10" cy="10" r="9" stroke="#fbbf24" strokeWidth="1.8" />
              <path d="M10 6v5" stroke="#fbbf24" strokeWidth="1.8" strokeLinecap="round" />
              <circle cx="10" cy="14" r="1" fill="#fbbf24" />
            </svg>
            <p style={{ fontFamily: "Poppins", fontSize: "13px", color: "#fbbf24", margin: 0 }}>
              Email already exist! please login.
            </p>
          </div>
          <Link
            href="/login"
            style={{
              flexShrink: 0,
              fontFamily: "Poppins",
              fontWeight: 600,
              fontSize: "13px",
              color: "#ffffff",
              background: "rgba(251, 191, 36, 0.25)",
              border: "1px solid rgba(251, 191, 36, 0.6)",
              borderRadius: "6px",
              padding: "4px 12px",
              textDecoration: "none",
              whiteSpace: "nowrap",
            }}
          >
            Login instead
          </Link>
        </div>
      )}

      {/* ── Generic API error ── */}
      {apiError && (
        <div
          role="alert"
          aria-live="assertive"
          style={{
            padding: "10px 14px",
            borderRadius: "10px",
            background: "rgba(239, 68, 68, 0.12)",
            border: "1px solid rgba(239, 68, 68, 0.45)",
          }}
        >
          <p style={{ fontFamily: "Poppins", fontSize: "13px", color: "#f87171", margin: 0 }}>
            {apiError}
          </p>
        </div>
      )}

      {/* ── Success ── */}
      {success && (
        <div
          role="status"
          aria-live="polite"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "12px 16px",
            borderRadius: "10px",
            background: "rgba(34, 197, 94, 0.15)",
            border: "1px solid rgba(34, 197, 94, 0.5)",
          }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
            <circle cx="10" cy="10" r="10" fill="rgba(34,197,94,0.3)" />
            <path
              d="M6 10.5l2.5 2.5L14 8"
              stroke="#22c55e"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <div>
            <p style={{ fontFamily: "Poppins", fontWeight: 600, fontSize: "14px", color: "#22c55e", margin: 0 }}>
              Signup successful!
            </p>
            <p style={{ fontFamily: "Poppins", fontSize: "12px", color: "rgba(255,255,255,0.65)", margin: 0 }}>
              Redirecting to login…
            </p>
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading || success}
        aria-label="Create account"
        className="disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 hover:brightness-90"
        style={{
          width: "100%",
          height: "50px",
          borderRadius: "10px",
          background: "rgba(87, 200, 231, 1)",
          fontFamily: "Poppins",
          fontWeight: 600,
          fontSize: "16px",
          color: "#ffffff",
          border: "none",
          cursor: "pointer",
        }}
      >
        {isLoading ? "Creating account…" : "Create account"}
      </button>

      <p
        className="text-center text-sm text-gray-300"
        style={{ fontFamily: "Poppins" }}
      >
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-semibold text-white hover:text-[#57C8E7] transition-colors duration-150"
        >
          Sign in
        </Link>
      </p>
    </form>
  );
}
