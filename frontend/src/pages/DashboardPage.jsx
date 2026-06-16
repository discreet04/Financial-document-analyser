import { Activity, Bot, FileText, LogOut, MessageSquare, RefreshCw, Search, Send, ShieldCheck } from "lucide-react";
import React, { useEffect, useState } from "react";

import { api } from "../api/client";
import { CitationList } from "../components/CitationList";
import { DocumentPanel } from "../components/DocumentPanel";
import { SummaryPanel } from "../components/SummaryPanel";
import { useAuth } from "../context/AuthContext";

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted">{label}</p>
          <p className="mt-2 text-3xl font-semibold text-ink">{value}</p>
        </div>
        <div className="rounded-md bg-blue-50 p-3 text-brand ring-1 ring-blue-100">
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { logout, user } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [history, setHistory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(true);
  const [chatLoading, setChatLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const [dashboardData, documentsData, historyData] = await Promise.all([
        api.dashboard(),
        api.documents(),
        api.chatHistory(),
      ]);
      setDashboard(dashboardData);
      setDocuments(documentsData);
      setHistory(historyData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function sendQuestion(event) {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion) return;

    const userMessage = { role: "user", content: cleanQuestion };
    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setChatLoading(true);
    setError("");

    try {
      const response = await api.askQuestion({ question: cleanQuestion,  document_id: selectedDocument?.id ?? null});
      setMessages((current) => [...current, { role: "assistant", content: response.answer, citations: response.citations }]);
      const historyData = await api.chatHistory();
      setHistory(historyData);
    } catch (err) {
      setError(err.message);
    } finally {
      setChatLoading(false);
    }
  }

  async function deleteDocument(id) {
    setError("");
    try {
      await api.deleteDocument(id);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function openSummary(id) {
    setSummary(null);
    setSummaryLoading(true);
    try {
      setSummary(await api.summarizeDocument(id));
    } catch (err) {
      setError(err.message);
    } finally {
      setSummaryLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-800 bg-slate-950 text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-5 sm:px-6 lg:px-8">
          <div>
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-white/10 p-2 text-cyan-200">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-lg font-semibold">Financial Document Analayser</h1>
                <p className="text-sm text-slate-300">Signed in as {user?.name}</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="rounded-md border border-white/15 p-2 text-slate-200 hover:bg-white/10" onClick={refresh} aria-label="Refresh">
              <RefreshCw className="h-4 w-4" />
            </button>
            <button className="inline-flex items-center gap-2 rounded-md border border-white/15 px-3 py-2 text-sm font-medium text-slate-100 hover:bg-white/10" onClick={logout}>
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </header>

      <div className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6 sm:px-6 lg:flex-row lg:items-end lg:justify-between lg:px-8">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-brand">Document intelligence workspace</p>
            <h2 className="mt-2 text-3xl font-semibold text-ink">Ask and analyse your PDF.</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
              Upload contracts, statements, policies, or reports, then retrieve grounded answers with citations from the files you own.
            </p>
          </div>
          <div className="flex items-center gap-3 rounded-lg border border-line bg-slate-50 px-4 py-3">
            <Search className="h-5 w-5 text-brand" />
            <div>
              <p className="text-sm font-medium text-ink">Cited search</p>
              <p className="text-xs text-muted">Answers stay tied to source pages.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(0,1fr)_430px] lg:px-8">
        <section className="space-y-6">
          {error && <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

          <div className="grid gap-4 sm:grid-cols-3">
            <Metric icon={FileText} label="Documents" value={dashboard?.total_documents ?? 0} />
            <Metric icon={MessageSquare} label="Chats" value={dashboard?.total_chats ?? 0} />
            <Metric icon={Activity} label="Recent items" value={dashboard?.recent_activity?.length ?? 0} />
          </div>

          <DocumentPanel
            documents={documents}
            loading={loading}
            selectedDocument={selectedDocument}
            onSelectDocument={setSelectedDocument}
            onDelete={deleteDocument}
            onRefresh={refresh}
            onSummary={openSummary}
            onUpload={api.uploadDocument}
          />

          <section className="rounded-lg border border-line bg-white shadow-soft">
            <div className="border-b border-line p-5">
              <h2 className="text-lg font-semibold text-ink">Recent Activity</h2>
              <p className="text-sm text-muted">Uploads, summaries, and document questions appear here.</p>
            </div>
            <div className="divide-y divide-line">
              {(dashboard?.recent_activity || []).map((activity, index) => (
                <div key={`${activity.type}-${index}`} className="p-5">
                  <p className="text-sm font-medium text-ink">{activity.label}</p>
                  <p className="text-sm text-muted">{new Date(activity.timestamp).toLocaleString()}</p>
                </div>
              ))}
              {!loading && !dashboard?.recent_activity?.length && <div className="p-5 text-sm text-muted">No recent activity yet.</div>}
            </div>
          </section>
        </section>

        <aside className="flex min-h-[680px] flex-col rounded-lg border border-line bg-white shadow-soft lg:sticky lg:top-6 lg:max-h-[calc(100vh-3rem)]">
          <div className="border-b border-line p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-emerald-50 p-2 text-emerald-700">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <h2 className="font-semibold text-ink">Ask your documents</h2>
                <p className="text-sm text-muted">Search every uploaded PDF with cited answers.</p>
              </div>
            </div>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto bg-slate-50 p-5">
            {messages.length === 0 && (
              <div className="rounded-lg border border-line bg-white p-4 text-sm leading-6 text-muted">
                Upload PDFs, then ask about risks, covenants, ratios, obligations, policy changes, or key parties.
              </div>
            )}
            {messages.map((message, index) => (
              <div key={index} className={message.role === "user" ? "ml-8 rounded-lg bg-brand p-4 text-sm text-white shadow-sm" : "mr-8 rounded-lg border border-line bg-white p-4 text-sm text-ink"}>
                <p className="whitespace-pre-wrap leading-6">{message.content}</p>
                <CitationList citations={message.citations} />
              </div>
            ))}
            {chatLoading && <div className="mr-8 rounded-lg border border-line bg-white p-4 text-sm text-muted">Thinking through the retrieved sources...</div>}
          </div>

          <form className="border-t border-line p-5" onSubmit={sendQuestion}>
            <textarea
              className="min-h-24 w-full resize-none rounded-md border border-line p-3 text-sm leading-6 outline-none focus:border-brand focus:ring-4 focus:ring-blue-100"
              placeholder="Ask a question about uploaded financial documents..."
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
            />
            <button className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60" disabled={chatLoading}>
              <Send className="h-4 w-4" />
              Send question
            </button>
          </form>
        </aside>

        <section className="rounded-lg border border-line bg-white shadow-soft lg:col-span-2">
          <div className="border-b border-line p-5">
            <h2 className="text-lg font-semibold text-ink">Chat History</h2>
            <p className="text-sm text-muted">Review earlier questions and the answer trail.</p>
          </div>
          <div className="divide-y divide-line">
            {history.map((item) => (
              <details key={item.id} className="p-5">
                <summary className="cursor-pointer font-medium text-ink">{item.question}</summary>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-muted">{item.answer}</p>
                <CitationList citations={item.citations} />
              </details>
            ))}
            {!loading && history.length === 0 && <div className="p-5 text-sm text-muted">No chat history yet.</div>}
          </div>
        </section>
      </div>

      <SummaryPanel loading={summaryLoading} summary={summary} onClose={() => setSummary(null)} />
    </main>
  );
}
