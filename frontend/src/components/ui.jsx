export function Button({ children, loading, className = "", ...props }) {
  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      className={`w-full rounded-lg bg-signal text-[#06110d] font-medium py-2.5 text-sm
        transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed
        ${className}`}
    >
      {loading ? "Please wait…" : children}
    </button>
  );
}

export function ErrorList({ errors }) {
  if (!errors || errors.length === 0) return null;
  return (
    <div className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2.5 space-y-1">
      {errors.map((err, i) => (
        <p key={i} className="text-xs text-danger">
          {err}
        </p>
      ))}
    </div>
  );
}
