import React from "react";

interface FormattedAnswerProps {
  content: string;
}

export const FormattedAnswer: React.FC<FormattedAnswerProps> = ({
  content,
}) => {
  if (!content) return null;

  // Split content by paragraphs or headers
  const lines = content
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);

  const formatTextWithCitations = (text: string) => {
    // Replace citation tags like [doc_2827e35aba79_p3_c0] with highlighted monospace chips
    const parts = text.split(/(\[[\w\-_]+\])/g);
    return parts.map((part, idx) => {
      if (part.startsWith("[") && part.endsWith("]")) {
        return (
          <span
            key={idx}
            className="inline-block mx-1 px-1.5 py-0.2 bg-teal-950/80 border border-teal-500/40 text-teal-300 font-mono text-[11px] rounded-none select-all"
          >
            {part}
          </span>
        );
      }

      // Convert inline **bold** text
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
      return boldParts.map((bPart, bIdx) => {
        if (bPart.startsWith("**") && bPart.endsWith("**")) {
          return (
            <strong
              key={`${idx}-${bIdx}`}
              className="text-neutral-100 font-semibold"
            >
              {bPart.slice(2, -2)}
            </strong>
          );
        }
        return <span key={`${idx}-${bIdx}`}>{bPart}</span>;
      });
    });
  };

  return (
    <div className="space-y-3.5 text-neutral-300 text-xs font-sans leading-relaxed select-text">
      {lines.map((line, idx) => {
        // Headers
        if (
          line.startsWith("###") ||
          line.startsWith("##") ||
          line.startsWith("#")
        ) {
          const headerText = line.replace(/^#+\s*/, "");
          return (
            <h4
              key={idx}
              className="text-sm font-mono font-semibold text-teal-400 pt-2 border-b border-neutral-800/80 pb-1 uppercase tracking-wider"
            >
              {headerText}
            </h4>
          );
        }

        // Bullet points
        if (line.startsWith("* ") || line.startsWith("- ")) {
          const bulletText = line.replace(/^[-*]\s+/, "");
          return (
            <div key={idx} className="flex items-start gap-2 pl-2">
              <span className="w-1.5 h-1.5 bg-teal-400 mt-1.5 shrink-0" />
              <div className="flex-1">
                {formatTextWithCitations(bulletText)}
              </div>
            </div>
          );
        }

        // Numbered list items
        if (/^\d+\.\s+/.test(line)) {
          const match = line.match(/^(\d+)\.\s+(.*)/);
          if (match) {
            return (
              <div key={idx} className="flex items-start gap-2.5 pl-2">
                <span className="font-mono text-teal-400 font-medium text-[11px] shrink-0">
                  {match[1]}.
                </span>
                <div className="flex-1">
                  {formatTextWithCitations(match[2])}
                </div>
              </div>
            );
          }
        }

        // Standard prose sentence block
        return (
          <p key={idx} className="text-neutral-300 text-[13px] leading-relaxed">
            {formatTextWithCitations(line)}
          </p>
        );
      })}
    </div>
  );
};
