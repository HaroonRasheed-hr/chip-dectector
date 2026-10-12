"use client";

import Image from "next/image";

export interface ExampleImage {
  id: number;
  src: string;
  alt: string;
}

const EXAMPLES: ExampleImage[] = [
  { id: 1, src: "/images/example-1.png", alt: "Example 1" },
  { id: 2, src: "/images/example-2.png", alt: "Example 2" },
  { id: 3, src: "/images/example-3.png", alt: "Example 3" },
  { id: 4, src: "/images/example-4.png", alt: "Example 4" },
];

interface ExampleImagesProps {
  selectedId: number | null;
  onSelect: (example: ExampleImage) => void;
}

export default function ExampleImages({ selectedId, onSelect }: ExampleImagesProps) {
  return (
    <section aria-labelledby="examples-label">
      <p
        id="examples-label"
        className="mb-3"
        style={{ fontFamily: "Poppins", fontWeight: 400, fontSize: "16px", color: "var(--theme-text)" }}
      >
        Examples:
      </p>
      <div className="flex gap-3 flex-wrap" role="listbox" aria-label="Example images">
        {EXAMPLES.map((example) => (
          <button
            key={example.id}
            role="option"
            aria-selected={selectedId === example.id}
            onClick={() => onSelect(example)}
            aria-label={example.alt}
            className={[
              "relative overflow-hidden shrink-0 transition-all duration-200 hover:opacity-90",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-[#079FF2]",
              selectedId === example.id ? "example-selected" : "border-2 border-transparent",
            ].join(" ")}
            /* Figma: 108×108, border-radius 20px */
            style={{ width: "108px", height: "108px", borderRadius: "20px" }}
          >
            <Image
              src={example.src}
              alt={example.alt}
              fill
              className="object-cover"
              sizes="108px"
            />
          </button>
        ))}
      </div>
    </section>
  );
}
