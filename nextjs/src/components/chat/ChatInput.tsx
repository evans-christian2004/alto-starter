"use client";

import { InputForm } from "@/components/InputForm";
import { useChatContext } from "@/components/chat/ChatProvider";

/**
 * ChatInput - Input form wrapper with context integration
 * Handles message submission through context instead of prop drilling
 * Extracted from ChatMessagesView input section
 */
export function ChatInput(): React.JSX.Element {
  const { handleSubmit, isLoading, sessionId } = useChatContext();

  // Show disabled state when no session
  const hasSession = Boolean(sessionId);

  return (
    <div className="relative z-10 flex-shrink-0 border-t-2 border-slate-600/80 bg-slate-900/95 backdrop-blur-md shadow-2xl shadow-black/40">
      <div className="w-full p-3 pt-4">
        {!hasSession && (
          <div className="text-center text-xs text-yellow-500/70 mb-2">
            ⚠️ Create a session to start chatting
          </div>
        )}
        <InputForm
          onSubmit={handleSubmit}
          isLoading={isLoading || !hasSession}
          context="chat"
        />
      </div>
    </div>
  );
}
