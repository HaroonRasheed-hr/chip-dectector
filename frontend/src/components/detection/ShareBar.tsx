"use client";

import { Facebook, Twitter, Link2 } from "lucide-react";
import { useState } from "react";

export default function ShareBar() {
  const [copied, setCopied] = useState(false);

  async function handleCopyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard API not available
    }
  }

  return (
    <div className="flex items-center justify-center gap-4 mt-4" role="toolbar" aria-label="Share options">
      <a
        href="https://www.facebook.com/sharer/sharer.php"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Share on Facebook"
        className="text-gray-400 hover:text-[#079FF2] transition-colors duration-150"
      >
        <Facebook size={18} />
      </a>
      <a
        href="https://twitter.com/intent/tweet"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Share on Twitter"
        className="text-gray-400 hover:text-[#079FF2] transition-colors duration-150"
      >
        <Twitter size={18} />
      </a>
      <button
        onClick={handleCopyLink}
        aria-label={copied ? "Link copied!" : "Copy link"}
        title={copied ? "Copied!" : "Copy link"}
        className="text-gray-400 hover:text-[#079FF2] transition-colors duration-150"
      >
        <Link2 size={18} />
      </button>
    </div>
  );
}
