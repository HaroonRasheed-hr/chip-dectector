"use client";

export type ModelName = "detr-resnet-50" | "detr-resnet-101" | "detr-resnet-dc5-50";

const MODELS: { id: ModelName; label: string }[] = [
  { id: "detr-resnet-50",     label: "detr-resnet-50"     },
  { id: "detr-resnet-101",    label: "detr-resnet-101"    },
  { id: "detr-resnet-dc5-50", label: "detr-resnet-dc5-50" },
];

interface ModelSelectorProps {
  selected: ModelName;
  onChange: (model: ModelName) => void;
}

export default function ModelSelector({ selected, onChange }: ModelSelectorProps) {
  return (
    <section aria-labelledby="model-name-label">
      <p
        id="model-name-label"
        className="mb-3"
        style={{
          width: "150px",
          height: "29px",
          fontFamily: "Inter",
          fontWeight: 600,
          fontSize: "24px",
          lineHeight: "100%",
          letterSpacing: "0%",
          color: "var(--theme-text)",
          display: "flex",
          alignItems: "center",
        }}
      >
        Model name:
      </p>
      <div
        className="flex gap-4"
        role="radiogroup"
        aria-labelledby="model-name-label"
      >
        {MODELS.map(({ id, label }) => {
          const isSelected = selected === id;
          return (
            <button
              key={id}
              role="radio"
              aria-checked={isSelected}
              onClick={() => onChange(id)}
              className="flex-1 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#079FF2]"
              style={{
                height: "72px",
                borderRadius: "14px",
                border: isSelected ? "1px solid #079FF2" : "1px solid var(--theme-model-btn-border)",
                background: isSelected ? "rgba(7, 159, 242, 0.10)" : "var(--theme-model-btn-bg)",
                color: isSelected ? "#079FF2" : "var(--theme-text)",
                fontFamily: "Poppins",
                fontWeight: 500,
                fontSize: "24px",
                lineHeight: "100%",
                letterSpacing: "0%",
              }}
            >
              {label}
            </button>
          );
        })}
      </div>
    </section>
  );
}
