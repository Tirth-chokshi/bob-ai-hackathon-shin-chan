import React from "react";
import { Card, LevelBadge, ScoreBar, Stat } from "../ui";
import { TimelineChart } from "../components/TimelineChart";
import { campaignColor, fmt, THREATS, BUCKET_LABEL } from "../labels";

// Triage: key numbers → activity → campaign list with the selected campaign's detail beside it
export function OverviewView({ data, selectedId, onSelect, panel }) {
  const { campaigns, timeline } = data;
  const count = (level) =>
    campaigns.filter((c) => c.assessment?.level === level).length;
  const notAssessed = campaigns.filter((c) => !c.assessment).length;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Campaigns found" value={fmt(campaigns.length)} />
        <Stat
          label="Urgent"
          value={count("URGENT")}
          tone={count("URGENT") ? "URGENT" : "muted"}
          hint="Act now"
        />
        <Stat
          label="Alert"
          value={count("ALERT")}
          tone={count("ALERT") ? "ALERT" : "muted"}
          hint="Log and watch closely"
        />
        <Stat
          label="Not assessed by IBM Bob"
          value={notAssessed}
          tone="muted"
          hint="Select a campaign to assess it"
        />
      </div>

      <Card
        title="Activity over time"
        subtitle={`Posts per ${BUCKET_LABEL[timeline.bucket_seconds] ?? "bucket"}. Coloured lines are the accounts of each campaign; a spike together means they posted together.`}
      >
        <TimelineChart timeline={timeline} />
      </Card>

      <div className="grid gap-4 lg:grid-cols-12 items-start">
        <Card
          title="Campaigns"
          subtitle="Ranked by coordination score. Select one to see why it was flagged."
          className="lg:col-span-7"
          bodyClassName="overflow-x-auto"
        >
          {campaigns.length === 0 ? (
            <p className="p-6 text-sm text-muted text-center">
              No coordinated campaigns found: no group of 5 or more accounts
              repeatedly posted the same text, link or reply within seconds of
              each other.
            </p>
          ) : (
            <CampaignTable
              campaigns={campaigns}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          )}
        </Card>
        <div className="lg:col-span-5 lg:sticky lg:top-72px lg:max-h-[calc(100vh-88px)] lg:overflow-y-auto">
          {panel}
        </div>
      </div>
    </div>
  );
}

function CampaignTable({ campaigns, selectedId, onSelect }) {
  return (
    <table className="w-full text-sm">
      <thead className="bg-subtle text-xs text-muted text-left">
        <tr>
          <th className="font-medium px-4 py-2">Campaign</th>
          <th className="font-medium px-4 py-2 text-right">Accounts</th>
          <th className="font-medium px-4 py-2 text-right">Posts</th>
          <th className="font-medium px-4 py-2 w-36">Score</th>
          <th className="font-medium px-4 py-2">IBM Bob assessment</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {campaigns.map((c) => {
          const selected = c.id === selectedId;
          return (
            <tr
              key={c.id}
              onClick={() => onSelect(c.id)}
              aria-selected={selected}
              className={`cursor-pointer ${selected ? "bg-subtle" : "hover:bg-subtle/60"}`}
            >
              <td
                className="px-4 py-3"
                style={{
                  boxShadow: selected
                    ? `inset 3px 0 0 ${campaignColor(c.id)}`
                    : undefined,
                }}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ background: campaignColor(c.id) }}
                  />
                  <span className="font-medium font-mono">
                    {c.id.toUpperCase()}
                  </span>
                  <span className="text-muted truncate max-w-180px">
                    {c.top_hashtag}
                  </span>
                </div>
              </td>
              <td className="px-4 py-3 text-right font-mono tabular-nums">
                {fmt(c.size)}
              </td>
              <td className="px-4 py-3 text-right font-mono tabular-nums">
                {fmt(c.post_count)}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono tabular-nums w-7 text-right">
                    {c.score}
                  </span>
                  <ScoreBar value={c.score} color={campaignColor(c.id)} />
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <LevelBadge level={c.assessment?.level} />
                  {c.assessment && (
                    <span className="text-muted text-xs truncate">
                      {THREATS[c.assessment.threat_type]}
                    </span>
                  )}
                </div>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
