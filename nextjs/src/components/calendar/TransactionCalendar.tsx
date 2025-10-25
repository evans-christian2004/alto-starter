"use client";

import React, { useState, useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { userData, type Transaction } from "@/data/userData";

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
  const [currentDate, setCurrentDate] = useState(new Date(2023, 8, 1)); // September 2023
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const transactionsByDate = useMemo(() => {
    const grouped: Record<string, Transaction[]> = {};
    userData.added.forEach((transaction) => {
      if (!grouped[transaction.date]) {
        grouped[transaction.date] = [];
      }
      grouped[transaction.date].push(transaction);
    });
    return grouped;
  }, []);

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
          <Card className="flex flex-col bg-slate-800/50 border-slate-700">
            {/* Month Navigation Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50 bg-slate-800/30">
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
                  className="bg-slate-700 border-slate-600 hover:bg-slate-600"
                >
                  <ChevronLeft className="h-4 w-4 text-slate-200" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={goToNextMonth}
                  className="bg-slate-700 border-slate-600 hover:bg-slate-600"
                >
                  <ChevronRight className="h-4 w-4 text-slate-200" />
                </Button>
              </div>
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
                return <div key={`empty-${index}`} className="min-h-[70px]" />;
              }

              const dateStr = formatDate(date);
              const transactions = transactionsByDate[dateStr] || [];
              const total = getTotalForDate(date);
              const isSelected = selectedDate === dateStr;

              return (
                <Card
                  key={dateStr}
                  onClick={() => setSelectedDate(dateStr)}
                  className={`min-h-[70px] p-2 cursor-pointer transition-all overflow-hidden ${
                    isSelected
                      ? "bg-slate-700 border-slate-500 ring-2 ring-blue-500"
                      : "bg-slate-800/30 border-slate-700 hover:bg-slate-700/50"
                  }`}
                >
                  <div className="flex flex-col h-full">
                    <div className="text-sm font-semibold text-slate-200 mb-2">
                      {date.getDate()}
                    </div>
                    {transactions.length > 0 && (
                      <div className="flex-1 flex flex-col gap-1 overflow-hidden">
                        {transactions.map((transaction, idx) => (
                          <div
                            key={transaction.transaction_id}
                            className={`text-[10px] px-1.5 py-0.5 rounded truncate ${getCategoryColor(
                              transaction.personal_finance_category.primary
                            )}`}
                            title={`${transaction.name} - ${formatCurrency(transaction.amount)}`}
                          >
                            {transaction.merchant_name || transaction.name}
                          </div>
                        ))}
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
                  <div className="max-h-[300px] overflow-y-auto">
                    <div className="space-y-2">
                      {selectedTransactions.map((transaction) => (
                        <Card
                          key={transaction.transaction_id}
                          className="p-3 bg-slate-800/50 border-slate-700"
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="font-medium text-slate-100">
                                {transaction.name}
                              </div>
                              <div className="text-sm text-slate-400">
                                {transaction.merchant_name}
                              </div>
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
                      ))}
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}

