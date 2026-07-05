const STEPS = [
  { key: "uploaded", label: "Uploaded" },
  { key: "validated", label: "Validated" },
  { key: "cleaned", label: "Cleaned" },
  { key: "analyzed", label: "Analyzed", upcoming: true },
];

const ORDER = { uploaded: 0, validated: 1, cleaned: 2, analyzed: 3, failed: -1 };

export default function PipelineStepper({ status, compact = false }) {
  const currentIndex = ORDER[status] ?? 0;
  const failed = status === "failed";

  if (compact) {
    const label = failed ? "Failed" : STEPS[currentIndex]?.label ?? "Uploaded";
    const cls = failed
      ? "border-danger/40 text-danger bg-danger/10"
      : "border-signal/40 text-signal bg-signal/10";
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${cls}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${failed ? "bg-danger" : "bg-signal"}`} />
        {label}
      </span>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {STEPS.map((step, i) => {
        const isDone = !failed && i <= currentIndex && !step.upcoming;
        const isCurrent = !failed && i === currentIndex;
        return (
          <div key={step.key} className="flex items-center gap-2">
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono border
                ${
                  failed && step.key === "uploaded"
                    ? "border-danger/40 text-danger bg-danger/10"
                    : isDone
                    ? "border-signal/40 text-signal bg-signal/10"
                    : "border-border text-ink-muted"
                }
                ${isCurrent ? "ring-1 ring-signal/30" : ""}`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isDone ? "bg-signal" : "bg-ink-muted/40"
                }`}
              />
              {step.label}
            </div>
            {i < STEPS.length - 1 && <span className="text-ink-muted/40 text-xs">→</span>}
          </div>
        );
      })}
    </div>
  );
}
