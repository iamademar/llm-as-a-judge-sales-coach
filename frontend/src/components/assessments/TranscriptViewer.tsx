"use client";

import * as React from "react";
import { RiSearchLine } from "@remixicon/react";

interface TranscriptViewerProps {
  transcript: string;
}

interface ParsedMessage {
  speaker: string;
  text: string;
  isRep: boolean;
}

function parseTranscript(raw: string): ParsedMessage[] {
  // Try to parse as JSON array first (structured transcript format)
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return parsed.map((item: any) => ({
        speaker: item.speaker_id || item.speaker || "Unknown",
        text: item.text || item.content || "",
        isRep: (item.speaker_id || item.speaker || "").toLowerCase().includes("rep"),
      }));
    }
  } catch {
    // Not JSON, try to parse as plain text with speaker tags
  }

  // Parse plain text format like "Rep: Hello" or "[Rep] Hello"
  const lines = raw.split("\n").filter((line) => line.trim());
  const messages: ParsedMessage[] = [];

  for (const line of lines) {
    // Match patterns like "Rep:", "Customer:", "[Rep]", etc.
    const match = line.match(/^(?:\[([^\]]+)\]|([^:]+):)\s*(.+)$/);
    if (match) {
      const speaker = (match[1] || match[2] || "").trim();
      const text = (match[3] || "").trim();
      const isRep = speaker.toLowerCase().includes("rep") || speaker.toLowerCase().includes("sales");
      messages.push({ speaker, text, isRep });
    } else if (line.trim()) {
      // No speaker tag, add as continuation
      if (messages.length > 0) {
        messages[messages.length - 1].text += " " + line.trim();
      } else {
        messages.push({ speaker: "Unknown", text: line.trim(), isRep: false });
      }
    }
  }

  return messages;
}

export function TranscriptViewer({ transcript }: TranscriptViewerProps) {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [filter, setFilter] = React.useState<"all" | "rep" | "customer">("all");

  const messages = React.useMemo(() => parseTranscript(transcript), [transcript]);

  const filteredMessages = React.useMemo(() => {
    let filtered = messages;

    // Apply speaker filter
    if (filter === "rep") {
      filtered = filtered.filter((m) => m.isRep);
    } else if (filter === "customer") {
      filtered = filtered.filter((m) => !m.isRep);
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((m) => m.text.toLowerCase().includes(query));
    }

    return filtered;
  }, [messages, filter, searchQuery]);

  const highlightText = (text: string, query: string): React.ReactNode => {
    if (!query.trim()) return text;

    const parts = text.split(new RegExp(`(${query})`, "gi"));
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={i} className="bg-indigo-500/30 text-indigo-200 rounded px-0.5">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      {/* Controls bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-4">
        <h3 className="text-sm font-medium text-slate-200">Transcript</h3>
        <div className="flex items-center gap-3">
          {/* Filter toggle group */}
          <div className="flex rounded-lg border border-slate-700 p-0.5 bg-slate-950">
            {(["all", "rep", "customer"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  filter === f
                    ? "bg-slate-700 text-slate-100"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {f === "all" ? "All" : f === "rep" ? "Rep" : "Customer"}
              </button>
            ))}
          </div>

          {/* Search input */}
          <div className="relative">
            <RiSearchLine className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-40 rounded-lg border border-slate-700 bg-slate-950 py-1.5 pl-9 pr-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Transcript messages */}
      <div className="max-h-[480px] overflow-y-auto rounded-lg border border-slate-800 bg-slate-950/50">
        {filteredMessages.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">
            {messages.length === 0
              ? "No transcript content available"
              : "No messages match your search"}
          </div>
        ) : (
          <div className="divide-y divide-slate-800/50">
            {filteredMessages.map((message, index) => (
              <div
                key={index}
                className={`p-3 ${
                  message.isRep
                    ? "border-l-2 border-l-indigo-500/50"
                    : "border-l-2 border-l-slate-600/50"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${
                      message.isRep
                        ? "bg-indigo-500/20 text-indigo-300"
                        : "bg-slate-700/50 text-slate-300"
                    }`}
                  >
                    {message.speaker}
                  </span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {highlightText(message.text, searchQuery)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Message count */}
      <div className="mt-3 text-xs text-slate-500">
        Showing {filteredMessages.length} of {messages.length} messages
      </div>
    </div>
  );
}

