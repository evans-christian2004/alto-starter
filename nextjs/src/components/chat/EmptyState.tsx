"use client";

import { useState, useEffect } from "react";
import { Target, ListChecks, CheckCircle, AlertCircle, Sparkles, Loader2 } from "lucide-react";
import { useChatContext } from "@/components/chat/ChatProvider";

/**
 * EmptyState - AI Goal Planner welcome screen
 * Extracted from ChatMessagesView empty state section
 * Displays when no messages exist in the current session
 */
export function EmptyState(): React.JSX.Element {
  const { userId, sessionId, handleSubmit } = useChatContext();
  const [suggestions, setSuggestions] = useState<string[]>([
    "Analyze my spending patterns",
    "Optimize payment schedule",
    "Review recurring subscriptions",
  ]);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch AI-generated suggestions when session is available
  useEffect(() => {
    if (!userId || !sessionId) return;

    const fetchSuggestions = async () => {
      try {
        setIsLoading(true);
        const response = await fetch("/api/suggestions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ userId, sessionId }),
        });

        if (response.ok) {
          const data = await response.json();
          if (data.suggestions && data.suggestions.length > 0) {
            setSuggestions(data.suggestions);
          }
        }
      } catch (error) {
        console.error("Error fetching suggestions:", error);
        // Keep default suggestions on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchSuggestions();
  }, [userId, sessionId]);

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
          <div className="flex items-center justify-center gap-2">
            <Sparkles className="h-4 w-4 text-cyan-400" />
            <p className="text-neutral-400 text-sm">
              {isLoading ? "Generating suggestions..." : "Try asking about:"}
            </p>
          </div>
          <div className="flex flex-col gap-2">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-cyan-400" />
              </div>
            ) : (
              suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSubmit(suggestion)}
                  className="px-2 py-1 bg-slate-700/50 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-200 rounded-lg text-xs transition-all duration-200 hover:border-cyan-400/50 border border-transparent cursor-pointer"
                >
                  {suggestion}
                </button>
              ))
            )}
          </div>
        </div>
      </div>
  );
}
