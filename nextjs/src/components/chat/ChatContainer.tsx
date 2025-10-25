"use client";

import { BackendHealthChecker } from "@/components/chat/BackendHealthChecker";
import { ChatContent } from "./ChatContent";
import { ChatInput } from "./ChatInput";

/**
 * ChatLayout - Pure layout component for chat interface
 * Handles only UI structure and layout, no business logic
 * Uses context for all state management
 */
export function ChatContainer(): React.JSX.Element {
  return (
    <div className="h-full flex flex-col bg-slate-900 relative">
      <BackendHealthChecker>
        {/* Fixed background */}
        <div className="absolute inset-0 via-slate-800 pointer-events-none"></div>

        {/* Scrollable Messages Area - takes remaining space */}
        <div className="relative z-10 flex-1 min-h-0">
          <ChatContent />
        </div>

        {/* Fixed Input Area - always at bottom */}
        <div className="relative z-10 flex-shrink-0">
          <ChatInput />
        </div>
      </BackendHealthChecker>
    </div>
  );
}
