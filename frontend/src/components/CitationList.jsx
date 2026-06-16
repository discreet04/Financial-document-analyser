import React from "react";

export function CitationList({ citations = [] }) {
  if (!citations.length) {
    return null;
  }

  return (
    <div className="mt-4 space-y-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">Sources</p>
      {citations.map((citation, index) => (
        <details key={`${citation.document_id}-${citation.page_number}-${index}`} className="rounded-lg border border-line bg-white p-3">
          <summary className="cursor-pointer text-sm font-medium text-ink">
            {citation.document_name} - page {citation.page_number}
          </summary>
          <p className="mt-2 text-sm leading-6 text-muted">{citation.chunk_text}</p>
        </details>
      ))}
    </div>
  );
}
