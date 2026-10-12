"use client";
import { useEffect, useState } from "react";

const DESIGN_W = 1440;
const DESIGN_H = 988;

export default function LoginScaleWrapper({ children }: { children: React.ReactNode }) {
  const [transform, setTransform] = useState({ scale: 1, ml: 0 });

  useEffect(() => {
    function compute() {
      const s = Math.min(window.innerWidth / DESIGN_W, window.innerHeight / DESIGN_H);
      const ml = Math.max(0, (window.innerWidth - DESIGN_W * s) / 2);
      setTransform({ scale: s, ml });
    }
    compute();
    window.addEventListener("resize", compute);
    return () => window.removeEventListener("resize", compute);
  }, []);

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        background: "linear-gradient(180deg, #0D2033 0%, #06111D 100%)",
      }}
    >
      <div
        style={{
          width: `${DESIGN_W}px`,
          height: `${DESIGN_H}px`,
          position: "relative",
          transform: `scale(${transform.scale})`,
          transformOrigin: "top left",
          marginLeft: `${transform.ml}px`,
        }}
      >
        {children}
      </div>
    </div>
  );
}
