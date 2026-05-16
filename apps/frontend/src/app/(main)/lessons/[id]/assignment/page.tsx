"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, Circle, ClipboardList, Loader2, XCircle } from "lucide-react";

import { Lesson } from "@/lib/api/lessons";
import { assignmentApi, chatbotApi, courseApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth/store";
import { Assignment, CourseDetail, UserRole } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChatbotStore } from "@/components/chat/store";

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
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [score, setScore] = useState<{ correct: number; total: number; percent: number } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
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
    setIsSubmitted(false);
    setScore(null);
    useChatbotStore.getState().reset();
  }, [assignment?.id]);

  useEffect(() => {
    if (!assignment?.id || !isLearner) return;

    chatbotApi.preloadAssignment({ assignment_id: assignment.id }).catch((preloadError) => {
      console.debug("Assignment chatbot context preload skipped:", preloadError);
    });
  }, [assignment?.id, isLearner]);

  const orderedQuestions = [...(assignment?.questions || [])].sort((a, b) => a.order_index - b.order_index);
  const answeredCount = Object.keys(selectedAnswers).length;
  const totalQuestionCount = orderedQuestions.length;

  const handleChooseAnswer = (questionId: string, optionId: string) => {
    if (isSubmitted) return;
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
  };

  const handleSubmit = () => {
    if (!assignment || orderedQuestions.length === 0) return;

    const correct = orderedQuestions.reduce((acc, question) => {
      const selectedOptionId = selectedAnswers[question.id];
      if (!selectedOptionId) return acc;

      const selectedOption = question.options.find((option) => option.id === selectedOptionId);
      return selectedOption?.is_correct ? acc + 1 : acc;
    }, 0);

    const total = orderedQuestions.length;
    const percent = Math.round((correct / total) * 100);

    setScore({ correct, total, percent });
    setIsSubmitted(true);
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

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_380px] 2xl:grid-cols-[minmax(0,1fr)_420px]">
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
                <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-3 text-sm text-muted-foreground">
                  <p>
                    Đã trả lời {answeredCount}/{totalQuestionCount} câu hỏi.
                  </p>
                  {isSubmitted && score && (
                    <p className="mt-1 font-medium text-foreground">
                      Kết quả: {score.correct}/{score.total} câu đúng ({score.percent}%)
                    </p>
                  )}
                </div>

                <div className="space-y-4">
                  {orderedQuestions.map((question, questionIndex) => {
                    const sortedOptions = [...question.options].sort((a, b) => a.order_index - b.order_index);
                    const selectedOptionId = selectedAnswers[question.id];

                    return (
                      <div key={question.id} className="rounded-lg border border-slate-200 p-4 space-y-3">
                        <p className="text-sm font-semibold text-foreground">
                          Câu {questionIndex + 1}. {question.question_text}
                        </p>

                        <div className="space-y-2">
                          {sortedOptions.map((option, optionIndex) => {
                            const isSelected = selectedOptionId === option.id;
                            const showCorrect = isSubmitted && option.is_correct;
                            const showIncorrect = isSubmitted && isSelected && !option.is_correct;

                            const optionClasses = showCorrect
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
                                  {String.fromCharCode(65 + optionIndex)}. {option.option_text}
                                </span>
                                {showCorrect ? (
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

                      </div>
                    );
                  })}
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    onClick={handleSubmit}
                    disabled={isSubmitted || answeredCount !== totalQuestionCount || totalQuestionCount === 0}
                  >
                    Nộp bài
                  </Button>
                  {isSubmitted && (
                    <Button
                      variant="outline"
                      onClick={() => {
                        setSelectedAnswers({});
                        setIsSubmitted(false);
                        setScore(null);
                      }}
                    >
                      Làm lại
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

        {assignment && (
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
