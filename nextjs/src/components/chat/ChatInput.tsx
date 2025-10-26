"use client";

import { InputForm } from "@/components/InputForm";
import { useChatContext } from "@/components/chat/ChatProvider";

/**
 * ChatInput - Input form wrapper with context integration
 * Handles message submission through context instead of prop drilling
 * Extracted from ChatMessagesView input section
 */
export function ChatInput(): React.JSX.Element {
  const { handleSubmit, isLoading } = useChatContext();

  return (
    <div className="relative z-10 flex-shrink-0 border-t-2 border-slate-600/80 bg-slate-900/95 backdrop-blur-md shadow-2xl shadow-black/40">
      <div className="w-full p-3 pt-4">
        <InputForm
          onSubmit={handleSubmit}
          isLoading={isLoading}
          context="chat"
        />
      </div>
    </div>
  );
}
