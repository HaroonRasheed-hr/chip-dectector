"use client";

import Link from "next/link";
import Image from "next/image";
import { Users } from "lucide-react";
import { Icon } from "@iconify/react";
import { useTheme } from "@/context/ThemeContext";

const NAV_LINK_STYLE: React.CSSProperties = {
  fontFamily: "Poppins",
  fontWeight: 400,
  fontSize: "16px",
  lineHeight: "150%",
  letterSpacing: "0%",
  color: "var(--theme-text)",
  display: "flex",
  alignItems: "center",
  gap: "6px",
  height: "24px",
};

export default function Navbar() {
  const { theme, toggle } = useTheme();

  return (
    <header
      className="w-full px-6"
      style={{
        height: "100px",
        background: "var(--theme-navbar-bg)",
        boxShadow: "var(--theme-navbar-shadow)",
      }}
      role="banner"
    >
      <div className="max-w-[1440px] mx-auto h-full flex items-center justify-between">
        <Link href="/detection" className="flex items-center" aria-label="Chip Detector home">
          <Image
            src="/images/chip-detector-logo.svg"
            alt="Chip Detector logo"
            width={56}
            height={45}
            priority
            style={{ objectFit: "contain" }}
          />
        </Link>

        <nav className="flex items-center gap-8" aria-label="Main navigation">
          <Link href="/detection" style={NAV_LINK_STYLE}>
            <Icon icon="tdesign:app" width={24} height={24} />
            <span style={{ width: "33px" }}>App</span>
          </Link>

          <Link href="/files" style={NAV_LINK_STYLE} prefetch={false}>
            <Icon icon="ph:files" width={24} height={24} />
            <span style={{ width: "35px" }}>Files</span>
          </Link>

          {/* Theme toggle */}
          <button
            type="button"
            onClick={toggle}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            className="flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95"
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "12px",
              background: "var(--theme-toggle-bg)",
              border: "1px solid var(--theme-toggle-border)",
              color: "var(--theme-toggle-color)",
              cursor: "pointer",
              fontSize: "20px",
              flexShrink: 0,
            }}
          >
            {theme === "dark" ? "🌙" : "☀️"}
          </button>

          <Link
            href="/community"
            prefetch={false}
            aria-label="Community"
            className="btn-gradient flex items-center justify-center gap-[10px] text-white transition-all duration-200"
            style={{
              width: "172px",
              height: "44px",
              borderRadius: "10px",
              paddingTop: "10px",
              paddingBottom: "10px",
              paddingLeft: "20px",
              paddingRight: "20px",
              fontFamily: "Poppins",
              fontSize: "16px",
              fontWeight: 400,
            }}
          >
            <Users size={16} />
            <span>Community</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
