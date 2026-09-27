import React, { useRef, useState } from "react";
import { ExternalLink, Printer } from "lucide-react";
import { Button, Spinner } from "../ui";

// The printable brief. IBM Bob writes only its summary; everything else comes from the analysis.
export function BriefView({ url }) {
  const frame = useRef(null);
  const [loading, setLoading] = useState(true);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">
          Time-stamped brief for the SHO with evidence hashes. Creating it can
          take up to 20 seconds when IBM Bob writes a new summary.
        </p>
        <div className="flex gap-2">
          <Button onClick={() => window.open(url, "_blank", "noopener")}>
            <ExternalLink className="w-4 h-4" />
            Open in new tab
          </Button>
          <Button
            variant="primary"
            disabled={loading}
            onClick={() => frame.current.contentWindow.print()}
          >
            <Printer className="w-4 h-4" />
            Print or save as PDF
          </Button>
        </div>
      </div>
      <div className="relative bg-surface border border-line rounded-lg overflow-hidden">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center gap-2 text-sm text-muted bg-surface">
            <Spinner />
            Preparing the brief…
          </div>
        )}
        <iframe
          ref={frame}
          key={url}
          src={url}
          title="Threat brief"
          onLoad={() => setLoading(false)}
          className="block w-full h-[calc(100vh-190px)] min-h-600px bg-white"
        />
      </div>
    </div>
  );
}
