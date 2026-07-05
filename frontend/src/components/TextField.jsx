export default function TextField({ label, error, className = "", ...props }) {
  return (
    <label className={`block ${className}`}>
      <span className="text-sm text-ink-muted">{label}</span>
      <input
        {...props}
        className={`mt-1.5 w-full rounded-lg bg-surface-raised border px-3 py-2.5 text-ink text-sm
          placeholder:text-ink-muted/60 outline-none transition-colors
          ${error ? "border-danger" : "border-border focus:border-signal"}`}
      />
      {error && <span className="text-xs text-danger mt-1 block">{error}</span>}
    </label>
  );
}
