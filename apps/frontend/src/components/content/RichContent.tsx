import { ReactNode } from "react";

type JsonValue = string | number | boolean | null | JsonObject | JsonValue[];
type JsonObject = { [key: string]: JsonValue };

export function tryParseJson(value: string): JsonValue | null {
  const trimmed = value.trim();
  if (!trimmed.startsWith("{") && !trimmed.startsWith("[")) return null;

  try {
    const parsed = JSON.parse(trimmed);
    if (parsed && typeof parsed === "object") {
      return parsed as JsonValue;
    }
  } catch {
    return null;
  }

  return null;
}

function renderPrimitive(value: string | number | boolean | null): ReactNode {
  if (value === null) return <span className="text-slate-500">null</span>;
  if (typeof value === "string") {
    return <span className="text-slate-900">{`"${value}"`}</span>;
  }
  if (typeof value === "boolean") return <span className="text-indigo-700">{value.toString()}</span>;
  return <span className="text-emerald-700">{value}</span>;
}

function renderQuotedCode(value: string, inline: boolean, className: string) {
  const parts: ReactNode[] = [];
  const pattern = /'([^']+)'/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let requiresBlock = false;

  while ((match = pattern.exec(value)) !== null) {
    if (match.index > lastIndex) {
      parts.push(value.slice(lastIndex, match.index));
    }

    const snippet = match[1];
    const isMultiline = snippet.includes("\n");
    const isLong = snippet.length > 120;
    const shouldBlock = isMultiline || isLong;
    if (shouldBlock) {
      requiresBlock = true;
      parts.push(
        <pre
          key={`code-${match.index}`}
          className="my-1 whitespace-pre-wrap rounded-md border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700"
        >
          {snippet}
        </pre>
      );
    } else {
      parts.push(
        <code
          key={`code-${match.index}`}
          className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] text-slate-800"
        >
          {snippet}
        </code>
      );
    }

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < value.length) {
    parts.push(value.slice(lastIndex));
  }

  if (inline && !requiresBlock) {
    return <span className={`whitespace-pre-wrap ${className}`}>{parts}</span>;
  }

  return <div className={`whitespace-pre-wrap ${className}`}>{parts}</div>;
}

function JsonViewer({ value, level = 0 }: { value: JsonValue; level?: number }) {
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-slate-500">[]</span>;
    }

    return (
      <div className={level > 0 ? "pl-3 border-l border-slate-200" : ""}>
        {value.map((item, index) => (
          <div key={index} className="mt-1">
            <span className="text-xs font-semibold text-slate-500">[{index}]</span>{" "}
            <JsonViewer value={item} level={level + 1} />
          </div>
        ))}
      </div>
    );
  }

  if (value && typeof value === "object") {
    const entries = Object.entries(value as JsonObject);
    if (entries.length === 0) {
      return <span className="text-slate-500">{"{}"}</span>;
    }

    return (
      <div className={level > 0 ? "pl-3 border-l border-slate-200" : ""}>
        {entries.map(([key, entryValue]) => (
          <div key={key} className="mt-1">
            <span className="text-xs font-semibold text-slate-500">{key}:</span>{" "}
            <JsonViewer value={entryValue} level={level + 1} />
          </div>
        ))}
      </div>
    );
  }

  return <span className="font-mono text-slate-900">{renderPrimitive(value)}</span>;
}

export function RichContent({
  value,
  className = "",
  inline = false,
}: {
  value: string;
  className?: string;
  inline?: boolean;
}) {
  const parsed = tryParseJson(value);

  if (parsed) {
    return (
      <div className={`rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ${className}`}>
        <JsonViewer value={parsed} />
      </div>
    );
  }

  return renderQuotedCode(value, inline, className);
}
