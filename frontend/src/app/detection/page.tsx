import type { Metadata } from "next";
import DetectionClient from "./DetectionClient";

export const metadata: Metadata = {
  title: "DETR Object Detection – xis.ai",
  description: "Run AI-powered DETR object detection on your images",
};

export default function DetectionPage() {
  return <DetectionClient />;
}
