import "./CipherSeal.css";

const GRID_SIZE = 36; 

export default function CipherSeal() {
  const blocks = Array.from({ length: GRID_SIZE }, (_, i) => i);

  return (
    <div className="cipher-seal" role="img" aria-label="Illustration of a file being encrypted and sealed">
      <div className="cipher-seal__grid">
        {blocks.map((i) => (
          <span
            key={i}
            className="cipher-seal__block"
            style={{ "--delay": `${(i % 6) * 0.09 + Math.floor(i / 6) * 0.06}s` }}
          />
        ))}
      </div>

      <svg
        className="cipher-seal__lock"
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect
          className="cipher-seal__lock-body"
          x="14"
          y="28"
          width="36"
          height="28"
          rx="4"
        />
        <path
          className="cipher-seal__lock-shackle"
          d="M22 28V20a10 10 0 0 1 20 0v8"
        />
        <circle className="cipher-seal__lock-pin" cx="32" cy="40" r="3.5" />
        <line
          className="cipher-seal__lock-pin"
          x1="32"
          y1="42.5"
          x2="32"
          y2="47.5"
        />
      </svg>
    </div>
  );
}