import { Suspense } from "react";
import { ChatProvider } from "@/components/chat/ChatProvider";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { TransactionCalendar } from "@/components/calendar/TransactionCalendar";

export default function HomePage(): React.JSX.Element {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Suspense fallback={<div>Loading...</div>}>
        <ChatProvider>
          {/* Shared Header - spans across both sections */}
          <ChatHeader />

          {/* Main Content Area - Chat and Calendar side by side */}
          <div className="flex flex-1 min-h-0">
            {/* Chat Section - Left Side */}
            <div className="min-w-[300px] max-w-[400px] border-r border-slate-700">
              <ChatContainer />
            </div>

            {/* Calendar Section - Right Side */}
            <div className="flex-1 min-w-0">
              <TransactionCalendar />
            </div>
          </div>
        </ChatProvider>
      </Suspense>
    </div>
  );
}
