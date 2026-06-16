import { FileText, Loader2, Sparkles, Trash2, Upload } from "lucide-react";
import React, { useRef, useState } from "react";

export function DocumentPanel({ documents, loading, onDelete, onRefresh, onSummary, onUpload, selectedDocument,
  onSelectDocument}) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  async function uploadFile(file) {
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please upload a PDF file.");
      return;
    }

    setUploading(true);
    setError("");
    try {
      await onUpload(file);
      await onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleFileChange(event) {
    await uploadFile(event.target.files?.[0]);
    event.target.value = "";
  }

  async function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    await uploadFile(event.dataTransfer.files?.[0]);
  }

  return (
    <section className="rounded-lg border border-line bg-white shadow-soft">
      <div className="flex flex-col gap-4 border-b border-line p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm font-medium text-brand">
            <Sparkles className="h-4 w-4" />
            Source library
          </div>
          <h2 className="mt-1 text-lg font-semibold text-ink">Documents</h2>
          <p className="text-sm text-muted">Upload PDFs, index their text, and keep every answer tied to a source.</p>
        </div>
        <button
          className="inline-flex items-center justify-center gap-2 rounded-md bg-brand px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-60"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
          Upload
        </button>
        <input ref={inputRef} type="file" accept="application/pdf" className="hidden" onChange={handleFileChange} />
      </div>

      {error && <div className="m-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <div
        className={`m-5 rounded-lg border border-dashed p-5 transition ${
          dragging ? "border-brand bg-blue-50" : "border-line bg-slate-50"
        }`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <div className="rounded-md bg-white p-3 text-brand shadow-sm">
              {uploading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Upload className="h-5 w-5" />}
            </div>
            <div>
              <p className="font-medium text-ink">Drop a PDF here or use the upload button</p>
              <p className="text-sm leading-6 text-muted">The backend extracts pages, creates chunks, and builds the searchable index.</p>
            </div>
          </div>
          <span className="rounded-md border border-line bg-white px-3 py-2 text-xs font-semibold uppercase text-muted">PDF only</span>
        </div>
      </div>

      <div className="divide-y divide-line">
        {loading && <div className="p-4 text-sm text-muted">Loading documents...</div>}
        {!loading && documents.length === 0 && <div className="px-5 pb-5 text-sm text-muted">No documents uploaded yet.</div>}
        {documents.map((document) => (
          <div key={document.id}
          onClick={() => onSelectDocument(document)}
          className={`flex flex-col gap-4 p-5 cursor-pointer sm:flex-row sm:items-center sm:justify-between ${
            selectedDocument?.id === document.id
            ? "bg-blue-50 border-l-4 border-blue-600"
            : ""
            }`}
            >
            <div className="flex min-w-0 items-center gap-3">
              <div className="rounded-md bg-blue-50 p-3 text-brand">
                <FileText className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="truncate font-medium text-ink">{document.filename}</p>
                <p className="text-sm text-muted">{new Date(document.upload_date).toLocaleString()}</p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <button className="rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-gray-50" onClick={() => onSummary(document.id)}>
                Summary
              </button>
              <button className="rounded-md border border-line p-2 text-muted hover:bg-red-50 hover:text-red-700" onClick={() => onDelete(document.id)} aria-label="Delete document">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
