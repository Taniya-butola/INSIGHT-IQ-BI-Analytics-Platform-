/**
 * The signature visual element of INSIGHT IQ: an ambient "signal line" —
 * part stock ticker, part vital sign — representing a retail business's
 * live sales pulse. Used once, on the branded half of the auth screens.
 */
export default function PulseLine({ className = "" }) {
  return (
    <svg
      viewBox="0 0 480 220"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="pulseFade" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#2DD4A7" stopOpacity="0" />
          <stop offset="15%" stopColor="#2DD4A7" stopOpacity="0.9" />
          <stop offset="85%" stopColor="#2DD4A7" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#2DD4A7" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* faint grid, evokes a trading/analytics terminal */}
      {Array.from({ length: 6 }).map((_, i) => (
        <line
          key={`h-${i}`}
          x1="0"
          y1={20 + i * 36}
          x2="480"
          y2={20 + i * 36}
          stroke="#FFFFFF"
          strokeOpacity="0.04"
        />
      ))}

      <path
        d="M0,150 L40,150 L60,90 L80,180 L100,60 L120,150 L160,150 L180,110 L200,150 L240,150 L260,40 L280,190 L300,150 L340,150 L360,100 L380,140 L400,70 L420,150 L480,150"
        stroke="url(#pulseFade)"
        strokeWidth="2.5"
        className="pulse-path"
      />

      <circle cx="260" cy="40" r="4" fill="#2DD4A7" />
      <circle cx="400" cy="70" r="4" fill="#F4B740" />
    </svg>
  );
}
