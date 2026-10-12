import type { Metadata } from "next";
import Image from "next/image";
import SignupForm from "@/components/signup/SignupForm";

export const metadata: Metadata = {
  title: "Register – Chip Detector",
  description: "Create your Chip Detector account",
};

export default function RegisterPage() {
  return (
    <main
      style={{
        display: "flex",
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        background: "linear-gradient(180deg, #0D2033 0%, #06111D 100%)",
      }}
    >
      {/* ── Left panel: branding + illustration ── */}
      <div
        style={{
          flex: "1 1 0",
          position: "relative",
          display: "flex",
          flexDirection: "column",
          padding: "48px 0 0 56px",
          overflow: "hidden",
        }}
      >
        <div style={{ width: "64px", height: "52px", position: "relative", flexShrink: 0 }}>
          <Image
            src="/images/chip-detector-logo.svg"
            alt="Chip Detector logo"
            fill
            style={{ objectFit: "contain", objectPosition: "left center" }}
            priority
          />
        </div>

        <p
          style={{
            marginTop: "18px",
            fontSize: "20px",
            lineHeight: "100%",
            color: "rgba(255, 255, 255, 1)",
            whiteSpace: "nowrap",
            flexShrink: 0,
          }}
        >
          <span style={{ fontFamily: "Poppins", fontWeight: 600 }}>Precision Beyond </span>
          <span style={{ fontFamily: "Poppins", fontWeight: 400 }}>Perception</span>
        </p>

        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            top: "140px",
          }}
        >
          <Image
            src="/images/login-illustration.png"
            alt="3D isometric analytics illustration"
            fill
            style={{ objectFit: "contain", objectPosition: "center bottom" }}
            priority
          />
        </div>
      </div>

      {/* ── Right panel: signup card ── */}
      <div
        style={{
          flex: "0 0 52%",
          height: "100%",
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "24px 56px 24px 32px",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: "580px",
            borderRadius: "20px",
            border: "2px solid rgba(255, 255, 255, 0.28)",
            background: "rgba(255, 255, 255, 0.12)",
            backdropFilter: "blur(18px)",
            WebkitBackdropFilter: "blur(18px)",
            boxShadow: "0px 4px 24px 0px rgba(0, 0, 0, 0.4)",
            padding: "36px 60px",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
          }}
        >
          <h1
            style={{
              fontFamily: "Inter, sans-serif",
              fontWeight: 700,
              fontSize: "36px",
              lineHeight: "100%",
              color: "rgba(255, 255, 255, 1)",
              margin: 0,
            }}
          >
            Create Account
          </h1>

          <SignupForm />
        </div>
      </div>
    </main>
  );
}
