"use client";

import React, { useCallback, useMemo, useState } from "react";
import { Search, Loader2 } from "lucide-react";

interface CompanyInputProps {
  onSubmit: (company: string) => void;
  isLoading: boolean;
}

const CompanyInput = React.memo(function CompanyInput({
  onSubmit,
  isLoading,
}: CompanyInputProps) {
  const [value, setValue] = useState("");

  const isValid = useMemo(() => value.trim().length >= 2, [value]);

  const isDisabled = useMemo(
    () => !isValid || isLoading,
    [isValid, isLoading]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setValue(e.target.value);
    },
    []
  );

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (isValid && !isLoading) {
        onSubmit(value.trim());
      }
    },
    [value, isValid, isLoading, onSubmit]
  );

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-xl">
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={handleChange}
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
      {!isValid && value.length > 0 && (
        <p className="mt-2 text-sm text-zinc-500">
          Enter at least 2 characters
        </p>
      )}
    </form>
  );
});

export default CompanyInput;
