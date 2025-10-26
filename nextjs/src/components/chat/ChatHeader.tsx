"use client";

import { Bot } from "lucide-react";
import { UserIdInput } from "@/components/chat/UserIdInput";
import { SessionSelector } from "@/components/chat/SessionSelector";
import { useChatContext } from "@/components/chat/ChatProvider";
import Image from "next/image";

/**
 * ChatHeader - User and session management interface
 * Extracted from ChatMessagesView header section
 * Handles user ID input and session selection
 */
export function ChatHeader(): React.JSX.Element {
  const {
    userId,
    sessionId,
    handleUserIdChange,
    handleUserIdConfirm,
    handleSessionSwitch,
    handleCreateNewSession,
  } = useChatContext();

  return (
    <div className="relative z-10 flex-shrink-0 border-b border-slate-700/50 bg-slate-800/80 backdrop-blur-sm">
      <div className="max-w-5xl mx-auto w-full flex justify-between items-center p-4">
        {/* Left side - App branding */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 flex items-center justify-center">
            <Image className="bg-sky-100 rounded-2xl p-1" src="/images/logo.svg" width={120} height={120} alt="alto logo"/>
          </div>
          <span className="text-xl font-semibold text-sky-100">Alto</span>
        </div>

        {/* Right side - User controls */}
        <div className="flex items-center gap-4">
          {/* User ID Management */}
          <UserIdInput
            currentUserId={userId}
            onUserIdChange={handleUserIdChange}
            onUserIdConfirm={handleUserIdConfirm}
            className="text-xs"
          />

          {/* Session Management */}
          {userId && (
            <SessionSelector
              currentUserId={userId}
              currentSessionId={sessionId}
              onSessionSelect={handleSessionSwitch}
              onCreateSession={handleCreateNewSession}
              className="text-xs"
            />
          )}
        </div>
      </div>
    </div>
  );
}
