"use client";

import { Target, ListChecks, CheckCircle } from "lucide-react";

/**
 * EmptyState - AI Goal Planner welcome screen
 * Extracted from ChatMessagesView empty state section
 * Displays when no messages exist in the current session
 */
export function EmptyState(): React.JSX.Element {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-3 text-center min-h-[65vh]">
        {/* Try asking about section */}
        <div className="space-y-3">
          <p className="text-neutral-400 text-sm">Try asking about:</p>
          <div className="flex flex-col gap-2">
            <span className="px-2 py-1 bg-slate-700/50 text-slate-300 rounded-lg text-xs">
              Your Finances
            </span>
            <span className="px-2 py-1 bg-slate-700/50 text-slate-300 rounded-lg text-xs">
              Moving Purchases
            </span>
            <span className="px-2 py-1 bg-slate-700/50 text-slate-300 rounded-lg text-xs">
              Account Insights
            </span>
          </div>
        </div>
      </div>
  );
}
