"use client";

import { Target, ListChecks, CheckCircle, AlertCircle } from "lucide-react";
import { useChatContext } from "@/components/chat/ChatProvider";

/**
 * EmptyState - AI Goal Planner welcome screen
 * Extracted from ChatMessagesView empty state section
 * Displays when no messages exist in the current session
 */
export function EmptyState(): React.JSX.Element {
  const { userId, sessionId } = useChatContext();

  // Show different message if no session exists
  if (!sessionId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-3 text-center min-h-[65vh]">
        <div className="space-y-4 max-w-md">
          <div className="flex justify-center">
            <AlertCircle className="h-12 w-12 text-yellow-500/70" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-200">
              No Session Active
            </h3>
            <p className="text-sm text-slate-400">
              Please create a new session to start chatting with Alto.
            </p>
            <p className="text-xs text-slate-500 mt-2">
              Click <span className="font-semibold text-cyan-400">"Create New Session"</span> in the session selector above.
            </p>
          </div>
        </div>
      </div>
    );
  }

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
