import type { Metadata } from "next";
import DetectionClient from "./DetectionClient";

export const metadata: Metadata = {
  title: "Chip Detection – Chip Detector",
  description: "Run AI-powered DETR object detection on your images",
};

export default function DetectionPage() {
  return <DetectionClient />;
}
