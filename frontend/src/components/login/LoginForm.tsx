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
  email: string;
  password: string;
}

interface FormErrors {
  email?: string;
  password?: string;
}

function validate(values: FormState): FormErrors {
  const errors: FormErrors = {};
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
  return errors;
}

export default function LoginForm() {
  const [form, setForm] = useState<FormState>({ email: "", password: "" });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const router = useRouter();

  function handleChange(field: keyof FormState) {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
      if (errors[field]) {
        setErrors((prev) => ({ ...prev, [field]: undefined }));
      }
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
    setApiError(null);

    try {
      const res = await fetch(`${API_BASE}/api/auth/login/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email: form.email,
          password: form.password,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data?.access) {
          try {
            localStorage.setItem("access_token", data.access);
          } catch {
            // localStorage unavailable (e.g. private mode) — ignore
          }
        }
        router.push("/detection");
        return;
      }

      let data: Record<string, unknown> = {};
      try {
        data = await res.json();
      } catch {
        setApiError("Something went wrong. Please try again.");
        return;
      }

      if (res.status === 401) {
        if (data.code === "user_not_found") {
          setErrors((prev) => ({
            ...prev,
            email: "User does not exist, please sign up first.",
          }));
        } else if (data.code === "invalid_password") {
          setErrors((prev) => ({ ...prev, password: "Incorrect Password" }));
        } else {
          setApiError(
            typeof data.detail === "string"
              ? data.detail
              : "Authentication failed."
          );
        }
        return;
      }

      if (typeof data.detail === "string") {
        setApiError(data.detail);
      } else {
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
      aria-label="Login form"
      className="flex flex-col gap-5"
    >
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

      <div className="flex flex-col gap-1.5">
        <Input
          id="password"
          type="password"
          label="Password"
          placeholder="Password"
          autoComplete="current-password"
          value={form.password}
          onChange={handleChange("password")}
          error={errors.password}
        />
        <div className="flex justify-end">
          <Link
            href="/forgot-password"
            prefetch={false}
            className="text-xs text-gray-300 hover:text-[#079FF2] transition-colors duration-150"
            style={{ fontFamily: "Poppins" }}
          >
            Forgot Password?
          </Link>
        </div>
      </div>

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

      <button
        type="submit"
        disabled={isLoading}
        aria-label="Sign in"
        className="disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 hover:brightness-90"
        style={{
          width: "100%",
          height: "50px",
          borderRadius: "10px",
          background: "#079FF2",
          fontFamily: "Poppins",
          fontWeight: 600,
          fontSize: "16px",
          color: "#ffffff",
          border: "none",
          cursor: "pointer",
        }}
      >
        {isLoading ? "Signing in…" : "Sign in"}
      </button>

      <p
        className="text-center text-sm text-gray-300"
        style={{ fontFamily: "Poppins" }}
      >
        Don&apos;t have an account yet?{" "}
        <Link
          href="/register"
          className="font-semibold text-white hover:text-[#079FF2] transition-colors duration-150"
        >
          Register for free
        </Link>
      </p>
    </form>
  );
}
