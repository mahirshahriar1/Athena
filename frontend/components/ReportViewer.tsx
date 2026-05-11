"use client";

import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import { FileText, Download } from "lucide-react";

interface ReportViewerProps {
  report: string;
  company: string;
}

const ReportViewer = React.memo(function ReportViewer({
  report,
  company,
}: ReportViewerProps) {
  const wordCount = useMemo(() => {
    return report.split(/\s+/).filter(Boolean).length;
  }, [report]);

  const handleDownload = useMemo(
    () => () => {
      const blob = new Blob([report], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${company.toLowerCase().replace(/\s+/g, "-")}-report.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    [report, company]
  );

  return (
    <div className="w-full max-w-4xl bg-zinc-900 border border-zinc-700 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-zinc-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-blue-400" />
          <div>
            <h2 className="text-lg font-semibold text-white">
              Intelligence Report: {company}
            </h2>
            <p className="text-xs text-zinc-500">{wordCount} words</p>
          </div>
        </div>
        <button
          onClick={handleDownload}
          className="flex items-center gap-2 px-3 py-2 rounded-lg
                     bg-zinc-800 text-zinc-300 text-sm hover:bg-zinc-700
                     transition-colors duration-200"
        >
          <Download className="w-4 h-4" />
          Download .md
        </button>
      </div>

      {/* Report content */}
      <div className="p-6 prose prose-invert prose-zinc max-w-none
                      prose-headings:text-zinc-100 prose-p:text-zinc-300
                      prose-li:text-zinc-300 prose-strong:text-white
                      prose-a:text-blue-400 prose-code:text-green-400">
        <ReactMarkdown>{report}</ReactMarkdown>
      </div>
    </div>
  );
});

export default ReportViewer;
