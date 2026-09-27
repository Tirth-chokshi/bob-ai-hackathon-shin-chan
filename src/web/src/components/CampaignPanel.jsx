import React, { useEffect, useRef, useState } from "react";
import { AlertTriangle, MousePointerClick } from "lucide-react";
import { api } from "../api";
import { Badge, Button, Label, LevelBadge, ScoreBar, Spinner } from "../ui";
import {
  campaignColor,
  FEATURES,
  SIGNALS,
  THREATS,
  fmt,
  fmtTime,
} from "../labels";

// Campaign detail: identity → why flagged → IBM Bob assessment → first posts (docs/design-system.md)
export function CampaignPanel({
  datasetId,
  campaignId,
  bobConfigured,
  onAssessed,
}) {
  const [campaign, setCampaign] = useState(null);
  const [result, setResult] = useState(null); // { verdict, escalation, cached, cost }
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState(null);
  const current = useRef(campaignId);
  current.current = campaignId;

  useEffect(() => {
    setCampaign(null);
    setResult(null);
    setError(null);
    if (!campaignId) return;
    let cancelled = false;
    api
      .campaign(datasetId, campaignId)
      .then((c) => !cancelled && setCampaign(c))
      .catch((e) => !cancelled && setError(e.message));
    api
      .verdict(datasetId, campaignId) // cached only; 404 = not assessed yet
      .then((v) => !cancelled && setResult(v))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [datasetId, campaignId]);

  const ask = async () => {
    const cid = campaignId;
    setAsking(true);
    setError(null);
    try {
      const r = await api.classify(datasetId, cid);
      onAssessed(cid, {
        threat_type: r.verdict.threat_type,
        severity: r.verdict.severity,
        level: r.escalation.level,
      });
      if (current.current === cid) setResult(r);
    } catch (e) {
      if (current.current === cid) setError(e.message);
    } finally {
      setAsking(false);
    }
  };

  if (!campaignId) {
    return (
      <div className="bg-surface border border-line rounded-lg p-6 text-center text-sm text-muted">
        <MousePointerClick
          className="w-6 h-6 mx-auto text-faint mb-2"
          aria-hidden
        />
        Select a campaign to see why it was flagged and IBM Bob's assessment.
      </div>
    );
  }
  if (!campaign) {
    return (
      <div className="bg-surface border border-line rounded-lg p-6 text-sm text-muted flex items-center justify-center gap-2">
        {error ? (
          <span className="text-urgent">{error}</span>
        ) : (
          <>
            <Spinner /> Loading campaign…
          </>
        )}
      </div>
    );
  }

  const evidence = new Set(result?.verdict.evidence_post_ids ?? []);

  return (
    <article className="bg-surface border border-line rounded-lg divide-y divide-line">
      {/* 1. Identity */}
      <header className="p-4">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className="w-3 h-3 rounded-full shrink-0"
            style={{ background: campaignColor(campaign.id) }}
          />
          <h2 className="text-base font-semibold">
            Campaign {campaign.id.toUpperCase()}
          </h2>
          {campaign.top_hashtag && (
            <span className="text-sm text-muted truncate">
              {campaign.top_hashtag}
            </span>
          )}
        </div>
        <p className="text-xs text-muted font-mono mt-1.5">
          {fmt(campaign.size)} accounts · {fmt(campaign.post_count)} posts ·{" "}
          {fmtTime(campaign.first_seen)} – {fmtTime(campaign.last_seen)}
        </p>
      </header>

      {/* 2. Why flagged */}
      <section className="p-4 space-y-3">
        <div className="flex items-baseline justify-between">
          <Label>Coordination score</Label>
          <span className="font-mono text-sm">
            <strong className="text-lg">{campaign.score}</strong> / 100
          </span>
        </div>
        <ul className="space-y-2.5">
          {Object.entries(campaign.features).map(([key, points]) => {
            const f = FEATURES[key] ?? { label: key, max: 25 };
            return (
              <li key={key}>
                <div className="flex justify-between text-xs mb-1">
                  <span>{f.label}</span>
                  <span className="font-mono text-muted">
                    {points}/{f.max}
                  </span>
                </div>
                <ScoreBar
                  value={points}
                  max={f.max}
                  color={campaignColor(campaign.id)}
                />
              </li>
            );
          })}
        </ul>
        <div className="flex flex-wrap gap-1.5 pt-1">
          {campaign.signals.map((s) => (
            <Badge key={s}>{SIGNALS[s] ?? s}</Badge>
          ))}
        </div>
      </section>

      {/* 3. IBM Bob assessment */}
      <section className="p-4 space-y-3">
        <Label>IBM Bob assessment</Label>
        {asking ? (
          <p className="flex items-center gap-2 text-sm text-muted">
            <Spinner className="w-4 h-4 text-accent" /> IBM Bob is reviewing the
            coordination analysis and representative posts.
          </p>
        ) : result ? (
          <Assessment result={result} />
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-muted">
              Not assessed yet. IBM Bob receives the coordination score
              breakdown, signals, campaign metadata and up to 20 stored
              representative posts. It returns the threat type, target,
              severity, legal sections to check and the posts it relied on.
            </p>
            <Button variant="primary" onClick={ask} disabled={!bobConfigured}>
              Ask IBM Bob
            </Button>
            {!bobConfigured && (
              <p className="text-xs text-muted">
                Live assessments require BOB_API_KEY in src/.env and IBM Bob
                Shell installed with `bob` available on the backend PATH.
              </p>
            )}
          </div>
        )}
        {error && <p className="text-sm text-urgent">{error}</p>}
      </section>

      {/* 4. First posts */}
      <section className="p-4">
        <Label className="mb-3">First posts, oldest first</Label>
        <ol className="space-y-2">
          {campaign.sample_posts.map((p) => (
            <li
              key={p.post_id}
              className={`rounded-md border p-3 text-sm ${evidence.has(p.post_id) ? "border-accent/50 bg-subtle" : "border-line"}`}
            >
              <div className="flex items-center justify-between gap-2 text-xs font-mono text-muted mb-1">
                <span className="truncate">
                  @{p.username.replace(/^@/, "")}
                </span>
                <span className="shrink-0">{fmtTime(p.created_at)}</span>
              </div>
              <p className="wrap-break-word">{p.text}</p>
              <div className="flex items-center justify-between mt-1.5 text-xs font-mono text-faint">
                <span>{p.post_id}</span>
                {evidence.has(p.post_id) && (
                  <span className="text-accent font-sans">
                    Cited by IBM Bob
                  </span>
                )}
              </div>
            </li>
          ))}
        </ol>
      </section>
    </article>
  );
}

function Assessment({ result }) {
  const { verdict, escalation, cached, cost } = result;
  return (
    <div className="space-y-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <LevelBadge level={escalation.level} />
        <span className="font-medium">
          {THREATS[verdict.threat_type] ?? verdict.threat_type}
        </span>
        <span className="text-muted">· severity {verdict.severity} of 5</span>
        <span className="ml-auto text-xs text-faint">
          {cached ? "Saved result" : `Cost ${cost.toFixed(3)} Bobcoins`}
        </span>
      </div>

      {verdict.offline_call_to_action && (
        <div className="flex gap-2 rounded-md bg-urgent-soft text-urgent px-3 py-2">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" aria-hidden />
          <span>
            Possible offline call to action flagged in supplied posts. Verify
            the wording and context.
          </span>
        </div>
      )}

      {verdict.offline_indicators?.length > 0 && (
        <div>
          <div className="text-xs text-muted mb-1">
            Reported claims · verification required
          </div>
          <ul className="space-y-1">
            {verdict.offline_indicators.map((indicator, index) => (
              <li
                key={`${indicator.kind}-${index}`}
                className="rounded-md bg-subtle px-3 py-2"
              >
                <span className="font-medium capitalize">
                  {indicator.kind.replaceAll("_", " ")}:{" "}
                </span>
                {indicator.value}
                <span className="block text-xs text-muted mt-0.5">
                  Cited posts: {indicator.evidence_post_ids.join(", ")} · verify
                  independently
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <dl className="space-y-2">
        <div>
          <dt className="text-xs text-muted">Target</dt>
          <dd>{verdict.target}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Narrative</dt>
          <dd>{verdict.narrative}</dd>
        </div>
      </dl>

      <div>
        <div className="text-xs text-muted mb-1">Recommended actions</div>
        <ul className="list-disc pl-5 space-y-0.5">
          {escalation.actions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      </div>

      {verdict.legal_suggestions.length > 0 && (
        <div>
          <div className="text-xs text-muted mb-1">
            Legal sections to check{" "}
            <span className="text-alert">(verify with a legal officer)</span>
          </div>
          <ul className="space-y-1.5">
            {verdict.legal_suggestions.map((s) => (
              <li key={s.id} className="rounded-md bg-subtle px-3 py-2">
                <div className="font-medium">
                  {s.law}{" "}
                  <span className="text-muted font-normal">
                    {s.ipc && s.ipc !== "—" && `(was ${s.ipc}) · `}
                    {s.title}
                  </span>
                </div>
                <div className="text-muted text-xs mt-0.5">{s.why}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
