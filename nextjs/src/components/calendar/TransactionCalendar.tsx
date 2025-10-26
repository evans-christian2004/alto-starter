"use client";

import React, { useState, useMemo, useEffect } from "react";
import { ChevronLeft, ChevronRight, ArrowRight, Calendar as CalendarIcon, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { userData, type Transaction } from "@/data/userData";

interface CalendarModification {
  modification_id: string;
  transaction_id: string;
  merchant_name: string;
  original_date?: string;
  new_date?: string;
  date?: string; // For planned transactions
  amount: number;
  reason: string;
  type?: string;
  category?: string;
  status: "suggested" | "approved";
}

interface ModificationsData {
  modifications: CalendarModification[];
  last_updated: string | null;
}

const CATEGORY_COLORS: Record<string, string> = {
  INCOME: "bg-green-500/20 text-green-300 border-green-500/50",
  ENTERTAINMENT: "bg-purple-500/20 text-purple-300 border-purple-500/50",
  FOOD_AND_DRINK: "bg-orange-500/20 text-orange-300 border-orange-500/50",
  UTILITIES: "bg-blue-500/20 text-blue-300 border-blue-500/50",
  TRANSPORTATION: "bg-yellow-500/20 text-yellow-300 border-yellow-500/50",
  TRANSFER_OUT: "bg-red-500/20 text-red-300 border-red-500/50",
  GENERAL_MERCHANDISE: "bg-pink-500/20 text-pink-300 border-pink-500/50",
};

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export function TransactionCalendar(): React.JSX.Element {
  const [currentDate, setCurrentDate] = useState(new Date(2025, 9, 1)); // October 2025
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [modifications, setModifications] = useState<CalendarModification[]>([]);
  const [hasAutoNavigated, setHasAutoNavigated] = useState(false);

  // Poll for modifications every 3 seconds
  useEffect(() => {
    const fetchModifications = async () => {
      try {
        const response = await fetch("/api/calendar-modifications");
        if (response.ok) {
          const data: ModificationsData = await response.json();
          setModifications(data.modifications || []);
        }
      } catch (error) {
        console.error("Error fetching modifications:", error);
      }
    };

    fetchModifications();
    const interval = setInterval(fetchModifications, 3000);
    return () => clearInterval(interval);
  }, []);

  // Create a map of transaction_id -> new_date for moved transactions
  const movedTransactions = useMemo(() => {
    const map = new Map<string, { newDate: string; originalDate: string; reason: string }>();
    modifications.forEach((mod) => {
      if (mod.type !== "planned" && mod.new_date && mod.original_date) {
        map.set(mod.transaction_id, {
          newDate: mod.new_date,
          originalDate: mod.original_date,
          reason: mod.reason,
        });
      }
    });
    return map;
  }, [modifications]);

  // Get planned transactions
  const plannedTransactions = useMemo(() => {
    return modifications.filter((mod) => mod.type === "planned");
  }, [modifications]);

  // Auto-navigate to the month with the most recent modification (only once when modifications appear)
  useEffect(() => {
    // Only auto-navigate once when modifications first appear
    if (modifications.length === 0) {
      // Reset flag when modifications are cleared
      setHasAutoNavigated(false);
      return;
    }

    // Don't auto-navigate if we've already done it
    if (hasAutoNavigated) return;

    // Collect all relevant dates (new_date for moves, date for planned)
    const relevantDates: string[] = [];
    
    modifications.forEach((mod) => {
      if (mod.type === "planned" && mod.date) {
        relevantDates.push(mod.date);
      } else if (mod.new_date) {
        relevantDates.push(mod.new_date);
      }
    });

    if (relevantDates.length === 0) return;

    // Sort dates to find the most recent one
    relevantDates.sort((a, b) => new Date(b).getTime() - new Date(a).getTime());
    const mostRecentDate = new Date(relevantDates[0]);

    // Navigate to that month
    const targetYear = mostRecentDate.getFullYear();
    const targetMonth = mostRecentDate.getMonth();
    
    setCurrentDate(new Date(targetYear, targetMonth, 1));
    setHasAutoNavigated(true); // Mark that we've auto-navigated
  }, [modifications.length, hasAutoNavigated]); // Only depend on length, not the full array

  const transactionsByDate = useMemo(() => {
    const grouped: Record<string, Transaction[]> = {};
    
    // Apply modifications to transactions
    userData.added.forEach((transaction) => {
      const moved = movedTransactions.get(transaction.transaction_id);
      const dateToUse = moved ? moved.newDate : transaction.date;
      
      if (!grouped[dateToUse]) {
        grouped[dateToUse] = [];
      }
      grouped[dateToUse].push(transaction);
    });

    // Add planned transactions
    plannedTransactions.forEach((planned) => {
      if (planned.date) {
        if (!grouped[planned.date]) {
          grouped[planned.date] = [];
        }
        // Create a transaction-like object for planned transactions
        grouped[planned.date].push({
          transaction_id: planned.transaction_id,
          name: planned.merchant_name,
          merchant_name: planned.merchant_name,
          date: planned.date,
          amount: planned.amount,
          personal_finance_category: {
            primary: planned.category || "GENERAL_SERVICES",
            detailed: "",
          },
          account_id: "",
          authorized_date: planned.date,
          iso_currency_code: "USD",
          pending: false,
          payment_channel: "other",
          // Mark as planned for visual differentiation
          isPlanned: true,
        } as Transaction & { isPlanned?: boolean });
      }
    });

    return grouped;
  }, [movedTransactions, plannedTransactions]);

  const selectedTransactions = useMemo(() => {
    return selectedDate ? transactionsByDate[selectedDate] || [] : [];
  }, [selectedDate, transactionsByDate]);

  const calendarDays = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days: (Date | null)[] = [];

    // Add empty slots for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }

    // Add all days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }

    return days;
  }, [currentDate]);

  const goToPreviousMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1)
    );
  };

  const goToNextMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1)
    );
  };

  const formatDate = (date: Date): string => {
    return date.toISOString().split("T")[0];
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const getCategoryColor = (category: string): string => {
    return CATEGORY_COLORS[category] || "bg-gray-500/20 text-gray-300 border-gray-500/50";
  };

  const getTotalForDate = (date: Date): number => {
    const dateStr = formatDate(date);
    const transactions = transactionsByDate[dateStr] || [];
    return transactions.reduce((sum, t) => sum + t.amount, 0);
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      <ScrollArea className="flex-1">
        <div className="p-6">
          <Card className="flex flex-col rounded-3xl bg-slate-800/50 border-slate-700 overflow-hidden">
            {/* Month Navigation Header */}
            <div className="flex flex-col px-4 py-3 border-b border-slate-700/50 bg-slate-800/30">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-100">
                  {currentDate.toLocaleDateString("en-US", {
                    month: "long",
                    year: "numeric",
                  })}
                </h2>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={goToPreviousMonth}
                    className="bg-slate-700 border-slate-600 hover:bg-slate-600 rounded-2xl"
                  >
                    <ChevronLeft className="h-4 w-4 text-slate-200" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={goToNextMonth}
                    className="bg-slate-700 border-slate-600 hover:bg-slate-600 rounded-2xl"
                  >
                    <ChevronRight className="h-4 w-4 text-slate-200" />
                  </Button>
                </div>
              </div>
              
              {/* Legend */}
              {(modifications.length > 0) && (
                <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-700/30">
                  <span className="text-xs text-slate-400">Legend:</span>
                  <div className="flex items-center gap-1">
                    <ArrowRight className="h-3 w-3 text-cyan-400" />
                    <span className="text-xs text-slate-300">AI Optimized</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Sparkles className="h-3 w-3 text-purple-400" />
                    <span className="text-xs text-slate-300">Planned</span>
                  </div>
                  <div className="ml-auto">
                    <Badge className="bg-cyan-500/20 text-cyan-300 border-cyan-500/50">
                      {modifications.filter(m => m.type !== "planned").length} moved
                    </Badge>
                    <Badge className="ml-2 bg-purple-500/20 text-purple-300 border-purple-500/50">
                      {plannedTransactions.length} planned
                    </Badge>
                  </div>
                </div>
              )}
            </div>

            {/* Calendar Grid */}
            <div className="flex flex-col p-4">
              {/* Weekday Headers */}
              <div className="grid grid-cols-7 gap-2 mb-2">
                {WEEKDAYS.map((day) => (
                  <div
                    key={day}
                    className="text-center text-sm font-semibold text-slate-400 py-2"
                  >
                    {day}
                  </div>
                ))}
              </div>

              {/* Calendar Days */}
              <div className="grid grid-cols-7 gap-2">
            {calendarDays.map((date, index) => {
              if (!date) {
                return <div key={`empty-${index}`} className="min-h-[85px]" />;
              }

              const dateStr = formatDate(date);
              const transactions = transactionsByDate[dateStr] || [];
              const total = getTotalForDate(date);
              const isSelected = selectedDate === dateStr;
              
              // Check if any transactions on this date were moved here
              const hasMovedTransactions = transactions.some((t) =>
                movedTransactions.has(t.transaction_id)
              );
              
              // Check if any transactions are planned
              const hasPlannedTransactions = transactions.some(
                (t: Transaction & { isPlanned?: boolean }) => t.isPlanned
              );

              return (
                <Card
                  key={dateStr}
                  onClick={() => setSelectedDate(dateStr)}
                  className={`min-h-[85px] p-2 cursor-pointer transition-all overflow-hidden ${
                    isSelected
                      ? "bg-slate-700 border-slate-500 ring-2 ring-cyan-500"
                      : hasMovedTransactions
                      ? "bg-cyan-900/20 border-cyan-700/50 hover:bg-cyan-800/30"
                      : hasPlannedTransactions
                      ? "bg-purple-900/20 border-purple-700/50 hover:bg-purple-800/30"
                      : "bg-slate-800/30 border-slate-700 hover:bg-slate-700/50"
                  }`}
                >
                  <div className="flex flex-col h-full">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-sm font-semibold text-slate-200">
                        {date.getDate()}
                      </div>
                      {hasMovedTransactions && (
                        <ArrowRight className="h-3 w-3 text-cyan-400" />
                      )}
                      {hasPlannedTransactions && (
                        <Sparkles className="h-3 w-3 text-purple-400" />
                      )}
                    </div>
                    {transactions.length > 0 && (
                      <div className="flex-1 flex flex-col gap-1 overflow-hidden">
                        {transactions.map((transaction: Transaction & { isPlanned?: boolean }) => {
                          const isMoved = movedTransactions.has(transaction.transaction_id);
                          const isPlanned = transaction.isPlanned;
                          
                          return (
                            <div
                              key={transaction.transaction_id}
                              className={`text-[10px] px-1.5 py-0.5 rounded-2xl truncate ${
                                isMoved
                                  ? "bg-cyan-500/30 text-cyan-200 border border-cyan-400/50"
                                  : isPlanned
                                  ? "bg-purple-500/30 text-purple-200 border border-purple-400/50"
                                  : getCategoryColor(
                                      transaction.personal_finance_category.primary
                                    )
                              }`}
                              title={`${transaction.name} - ${formatCurrency(transaction.amount)}${
                                isMoved ? " (Moved)" : isPlanned ? " (Planned)" : ""
                              }`}
                            >
                              {isPlanned && "📅 "}
                              {transaction.merchant_name || transaction.name}
                            </div>
                          );
                        })}
                        {transactions.length > 0 && (
                          <div className={`text-[10px] font-bold mt-auto pt-1 border-t border-slate-600 ${
                            transactions.some(t => t.personal_finance_category.primary === "INCOME")
                              ? "text-green-400"
                              : "text-red-400"
                          }`}>
                            {formatCurrency(total)}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
              </div>
            </div>

            {/* Transaction Details Sidebar */}
            {selectedDate && selectedTransactions.length > 0 && (
              <div className="border-t border-slate-700">
                <Card className="m-4 bg-slate-700/50 border-slate-600 p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-semibold text-slate-100">
                      Transactions for{" "}
                      {new Date(selectedDate + "T00:00:00").toLocaleDateString("en-US", {
                        month: "long",
                        day: "numeric",
                      })}
                    </h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedDate(null)}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      Close
                    </Button>
                  </div>
                  <div className="max-h-[300px] rounded-xl overflow-y-auto">
                    <div className="space-y-2">
                      {selectedTransactions.map((transaction: Transaction & { isPlanned?: boolean }) => {
                        const moved = movedTransactions.get(transaction.transaction_id);
                        const isPlanned = transaction.isPlanned;
                        
                        return (
                          <Card
                            key={transaction.transaction_id}
                            className={`p-3 ${
                              moved
                                ? "bg-cyan-900/30 border-cyan-700/50"
                                : isPlanned
                                ? "bg-purple-900/30 border-purple-700/50"
                                : "bg-slate-800/50 border-slate-700"
                            }`}
                          >
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <div className="font-medium text-slate-100 flex items-center gap-2">
                                  {transaction.name}
                                  {moved && (
                                    <Badge className="bg-cyan-500/20 text-cyan-300 border-cyan-500/50">
                                      Moved
                                    </Badge>
                                  )}
                                  {isPlanned && (
                                    <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/50">
                                      Planned
                                    </Badge>
                                  )}
                                </div>
                                <div className="text-sm text-slate-400">
                                  {transaction.merchant_name}
                                </div>
                                {moved && (
                                  <div className="mt-2 text-xs text-cyan-300 bg-cyan-900/20 p-2 rounded border border-cyan-700/30">
                                    <div className="flex items-center gap-1 mb-1">
                                      <ArrowRight className="h-3 w-3" />
                                      <span className="font-semibold">
                                        Moved from {new Date(moved.originalDate + "T00:00:00").toLocaleDateString("en-US", {
                                          month: "short",
                                          day: "numeric",
                                        })}
                                      </span>
                                    </div>
                                    <div className="text-slate-400">{moved.reason}</div>
                                  </div>
                                )}
                                <Badge
                                  className={`mt-2 ${getCategoryColor(
                                    transaction.personal_finance_category.primary
                                  )}`}
                                  variant="outline"
                                >
                                  {transaction.personal_finance_category.primary.replace(
                                    /_/g,
                                    " "
                                  )}
                                </Badge>
                              </div>
                              <div className={`text-lg font-bold ${
                                transaction.personal_finance_category.primary === "INCOME"
                                  ? "text-green-400"
                                  : "text-red-400"
                              }`}>
                                {transaction.personal_finance_category.primary === "INCOME" ? "+" : "-"}
                                {formatCurrency(transaction.amount)}
                              </div>
                            </div>
                          </Card>
                        );
                      })}
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </Card>
        </div>
      </ScrollArea>

      {/* Global styles to round session/select controls.
          Apply className="session-select" to your session dropdown component
          if you want to target it explicitly. */}
      <style jsx global>{`
        /* explicit class you can add to the session select component */
        .session-select,
        .session-select .trigger,
        .session-select .select-trigger {
          border-radius: 0.75rem !important;
          overflow: hidden;
        }

        /* generic fallbacks to catch common select/combobox implementations */
        select,
        [role="combobox"],
        .select,
        .SelectTrigger,
        .trigger {
          border-radius: 0.75rem !important;
        }
      `}</style>
    </div>
  );
}

