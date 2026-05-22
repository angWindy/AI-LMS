"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type QuestionPageSize = "1" | "5" | "all";

export interface QuestionNavigatorItem {
  id: string;
  isAnswered: boolean;
}

interface QuestionNavigatorProps {
  questions: QuestionNavigatorItem[];
  answeredCount: number;
  pageSize: QuestionPageSize;
  currentPage: number;
  totalPages: number;
  visibleStart: number;
  visibleEnd: number;
  onPageSizeChange: (pageSize: QuestionPageSize) => void;
  onPageChange: (page: number) => void;
  onQuestionClick: (questionIndex: number) => void;
  className?: string;
}

export function QuestionNavigator({
  questions,
  answeredCount,
  pageSize,
  currentPage,
  totalPages,
  visibleStart,
  visibleEnd,
  onPageSizeChange,
  onPageChange,
  onQuestionClick,
  className,
}: QuestionNavigatorProps) {
  const totalQuestions = questions.length;

  return (
    <div className={`rounded-lg border border-slate-200 bg-slate-50/70 p-3 ${className || ""}`}>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-[220px]">
          <p className="text-sm font-medium text-slate-900">
            Đã trả lời {answeredCount}/{totalQuestions} câu hỏi
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Đang hiển thị {totalQuestions === 0 ? 0 : visibleStart + 1}-{visibleEnd} / {totalQuestions} câu.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Select value={pageSize} onValueChange={(value) => onPageSizeChange(value as QuestionPageSize)}>
            <SelectTrigger className="h-9 w-[150px] bg-white">
              <SelectValue placeholder="Số câu/trang" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1 câu/trang</SelectItem>
              <SelectItem value="5">5 câu/trang</SelectItem>
              <SelectItem value="all">Tất cả</SelectItem>
            </SelectContent>
          </Select>

          {pageSize !== "all" && (
            <div className="flex items-center gap-1">
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-9 w-9 bg-white"
                disabled={currentPage <= 1}
                onClick={() => onPageChange(currentPage - 1)}
                aria-label="Trang trước"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="min-w-[72px] text-center text-sm text-muted-foreground">
                {currentPage}/{Math.max(totalPages, 1)}
              </span>
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-9 w-9 bg-white"
                disabled={currentPage >= totalPages}
                onClick={() => onPageChange(currentPage + 1)}
                aria-label="Trang sau"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        <div className="grid grid-cols-5 gap-1.5 self-start lg:grid-cols-10 lg:justify-items-end">
          {questions.map((question, index) => {
            const isVisible = index >= visibleStart && index < visibleEnd;
            const statusClasses = question.isAnswered
              ? "border-emerald-400 bg-emerald-500 text-white hover:bg-emerald-600"
              : "border-slate-300 bg-white text-slate-700 hover:bg-slate-100";
            const visibleClasses = isVisible ? "ring-2 ring-primary/40 ring-offset-1" : "";

            return (
              <button
                key={question.id}
                type="button"
                onClick={() => onQuestionClick(index)}
                className={`flex h-7 w-7 items-center justify-center rounded-full border text-[11px] font-semibold leading-none transition-colors ${statusClasses} ${visibleClasses}`}
                aria-label={`Chuyển đến câu ${index + 1}${question.isAnswered ? ", đã làm" : ", chưa làm"}`}
              >
                {index + 1}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
