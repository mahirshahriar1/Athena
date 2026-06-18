"use client";

import React, { useCallback, useMemo, useState } from "react";
import { Search, Loader2, Globe } from "lucide-react";

interface CompanyInputProps {
  onSubmit: (company: string, websiteUrl?: string) => void;
  isLoading: boolean;
}

const CompanyInput = React.memo(function CompanyInput({
  onSubmit,
  isLoading,
}: CompanyInputProps) {
  const [company, setCompany] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");

  const isValid = useMemo(() => company.trim().length >= 2, [company]);

  const isDisabled = useMemo(
    () => !isValid || isLoading,
    [isValid, isLoading]
  );

  const handleCompanyChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setCompany(e.target.value);
    },
    []
  );

  const handleUrlChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setWebsiteUrl(e.target.value);
    },
    []
  );

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (isValid && !isLoading) {
        onSubmit(company.trim(), websiteUrl.trim() || undefined);
      }
    },
    [company, websiteUrl, isValid, isLoading, onSubmit]
  );

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-xl space-y-3">
      <div className="relative">
        <input
          type="text"
          value={company}
          onChange={handleCompanyChange}
          placeholder="Enter a company name (e.g., Notion, Stripe)"
          disabled={isLoading}
          className="w-full px-5 py-4 pr-14 rounded-xl bg-zinc-900 border border-zinc-700
                     text-white placeholder-zinc-500 text-lg
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-all duration-200"
        />
        <button
          type="submit"
          disabled={isDisabled}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg
                     bg-blue-600 text-white hover:bg-blue-500
                     disabled:opacity-30 disabled:cursor-not-allowed
                     transition-colors duration-200"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Search className="w-5 h-5" />
          )}
        </button>
      </div>

      <div className="relative">
        <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
        <input
          type="text"
          value={websiteUrl}
          onChange={handleUrlChange}
          placeholder="Optional: primary website (e.g., notion.so)"
          disabled={isLoading}
          className="w-full pl-11 pr-5 py-3 rounded-xl bg-zinc-900/60 border border-zinc-800
                     text-zinc-200 placeholder-zinc-600 text-sm
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-all duration-200"
        />
      </div>

      {!isValid && company.length > 0 && (
        <p className="text-sm text-zinc-500">
          Enter at least 2 characters
        </p>
      )}
    </form>
  );
});

export default CompanyInput;
