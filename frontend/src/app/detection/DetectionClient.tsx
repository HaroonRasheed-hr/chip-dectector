"use client";

import { useState, useRef } from "react";
import Navbar from "@/components/layout/Navbar";
import HowToUse from "@/components/detection/HowToUse";
import ModelSelector, { ModelName } from "@/components/detection/ModelSelector";
import ImagePanel from "@/components/detection/ImagePanel";
import ExampleImages, { ExampleImage } from "@/components/detection/ExampleImages";

// Default to the same origin the page was served from, so the app works on
// http://localhost:8000 and http://127.0.0.1:8000 alike (Django serves both
// the static frontend and the API). Override with NEXT_PUBLIC_API_URL only
// when the backend runs on a different host.
const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/+$/, "");

const CENTERED_1164: React.CSSProperties = {
  width: "1164px",
  marginLeft: "auto",
  marginRight: "auto",
};

export default function DetectionClient() {
  const [selectedModel, setSelectedModel] = useState<ModelName>("detr-resnet-50");
  const [inputImage, setInputImage] = useState<string | null>(null);
  const [outputImage, setOutputImage] = useState<string | null>(null);
  const [selectedExample, setSelectedExample] = useState<number | null>(null);
  const [isInferring, setIsInferring] = useState(false);
  const [inferError, setInferError] = useState<string | null>(null);
  const blobUrlRef = useRef<string | null>(null);
  const uploadedFileRef = useRef<File | null>(null);
  const exampleSrcRef = useRef<string | null>(null);

  function handleImageUpload(file: File) {
    if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current);
    const url = URL.createObjectURL(file);
    blobUrlRef.current = url;
    uploadedFileRef.current = file;
    exampleSrcRef.current = null;
    setInputImage(url);
    setOutputImage(null);
    setSelectedExample(null);
    setInferError(null);
  }

  function handleExampleSelect(example: ExampleImage) {
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }
    uploadedFileRef.current = null;
    exampleSrcRef.current = example.src;
    setSelectedExample(example.id);
    setInputImage(example.src);
    setOutputImage(null);
    setInferError(null);
  }

  async function handleInfer() {
    if (!inputImage) return;
    setIsInferring(true);
    setOutputImage(null);
    setInferError(null);
    try {
      let imageBlob: Blob | null = uploadedFileRef.current;
      let filename = uploadedFileRef.current?.name ?? "input.png";

      if (!imageBlob && exampleSrcRef.current) {
        const res = await fetch(exampleSrcRef.current);
        if (!res.ok) throw new Error(`failed to load example image (${res.status})`);
        imageBlob = await res.blob();
        filename = exampleSrcRef.current.split("/").pop() ?? "example.png";
      }

      if (!imageBlob) throw new Error("no image available to infer on");

      const form = new FormData();
      form.append("image", imageBlob, filename);
      // selectedModel is a UI-side label only; the backend auto-routes
      // via INFERENCE_DEFAULT_PROVIDER (tensorrt → onnx_cpu → stub).

      const res = await fetch(`${API_BASE}/api/inference/infer/`, {
        method: "POST",
        body: form,
        credentials: "include",
      });

      if (!res.ok) {
        const detail = await res.text().catch(() => "");
        throw new Error(`inference HTTP ${res.status}: ${detail.slice(0, 200)}`);
      }

      const data: { output_image: string | null } = await res.json();
      setOutputImage(data.output_image ?? inputImage);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "inference request failed";
      setInferError(msg);
    } finally {
      setIsInferring(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 w-full flex flex-col" role="main">
        <div
          style={{
            ...CENTERED_1164,
            height: "400px",
            marginTop: "93px",
            borderRadius: "20px",
            border: "2px solid var(--theme-card-border)",
            background: "var(--theme-card-bg)",
            backdropFilter: "blur(16px)",
            WebkitBackdropFilter: "blur(16px)",
            overflow: "hidden",
          }}
        >
          <HowToUse />
        </div>

        <div
          style={{
            ...CENTERED_1164,
            paddingTop: "32px",
            paddingBottom: "32px",
            display: "flex",
            flexDirection: "column",
            gap: "32px",
          }}
        >
          <ModelSelector selected={selectedModel} onChange={setSelectedModel} />

          <section aria-label="Image input and output panels">
            <div className="flex flex-col sm:flex-row gap-4">
              <ImagePanel
                variant="input"
                label="Input Image"
                imageSrc={inputImage}
                onImageChange={handleImageUpload}
              />
              <ImagePanel
                variant="output"
                label="Output Img with predicted Instances"
                imageSrc={outputImage}
              />
            </div>
          </section>

          <button
            disabled={!inputImage || isInferring}
            onClick={handleInfer}
            aria-label="Run inference on the selected image"
            className="disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            style={{
              width: "456px",
              height: "76px",
              borderRadius: "20px",
              paddingTop: "20px",
              paddingRight: "200px",
              paddingBottom: "20px",
              paddingLeft: "200px",
              gap: "10px",
              opacity: 1,
              background: "var(--gradient-brand)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              alignSelf: "center",
            }}
          >
            <span
              style={{
                fontFamily: "Poppins",
                fontWeight: 600,
                fontSize: "24px",
                lineHeight: "100%",
                letterSpacing: "0%",
                verticalAlign: "middle",
                color: "rgba(255, 255, 255, 1)",
                whiteSpace: "nowrap",
              }}
            >
              {isInferring ? "Inferring…" : "Infer"}
            </span>
          </button>

          {inferError && (
            <p
              role="alert"
              style={{
                color: "#e57373",
                fontFamily: "Poppins",
                fontSize: "14px",
                textAlign: "center",
                margin: 0,
              }}
            >
              {inferError}
            </p>
          )}

          <ExampleImages selectedId={selectedExample} onSelect={handleExampleSelect} />
        </div>
      </main>
    </div>
  );
}
