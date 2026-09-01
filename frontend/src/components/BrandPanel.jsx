import CipherSeal from "./CipherSeal";
import "./BrandPanel.css";

export default function BrandPanel({ headline, body }) {
  return (
    <div className="brand-panel">
      <div className="brand-panel__mark">TrustShare</div>

      <div className="brand-panel__visual">
        <CipherSeal />
      </div>

      <div className="brand-panel__copy">
        <h1 className="brand-panel__headline">{headline}</h1>
        <p className="brand-panel__body">{body}</p>
      </div>
    </div>
  );
}