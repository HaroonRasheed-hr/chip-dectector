"use client";

import { useRef, useState, DragEvent, ChangeEvent } from "react";
import Image from "next/image";
import { Icon } from "@iconify/react";

interface ImagePanelProps {
  variant: "input" | "output";
  imageSrc?: string | null;
  label: string;
  onImageChange?: (file: File) => void;
}

export default function ImagePanel({
  variant,
  imageSrc,
  label,
  onImageChange,
}: ImagePanelProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isInput = variant === "input";

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(false);
    if (!isInput) return;
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      onImageChange?.(file);
    }
  }

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onImageChange?.(file);
  }

  function handleClick() {
    if (isInput) fileInputRef.current?.click();
  }

  return (
    <div className="flex-1 min-w-0" style={{ position: "relative", paddingTop: "21px" }}>
      {/* Floating label badge — sits on top of the panel border */}
      <span
        className="text-white"
        style={{
          position: "absolute",
          top: 0,
          left: "27px",
          zIndex: 2,
          width: isInput ? "247.73px" : "352.09px",
          height: "42.43px",
          borderRadius: "20px",
          padding: "10px",
          gap: "10px",
          background: "rgba(62, 95, 170, 1)",
          fontFamily: "Inter",
          fontWeight: 600,
          fontSize: "14px",
          lineHeight: "100%",
          letterSpacing: "0%",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </span>

      {/* Panel body */}
      <div
        role={isInput ? "button" : undefined}
        tabIndex={isInput ? 0 : undefined}
        aria-label={isInput ? "Upload or drop an image" : "Output image area"}
        onClick={handleClick}
        onKeyDown={(e) => {
          if (isInput && (e.key === "Enter" || e.key === " ")) handleClick();
        }}
        onDragOver={(e) => {
          if (isInput) {
            e.preventDefault();
            setIsDragOver(true);
          }
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        className={[
          "relative overflow-hidden transition-all duration-200",
          "flex flex-col items-center justify-center",
          isInput ? "cursor-pointer" : "cursor-default",
          isDragOver ? "brightness-110" : "",
        ].join(" ")}
        style={{
          height: "440px",
          borderRadius: "20px",
          border: "2px solid var(--theme-card-border)",
          background: "var(--theme-card-bg)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
          boxShadow: "5px 10px 25px 0px rgba(0, 0, 0, 0.25)",
        }}
      >
        {imageSrc ? (
          <Image
            src={imageSrc}
            alt={isInput ? "Input image" : "Output image with predictions"}
            fill
            className="object-contain"
          />
        ) : (
          <div className="flex flex-col items-center gap-3 p-6 text-center select-none">
            {isInput ? (
              <>
                <Icon
                  icon="solar:gallery-add-bold-duotone"
                  width={86}
                  height={86}
                  style={{ color: "var(--theme-icon)" }}
                />
                <p className="text-sm" style={{ fontFamily: "Poppins", color: "var(--theme-icon)" }}>
                  Drop Image Here
                </p>
              </>
            ) : (
              <>
                <Icon
                  icon="solar:gallery-check-line-duotone"
                  width={86}
                  height={86}
                  style={{ color: "var(--theme-icon)" }}
                />
                <p className="text-sm" style={{ fontFamily: "Poppins", color: "var(--theme-icon)" }}>
                  No Defect
                </p>
              </>
            )}
          </div>
        )}

        {isInput && (
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
            aria-hidden="true"
          />
        )}
      </div>
    </div>
  );
}
