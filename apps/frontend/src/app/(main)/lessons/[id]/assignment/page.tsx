"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, Circle, ClipboardList, Loader2, XCircle } from "lucide-react";

import { Lesson } from "@/lib/api/lessons";
import { assignmentApi, chatbotApi, courseApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth/store";
import { Assignment, AssignmentQuestionType, AssignmentType, CourseDetail, Submission, UserRole } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChatbotStore } from "@/components/chat/store";
import { QuestionNavigator, QuestionPageSize } from "@/components/assignments/QuestionNavigator";
import { RichContent } from "@/components/content/RichContent";

interface AssignmentLessonContext {
  id: string;
  title: string;
  course_id?: string;
}

export default function LessonAssignmentPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useAuthStore();
  const lessonId = params.id as string;
  const assignmentId = searchParams.get("assignmentId");
  const courseId = searchParams.get("courseId");
  const courseSlug = searchParams.get("courseSlug");
  const lessonTitle = searchParams.get("lessonTitle") || "Bài học";

  const [lesson, setLesson] = useState<AssignmentLessonContext | null>(null);
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [textAnswers, setTextAnswers] = useState<Record<string, string>>({});
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [score, setScore] = useState<{ correct: number; total: number; percent: number } | null>(null);
  const [questionPageSize, setQuestionPageSize] = useState<QuestionPageSize>("1");
  const [currentQuestionPage, setCurrentQuestionPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isLearner = user?.role === UserRole.LEARNER;
  const canAssignWork = user?.role === UserRole.INSTRUCTOR || user?.role === UserRole.ADMIN;

  useEffect(() => {
    const fetchData = async () => {
      try {
        let lessonData: Lesson | undefined;

        if (courseId) {
          try {
            const courseData = await courseApi.getById(courseId);
            setCourse(courseData);

            const assignments = await assignmentApi.listByCourse(courseData.id, canAssignWork);
            const lessonAssignments = assignments
              .filter((item) => item.lesson_id === lessonId)
              .sort((a, b) => a.order_index - b.order_index);

            const selectedAssignment = assignmentId
              ? lessonAssignments.find((item) => item.id === assignmentId)
              : isLearner
                ? lessonAssignments.find((item) => item.is_published) || lessonAssignments[0]
                : lessonAssignments[0];

            setAssignment(selectedAssignment || null);

            try {
              const lessons = await courseApi.getLessons(courseData.id);
              lessonData = (lessons as Lesson[]).find((item) => item.id === lessonId);
            } catch {
              // Fall back to query context.
            }
          } catch {
            // Optional for breadcrumbs.
          }
        }

        setLesson({
          id: lessonId,
          title: lessonData?.title || lessonTitle,
          course_id: lessonData?.course_id || courseId || undefined,
        });
      } catch (err: any) {
        setError(err.response?.data?.detail || "Không thể mở trang bài tập");
      } finally {
        setIsLoading(false);
      }
    };

    if (lessonId) {
      fetchData();
    }
  }, [lessonId, assignmentId, courseId, lessonTitle, canAssignWork, isLearner]);

  useEffect(() => {
    setSelectedAnswers({});
    setTextAnswers({});
    setSubmission(null);
    setIsSubmitted(false);
    setScore(null);
    setCurrentQuestionPage(1);
    useChatbotStore.getState().reset();
  }, [assignment?.id]);

  useEffect(() => {
    if (!assignment?.id || !isLearner || assignment.assignment_type === AssignmentType.TEST) return;

    chatbotApi.preloadAssignment({ assignment_id: assignment.id }).catch((preloadError) => {
      console.debug("Assignment chatbot context preload skipped:", preloadError);
    });
  }, [assignment?.id, assignment?.assignment_type, isLearner]);

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
        const correct = (savedSubmission.answers || []).filter((answer) => answer.is_correct).length;
        setSelectedAnswers(restoredSelectedAnswers);
        setTextAnswers(restoredTextAnswers);
        setSubmission(savedSubmission);
        setScore({
          correct,
          total: assignment.questions.length,
          percent: Math.round(Number(savedSubmission.score || 0)),
        });
        setIsSubmitted(true);
      })
      .catch((submissionError) => {
        if (submissionError?.response?.status !== 404) {
          console.debug("Saved submission load skipped:", submissionError);
        }
      });
  }, [assignment?.id, assignment?.questions.length, isLearner]);

  const orderedQuestions = useMemo(
    () => [...(assignment?.questions || [])].sort((a, b) => a.order_index - b.order_index),
    [assignment?.questions]
  );
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
  const submissionAnswersByQuestion = new Map((submission?.answers || []).map((answer) => [answer.question_id, answer]));

  useEffect(() => {
    if (currentQuestionPage > totalQuestionPages) {
      setCurrentQuestionPage(totalQuestionPages);
    }
  }, [currentQuestionPage, totalQuestionPages]);

  const handleChooseAnswer = (questionId: string, optionId: string) => {
    if (isSubmitted) return;
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
  };

  const scrollToQuestion = (questionId?: string) => {
    window.setTimeout(() => {
      const target = questionId
        ? document.getElementById(`assignment-question-${questionId}`)
        : document.getElementById("assignment-question-list");
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
    if (!assignment || orderedQuestions.length === 0) return;

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
      const correct = (result.answers || []).filter((answer) => answer.is_correct).length;
      const percent = Math.round(Number(result.score || 0));
      setSubmission(result);
      setScore({ correct, total: orderedQuestions.length, percent });
      setIsSubmitted(true);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Nộp bài thất bại");
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
      setIsSubmitted(false);
      setScore(null);
      setCurrentQuestionPage(1);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Không thể xóa kết quả bài làm");
    } finally {
      setIsResetting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <Card className="p-10 text-center">
        <CardTitle className="mb-3">Không thể mở bài tập</CardTitle>
        <CardDescription className="mb-4">{error || "Bài học không tồn tại"}</CardDescription>
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
        {!course && courseSlug && <Link href={`/courses/${courseSlug}`}>Khóa học</Link>}
        {(course || courseSlug) && <span>&gt;</span>}
        <span>{lesson.title}</span>
        <span>&gt;</span>
        <span className="text-foreground font-medium">Bài tập</span>
      </div>

      <div
        className={
          assignment?.assignment_type === AssignmentType.TEST
            ? "grid grid-cols-1 gap-6"
            : "grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_380px] 2xl:grid-cols-[minmax(0,1fr)_420px]"
        }
      >
        <Card className="min-w-0">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5" />
              Khu vực làm bài tập
            </CardTitle>
            <CardDescription>
              {assignment
                ? `Bài tập: ${assignment.title}`
                : canAssignWork
                  ? "Lesson này chưa có bài tập. Hãy giao bài tập từ trang khóa học."
                  : "Bài tập cho lesson này chưa được tạo bởi giáo viên hoặc admin."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {assignment && isLearner ? (
              <>
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

                {isSubmitted && score && (
                  <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm">
                    <p className="font-medium text-emerald-900">
                      Kết quả: {score.correct}/{score.total} câu đúng ({score.percent}%)
                    </p>
                  </div>
                )}

                <div id="assignment-question-list" className="space-y-4 scroll-mt-6">
                  {visibleQuestions.map((question) => {
                    const questionIndex = orderedQuestions.findIndex((item) => item.id === question.id);
                    const sortedOptions = [...question.options].sort((a, b) => a.order_index - b.order_index);
                    const selectedOptionId = selectedAnswers[question.id];
                    const submittedAnswer = submissionAnswersByQuestion.get(question.id);

                    return (
                      <div
                        key={question.id}
                        id={`assignment-question-${question.id}`}
                        className="rounded-lg border border-slate-200 p-4 space-y-3 scroll-mt-6"
                      >
                        <div className="text-sm font-semibold text-foreground">
                          <span className="mr-1">Câu {questionIndex + 1}.</span>
                          <RichContent value={question.question_text} inline />
                        </div>

                        {question.question_type === AssignmentQuestionType.ESSAY ? (
                          <Textarea
                            value={textAnswers[question.id] || ""}
                            disabled={isSubmitted}
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
                                  disabled={isSubmitted}
                                  onClick={() => handleChooseAnswer(question.id, option.id)}
                                  className={`w-full rounded-md border px-3 py-2 text-left text-sm flex items-center justify-between gap-2 transition-colors ${optionClasses} ${isSubmitted ? "cursor-default" : "cursor-pointer"}`}
                                >
                                  <span>
                                    {String.fromCharCode(65 + optionIndex)}.{" "}
                                    <RichContent value={option.option_text} inline />
                                  </span>
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

                        {isSubmitted && submittedAnswer && (
                          <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
                            {submittedAnswer.correct_answer_text && (
                              <p className="font-medium text-slate-900">
                                Đáp án chuẩn:{" "}
                                <RichContent value={submittedAnswer.correct_answer_text} inline />
                              </p>
                            )}
                            {submittedAnswer.explanation && (
                              <RichContent value={submittedAnswer.explanation} className="mt-1 text-slate-700" />
                            )}
                            {submittedAnswer.feedback && (
                              <RichContent value={submittedAnswer.feedback} className="mt-1 text-muted-foreground" />
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    onClick={handleSubmit}
                    disabled={isSubmitted || isSubmitting || answeredCount !== totalQuestionCount || totalQuestionCount === 0}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Đang nộp...
                      </>
                    ) : (
                      "Nộp bài"
                    )}
                  </Button>
                  {isSubmitted && (
                    <Button
                      variant="outline"
                      onClick={handleRetake}
                      disabled={isResetting}
                    >
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
              </>
            ) : assignment && canAssignWork ? (
              <p className="text-sm text-muted-foreground">
                Bạn đang ở vai trò giảng viên/admin. Học sinh sẽ làm bài tại trang này, còn bạn giao bài tập từ màn hình chi tiết khóa học.
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                {canAssignWork
                  ? "Lesson này chưa có bài tập. Hãy quay lại khóa học để tạo assignment cho lesson này."
                  : "Giáo viên hoặc admin cần tạo assignment cho lesson này trước khi học sinh có thể truy cập trang làm bài."}
              </p>
            )}
            <Button asChild variant="outline">
              <Link href={course ? `/courses/${course.slug}` : courseSlug ? `/courses/${courseSlug}` : "/courses"}>Quay về nội dung khóa học</Link>
            </Button>
          </CardContent>
        </Card>

        {assignment && assignment.assignment_type !== AssignmentType.TEST && (
          <aside className="min-h-[560px] xl:sticky xl:top-6 xl:h-[calc(100vh-8rem)]">
            <ChatWindow
              mode="assignment"
              courseId={course?.id || courseId || undefined}
              lessonId={lesson.id}
              lessonTitle={lesson.title}
              assignmentId={assignment.id}
              assignmentTitle={assignment.title}
              fitContainer={true}
              className="h-full"
            />
          </aside>
        )}
      </div>
    </div>
  );
}
