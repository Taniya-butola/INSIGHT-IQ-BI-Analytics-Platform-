import PulseLine from "./PulseLine";

export default function AuthLayout({ eyebrow, title, subtitle, children }) {
  return (
    <div className="min-h-screen flex bg-base">
      {/* Branded panel — the signature moment */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 bg-surface border-r border-border overflow-hidden">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-md bg-signal/15 border border-signal/30 flex items-center justify-center">
            <span className="text-signal font-display font-semibold">iQ</span>
          </div>
          <span className="font-display font-semibold text-ink text-lg">INSIGHT IQ</span>
        </div>

        <div className="relative">
          <PulseLine className="w-full h-auto opacity-90" />
          <p className="mt-6 font-mono text-xs text-ink-muted tracking-wide">
            LIVE FEED · REVENUE · CHURN RISK · REORDER SIGNALS
          </p>
          <h2 className="mt-4 font-display text-3xl font-semibold text-ink leading-tight max-w-md">
            Every sale tells a story. INSIGHT IQ reads it for you.
          </h2>
          <p className="mt-3 text-ink-muted max-w-sm">
            Upload a spreadsheet, get a boardroom-ready read on revenue, customers,
            and inventory in minutes.
          </p>
        </div>

        <p className="text-xs text-ink-muted font-mono">Retail Sales Analytics · Phase 1</p>
      </div>

      {/* Form panel */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-md bg-signal/15 border border-signal/30 flex items-center justify-center">
              <span className="text-signal font-display font-semibold text-sm">iQ</span>
            </div>
            <span className="font-display font-semibold text-ink">INSIGHT IQ</span>
          </div>

          {eyebrow && (
            <p className="text-signal font-mono text-xs tracking-wide uppercase mb-2">
              {eyebrow}
            </p>
          )}
          <h1 className="font-display text-2xl font-semibold text-ink">{title}</h1>
          {subtitle && <p className="text-ink-muted text-sm mt-2">{subtitle}</p>}

          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
