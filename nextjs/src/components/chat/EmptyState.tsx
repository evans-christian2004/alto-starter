"use client";

import { Target, ListChecks, CheckCircle } from "lucide-react";

/**
 * EmptyState - AI Goal Planner welcome screen
 * Extracted from ChatMessagesView empty state section
 * Displays when no messages exist in the current session
 */
export function EmptyState(): React.JSX.Element {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 text-center min-h-[65vh]">
        {/* Try asking about section */}
        <div className="space-y-4">
          <p className="text-neutral-400">Try asking about:</p>
          <div className="flex flex-wrap gap-2 justify-center">
            <span className="px-3 py-1 bg-slate-700/50 text-slate-300 rounded-full text-sm">
              Goal setting strategies
            </span>
            <span className="px-3 py-1 bg-slate-700/50 text-slate-300 rounded-full text-sm">
              Project planning methods
            </span>
            <span className="px-3 py-1 bg-slate-700/50 text-slate-300 rounded-full text-sm">
              Task prioritization
            </span>
            <span className="px-3 py-1 bg-slate-700/50 text-slate-300 rounded-full text-sm">
              Achievement milestones
            </span>
          </div>
        </div>
      </div>
  );
}
