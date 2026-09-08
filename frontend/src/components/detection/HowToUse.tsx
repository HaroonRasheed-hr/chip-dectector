"use client";

import Image from "next/image";
import { Play, Pause, VolumeX, Volume2, Maximize, SkipBack, SkipForward } from "lucide-react";
import { useRef, useState, useEffect } from "react";

const TEXT_STYLE: React.CSSProperties = {
  fontFamily: "Inter",
  fontWeight: 400,
  fontSize: "16px",
  lineHeight: "150%",
  letterSpacing: "0%",
  color: "var(--theme-text-dim)",
};

const BULLET_STYLE: React.CSSProperties = {
  ...TEXT_STYLE,
  display: "flex",
  gap: "8px",
  alignItems: "flex-start",
  width: "519px",
  minHeight: "48px",
};

const CTRL_BTN: React.CSSProperties = {
  background: "none",
  border: "none",
  cursor: "pointer",
  padding: "4px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "white",
  borderRadius: "4px",
  flexShrink: 0,
  lineHeight: 0,
};

const SKIP_SECONDS = 10;

/** Clamps x between 0 and 1 and returns it. */
function clamp01(x: number) {
  return Math.max(0, Math.min(1, x));
}

export default function HowToUse() {
  const videoRef     = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const trackRef     = useRef<HTMLDivElement>(null);
  const dragging     = useRef(false);

  const [playing,  setPlaying]  = useState(false);
  const [muted,    setMuted]    = useState(true);
  const [progress, setProgress] = useState(0); // 0–100

  /* ── Sync state from actual video events ───────────────── */
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;

    const onTimeUpdate = () => {
      if (dragging.current || !v.duration) return;
      setProgress((v.currentTime / v.duration) * 100);
    };
    const onPlay  = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onEnded = () => { setPlaying(false); setProgress(0); };

    v.addEventListener("timeupdate", onTimeUpdate);
    v.addEventListener("play",       onPlay);
    v.addEventListener("pause",      onPause);
    v.addEventListener("ended",      onEnded);

    return () => {
      v.removeEventListener("timeupdate", onTimeUpdate);
      v.removeEventListener("play",       onPlay);
      v.removeEventListener("pause",      onPause);
      v.removeEventListener("ended",      onEnded);
    };
  }, []);

  /* ── Seek to a fraction 0-1 of the video duration ──────── */
  function seekToFraction(fraction: number) {
    const v = videoRef.current;
    if (!v || !v.duration) return;
    const t = clamp01(fraction) * v.duration;
    v.currentTime = t;
    setProgress(clamp01(fraction) * 100);
  }

  /* ── Calculate fraction from a pointer clientX on the track */
  function fractionAt(clientX: number): number {
    const rect = trackRef.current!.getBoundingClientRect();
    return clamp01((clientX - rect.left) / rect.width);
  }

  /* ── Progress-bar pointer handlers ─────────────────────── */
  function onTrackPointerDown(e: React.PointerEvent<HTMLDivElement>) {
    e.currentTarget.setPointerCapture(e.pointerId); // keep events during drag
    dragging.current = true;
    seekToFraction(fractionAt(e.clientX));
  }

  function onTrackPointerMove(e: React.PointerEvent<HTMLDivElement>) {
    if (!dragging.current) return;
    seekToFraction(fractionAt(e.clientX));
  }

  function onTrackPointerUp(e: React.PointerEvent<HTMLDivElement>) {
    if (!dragging.current) return;
    seekToFraction(fractionAt(e.clientX));
    dragging.current = false;
    e.currentTarget.releasePointerCapture(e.pointerId);
  }

  /* ── Playback controls ──────────────────────────────────── */
  function startVideo() {
    const v = videoRef.current;
    if (!v) return;
    v.muted = true;
    v.play().catch(() => {});
  }

  function togglePlayPause() {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) { v.play().catch(() => {}); } else { v.pause(); }
  }

  function toggleMute() {
    const v = videoRef.current;
    if (!v) return;
    v.muted = !v.muted;
    setMuted(v.muted);
  }

  function toggleFullscreen() {
    const el = containerRef.current;
    if (!el) return;
    if (!document.fullscreenElement) el.requestFullscreen();
    else                             document.exitFullscreen();
  }

  function skipBy(delta: number) {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = Math.max(0, Math.min(v.duration || 0, v.currentTime + delta));
  }

  /* ─── Render ──────────────────────────────────────────── */
  return (
    <div className="w-full h-full flex">

      {/* ── Left: text + Watch Demo ── */}
      <div
        style={{
          width: "519px",
          height: "311px",
          marginTop: "45px",
          marginLeft: "75px",
          borderRadius: "10px",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
        }}
        aria-labelledby="how-to-use-heading"
      >
        <h2
          id="how-to-use-heading"
          style={{
            fontFamily: "Inter",
            fontWeight: 600,
            fontSize: "18px",
            lineHeight: "150%",
            color: "var(--theme-text)",
            marginBottom: "4px",
          }}
        >
          How to Use ?
        </h2>

        <p style={{ ...TEXT_STYLE, width: "519px", height: "48px" }}>
          Lorem ipsum dolor sit amet consectetur. Proin congue aliquam
          hendrerit mattis. Ac nulla tincidunt urna mattis urna.
        </p>

        <ul style={{ display: "flex", flexDirection: "column", gap: "4px", marginTop: "8px" }}>
          <li style={{ ...TEXT_STYLE, display: "flex", gap: "8px", alignItems: "flex-start" }}>
            <span>•</span>
            <span>Select a model.</span>
          </li>
          <li style={BULLET_STYLE}>
            <span style={{ lineHeight: "150%", flexShrink: 0 }}>•</span>
            <span>
              Select an example by clicking a thumbnail below or Upload an image
              by clicking on the canvas
            </span>
          </li>
          <li style={BULLET_STYLE}>
            <span style={{ lineHeight: "150%", flexShrink: 0 }}>•</span>
            <span>
              Then, click &quot;Infer&quot; button to predict object instances.
              It will take about 10 seconds (on cpu)
            </span>
          </li>
        </ul>

        <div style={{ marginTop: "auto" }}>
          <button
            type="button"
            className="btn-gradient"
            onClick={startVideo}
            style={{
              width: "198px",
              height: "48px",
              borderRadius: "10px",
              paddingTop: "12px",
              paddingBottom: "12px",
              paddingLeft: "46px",
              paddingRight: "46px",
              fontFamily: "Inter",
              fontWeight: 600,
              fontSize: "16px",
              lineHeight: "100%",
              letterSpacing: "0%",
              color: "rgba(255,255,255,1)",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              whiteSpace: "nowrap",
            }}
          >
            Watch Demo
          </button>
        </div>
      </div>

      {/* ── Right: video player ── */}
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "35px 45px 35px 40px",
        }}
      >
        <div
          ref={containerRef}
          style={{
            width: "100%",
            height: "100%",
            borderRadius: "12px",
            border: "1px solid var(--theme-card-border)",
            position: "relative",
            overflow: "hidden",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {/* Thumbnail */}
          {!playing && (
            <Image
              alt="Demo video thumbnail"
              fetchPriority="high"
              decoding="async"
              fill
              className="object-cover"
              src="/images/video-thumnail.png"
              style={{ position: "absolute", height: "100%", width: "100%", inset: 0, color: "transparent" }}
            />
          )}

          {/* Video */}
          <video
            ref={videoRef}
            src="/images/Login-xis.mp4"
            muted
            playsInline
            style={{
              position: "absolute",
              inset: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              opacity: playing ? 1 : 0,
            }}
          />

          {/* Centre play button — before first play */}
          {!playing && (
            <div
              onClick={startVideo}
              style={{
                width: "80px",
                height: "80px",
                borderRadius: "50%",
                background: "rgba(102,187,242,0.75)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                zIndex: 1,
                position: "relative",
              }}
            >
              <Play size={28} fill="white" color="white" style={{ marginLeft: "4px" }} />
            </div>
          )}

          {/* Controls bar */}
          {playing && (
            <div
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                background: "linear-gradient(transparent, rgba(0,0,0,0.72))",
                padding: "0 10px 6px",
                zIndex: 10,
                display: "flex",
                flexDirection: "column",
                gap: "2px",
              }}
            >
              {/*
                Custom progress track.
                - The track div is the ONLY pointer target.
                - setPointerCapture routes pointermove/up here even when the
                  cursor leaves the bar while dragging.
                - fractionAt() uses getBoundingClientRect so the seek position
                  matches exactly where the user clicked, not a range thumb.
              */}
              <div
                ref={trackRef}
                onPointerDown={onTrackPointerDown}
                onPointerMove={onTrackPointerMove}
                onPointerUp={onTrackPointerUp}
                style={{
                  width: "100%",
                  height: "18px",        /* tall hit-area */
                  display: "flex",
                  alignItems: "center",
                  cursor: "pointer",
                  position: "relative",
                  margin: "4px 0 2px",
                  touchAction: "none",   /* prevent scroll-interference on touch */
                }}
              >
                {/* Rail */}
                <div style={{
                  position: "absolute",
                  left: 0, right: 0,
                  height: "4px",
                  borderRadius: "2px",
                  background: "rgba(255,255,255,0.25)",
                  pointerEvents: "none",
                }} />
                {/* Fill */}
                <div style={{
                  position: "absolute",
                  left: 0,
                  width: `${progress}%`,
                  height: "4px",
                  borderRadius: "2px",
                  background: "rgba(102,187,242,1)",
                  pointerEvents: "none",
                }} />
                {/* Thumb */}
                <div style={{
                  position: "absolute",
                  left: `${progress}%`,
                  transform: "translateX(-50%)",
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  background: "rgba(102,187,242,1)",
                  boxShadow: "0 0 0 2px rgba(255,255,255,0.4)",
                  pointerEvents: "none",
                }} />
              </div>

              {/* Button row */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "2px" }}>
                  <button type="button" style={CTRL_BTN} onClick={togglePlayPause} title="Play / Pause">
                    {playing
                      ? <Pause size={20} fill="white" color="white" />
                      : <Play  size={20} fill="white" color="white" />}
                  </button>
                  <button type="button" style={CTRL_BTN} onClick={() => skipBy(-SKIP_SECONDS)} title={`Back ${SKIP_SECONDS}s`}>
                    <SkipBack size={20} color="white" />
                  </button>
                  <button type="button" style={CTRL_BTN} onClick={() => skipBy(SKIP_SECONDS)} title={`Forward ${SKIP_SECONDS}s`}>
                    <SkipForward size={20} color="white" />
                  </button>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "2px" }}>
                  <button type="button" style={CTRL_BTN} onClick={toggleMute} title={muted ? "Unmute" : "Mute"}>
                    {muted ? <VolumeX size={20} color="white" /> : <Volume2 size={20} color="white" />}
                  </button>
                  <button type="button" style={CTRL_BTN} onClick={toggleFullscreen} title="Fullscreen">
                    <Maximize size={20} color="white" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
