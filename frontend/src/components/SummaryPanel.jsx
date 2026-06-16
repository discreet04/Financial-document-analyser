import { AlertTriangle, CheckCircle2, Scale, TrendingUp, X } from "lucide-react";
import React from "react";

function SummaryList({ icon: Icon, title, items }) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-2 font-medium text-ink">
        <Icon className="h-4 w-4 text-brand" />
        {title}
      </div>
      <ul className="space-y-2 text-sm leading-6 text-muted">
        {(items || []).map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export function SummaryPanel({ loading, onClose, summary }) {
  if (!loading && !summary) return null;

  return (
    <aside className="fixed inset-y-0 right-0 z-20 w-full max-w-xl overflow-y-auto border-l border-line bg-white p-6 shadow-soft">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-ink">Executive Summary</h2>
          <p className="text-sm text-muted">Generated from the selected document.</p>
        </div>
        <button className="rounded-md border border-line p-2 hover:bg-gray-50" onClick={onClose} aria-label="Close summary">
          <X className="h-4 w-4" />
        </button>
      </div>

      {loading && <div className="text-sm text-muted">Generating summary...</div>}

      {summary && (
        <div className="space-y-6">
          <p className="rounded-lg bg-gray-50 p-4 text-sm leading-6 text-ink">{summary.executive_summary}</p>
          <SummaryList icon={AlertTriangle} title="Key Risks" items={summary.key_risks} />
          <SummaryList icon={TrendingUp} title="Financial Highlights" items={summary.financial_highlights} />
          <SummaryList icon={Scale} title="Compliance Concerns" items={summary.compliance_concerns} />
          <SummaryList icon={CheckCircle2} title="Important Findings" items={summary.important_findings} />
        </div>
      )}
    </aside>
  );
}
