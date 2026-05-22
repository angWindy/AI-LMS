"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, Circle, ClipboardCheck, Loader2, XCircle } from "lucide-react";

import { assignmentApi, courseApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth/store";
import { Assignment, AssignmentQuestionType, CourseDetail, Submission, UserRole } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { QuestionNavigator, QuestionPageSize } from "@/components/assignments/QuestionNavigator";

export default function CourseTestPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuthStore();
  const slug = params.slug as string;
  const assignmentId = params.assignmentId as string;

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [textAnswers, setTextAnswers] = useState<Record<string, string>>({});
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [questionPageSize, setQuestionPageSize] = useState<QuestionPageSize>("1");
  const [currentQuestionPage, setCurrentQuestionPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isLearner = user?.role === UserRole.LEARNER;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [courseData, assignmentData] = await Promise.all([
          courseApi.getBySlug(slug),
          assignmentApi.getById(assignmentId),
        ]);
        setCourse(courseData);
        setAssignment(assignmentData);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Không thể mở bài kiểm tra");
      } finally {
        setIsLoading(false);
      }
    };

    if (slug && assignmentId) {
      fetchData();
    }
  }, [slug, assignmentId]);

  useEffect(() => {
    if (!assignment?.id || !isLearner) return;

    assignmentApi.getMySubmission(assignment.id)
      .then((savedSubmission) => {
        const restoredSelectedAnswers: Record<string, string> = {};
        const restoredTextAnswers: Record<string, string> = {};
        for (const answer of savedSubmission.answers || []) {
          if (answer.selected_option_id) {
            restoredSelectedAnswers[answer.question_id] = answer.selected_option_id;
          }
          if (answer.answer_text) {
            restoredTextAnswers[answer.question_id] = answer.answer_text;
          }
        }
        setSelectedAnswers(restoredSelectedAnswers);
        setTextAnswers(restoredTextAnswers);
        setSubmission(savedSubmission);
      })
      .catch((submissionError) => {
        if (submissionError?.response?.status !== 404) {
          console.debug("Saved test submission load skipped:", submissionError);
        }
      });
  }, [assignment?.id, isLearner]);

  const orderedQuestions = useMemo(
    () => [...(assignment?.questions || [])].sort((a, b) => a.order_index - b.order_index),
    [assignment?.questions]
  );
  const submissionAnswersByQuestion = new Map((submission?.answers || []).map((answer) => [answer.question_id, answer]));
  const answeredCount = orderedQuestions.reduce((count, question) => {
    if (question.question_type === AssignmentQuestionType.ESSAY) {
      return textAnswers[question.id]?.trim() ? count + 1 : count;
    }
    return selectedAnswers[question.id] ? count + 1 : count;
  }, 0);
  const totalQuestionCount = orderedQuestions.length;
  const totalQuestionPages =
    questionPageSize === "all"
      ? 1
      : Math.max(1, Math.ceil(totalQuestionCount / Number(questionPageSize)));
  const visibleStart =
    questionPageSize === "all"
      ? 0
      : (Math.min(currentQuestionPage, totalQuestionPages) - 1) * Number(questionPageSize);
  const visibleEnd =
    questionPageSize === "all"
      ? totalQuestionCount
      : Math.min(visibleStart + Number(questionPageSize), totalQuestionCount);
  const visibleQuestions =
    questionPageSize === "all" ? orderedQuestions : orderedQuestions.slice(visibleStart, visibleEnd);
  const questionNavigatorItems = orderedQuestions.map((question) => ({
    id: question.id,
    isAnswered:
      question.question_type === AssignmentQuestionType.ESSAY
        ? Boolean(textAnswers[question.id]?.trim())
        : Boolean(selectedAnswers[question.id]),
  }));

  useEffect(() => {
    if (currentQuestionPage > totalQuestionPages) {
      setCurrentQuestionPage(totalQuestionPages);
    }
  }, [currentQuestionPage, totalQuestionPages]);

  useEffect(() => {
    setCurrentQuestionPage(1);
  }, [assignment?.id]);

  const scrollToQuestion = (questionId?: string) => {
    window.setTimeout(() => {
      const target = questionId
        ? document.getElementById(`test-question-${questionId}`)
        : document.getElementById("test-question-list");
      target?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 0);
  };

  const handleQuestionPageChange = (page: number) => {
    setCurrentQuestionPage(page);
    scrollToQuestion();
  };

  const handleQuestionPageSizeChange = (pageSize: QuestionPageSize) => {
    setQuestionPageSize(pageSize);
    setCurrentQuestionPage(1);
    scrollToQuestion();
  };

  const handleQuestionJump = (questionIndex: number) => {
    const question = orderedQuestions[questionIndex];
    if (!question) return;

    if (questionPageSize !== "all") {
      setCurrentQuestionPage(Math.floor(questionIndex / Number(questionPageSize)) + 1);
    }
    scrollToQuestion(question.id);
  };

  const handleSubmit = async () => {
    if (!assignment) return;
    setIsSubmitting(true);
    try {
      const result = await assignmentApi.submit(assignment.id, {
        answers: orderedQuestions.map((question) => ({
          question_id: question.id,
          selected_option_id:
            question.question_type === AssignmentQuestionType.MULTIPLE_CHOICE
              ? selectedAnswers[question.id]
              : undefined,
          answer_text:
            question.question_type === AssignmentQuestionType.ESSAY
              ? textAnswers[question.id]?.trim()
              : undefined,
        })),
      });
      setSubmission(result);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Nộp bài kiểm tra thất bại");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetake = async () => {
    if (!assignment) return;

    setIsResetting(true);
    try {
      await assignmentApi.resetMySubmission(assignment.id);
      setSelectedAnswers({});
      setTextAnswers({});
      setSubmission(null);
      setCurrentQuestionPage(1);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Không thể xóa kết quả bài kiểm tra");
    } finally {
      setIsResetting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !assignment) {
    return (
      <Card className="p-10 text-center">
        <CardTitle className="mb-3">Không thể mở bài kiểm tra</CardTitle>
        <CardDescription className="mb-4">{error || "Bài kiểm tra không tồn tại"}</CardDescription>
        <Button onClick={() => router.back()}>Quay lại</Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        {course && <Link href={`/courses/${course.slug}`}>{course.title}</Link>}
        <span>&gt;</span>
        <span className="font-medium text-foreground">Bài kiểm tra</span>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ClipboardCheck className="h-5 w-5" />
            {assignment.title}
          </CardTitle>
          <CardDescription>
            {isLearner
              ? "Trang bài kiểm tra không có chatbot hỗ trợ."
              : "Bạn đang xem bài kiểm tra ở vai trò giảng viên/admin."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <QuestionNavigator
            questions={questionNavigatorItems}
            answeredCount={answeredCount}
            pageSize={questionPageSize}
            currentPage={currentQuestionPage}
            totalPages={totalQuestionPages}
            visibleStart={visibleStart}
            visibleEnd={visibleEnd}
            onPageSizeChange={handleQuestionPageSizeChange}
            onPageChange={handleQuestionPageChange}
            onQuestionClick={handleQuestionJump}
          />

          {submission && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm">
              <p className="font-medium text-emerald-900">Kết quả: {Number(submission.score || 0).toFixed(0)}%</p>
              {submission.feedback && <p className="mt-1 text-emerald-800">{submission.feedback}</p>}
            </div>
          )}

          <div id="test-question-list" className="space-y-4 scroll-mt-6">
            {visibleQuestions.map((question) => {
              const questionIndex = orderedQuestions.findIndex((item) => item.id === question.id);
              const sortedOptions = [...question.options].sort((a, b) => a.order_index - b.order_index);
              const selectedOptionId = selectedAnswers[question.id];
              const submittedAnswer = submissionAnswersByQuestion.get(question.id);
              const isSubmitted = !!submission;

              return (
                <div
                  key={question.id}
                  id={`test-question-${question.id}`}
                  className="space-y-3 rounded-lg border border-slate-200 p-4 scroll-mt-6"
                >
                  <p className="text-sm font-semibold text-foreground">
                    Câu {questionIndex + 1}. {question.question_text}
                  </p>

                  {question.question_type === AssignmentQuestionType.ESSAY ? (
                    <Textarea
                      value={textAnswers[question.id] || ""}
                      disabled={isSubmitted || !isLearner}
                      rows={5}
                      onChange={(event) =>
                        setTextAnswers((prev) => ({
                          ...prev,
                          [question.id]: event.target.value,
                        }))
                      }
                      placeholder="Nhập câu trả lời tự luận"
                    />
                  ) : (
                    <div className="space-y-2">
                      {sortedOptions.map((option, optionIndex) => {
                        const isSelected = selectedOptionId === option.id;
                        const isSelectedCorrect = isSubmitted && isSelected && submittedAnswer?.is_correct;
                        const showIncorrect = isSubmitted && isSelected && submittedAnswer?.is_correct === false;
                        const optionClasses = isSelectedCorrect
                          ? "border-emerald-300 bg-emerald-50"
                          : showIncorrect
                            ? "border-red-300 bg-red-50"
                            : isSelected
                              ? "border-primary bg-primary/5"
                              : "border-slate-200 bg-white hover:bg-slate-50";

                        return (
                          <button
                            key={option.id}
                            type="button"
                            disabled={isSubmitted || !isLearner}
                            onClick={() => setSelectedAnswers((prev) => ({ ...prev, [question.id]: option.id }))}
                            className={`flex w-full items-center justify-between gap-2 rounded-md border px-3 py-2 text-left text-sm transition-colors ${optionClasses}`}
                          >
                            <span>{String.fromCharCode(65 + optionIndex)}. {option.option_text}</span>
                            {isSelectedCorrect ? (
                              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                            ) : showIncorrect ? (
                              <XCircle className="h-4 w-4 text-red-600" />
                            ) : isSelected ? (
                              <Circle className="h-4 w-4 text-primary" />
                            ) : null}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {submittedAnswer && (
                    <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
                      {submittedAnswer.correct_answer_text && (
                        <p className="font-medium text-slate-900">Đáp án chuẩn: {submittedAnswer.correct_answer_text}</p>
                      )}
                      {submittedAnswer.explanation && <p className="mt-1 text-slate-700">{submittedAnswer.explanation}</p>}
                      {submittedAnswer.feedback && <p className="mt-1 text-muted-foreground">{submittedAnswer.feedback}</p>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {isLearner && (
            <div className="flex items-center gap-2">
              <Button
                onClick={handleSubmit}
                disabled={!!submission || isSubmitting || answeredCount !== totalQuestionCount || totalQuestionCount === 0}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Đang nộp...
                  </>
                ) : (
                  "Nộp bài kiểm tra"
                )}
              </Button>
              {submission && (
                <Button variant="outline" onClick={handleRetake} disabled={isResetting}>
                  {isResetting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Đang xóa...
                    </>
                  ) : (
                    "Làm lại"
                  )}
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
