"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Edit3,
  Loader2,
  Plus,
  Sparkles,
  Trash2,
} from "lucide-react";

import { courseApi, Lesson, questionBankApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth/store";
import {
  QuestionBankCourse,
  QuestionBankQuestion,
  QuestionDifficulty,
  QuestionPurposeType,
  UserRole,
} from "@/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const ALL_LESSONS_VALUE = "all";

const difficultyLabels: Record<QuestionDifficulty, string> = {
  [QuestionDifficulty.EASY]: "Dễ",
  [QuestionDifficulty.MEDIUM]: "Trung bình",
  [QuestionDifficulty.HARD]: "Khó",
};

const purposeLabels: Record<QuestionPurposeType, string> = {
  [QuestionPurposeType.PRACTICE]: "Luyện tập",
  [QuestionPurposeType.ASSESSMENT]: "Kiểm tra",
  [QuestionPurposeType.SHARED]: "Dùng chung",
};

interface QuestionEditorState {
  lesson_id: string | null;
  question_text: string;
  explanation: string;
  difficulty: QuestionDifficulty;
  purpose_type: QuestionPurposeType;
  options: string[];
  correctIndex: number;
}

export default function QuestionBankPage() {
  const { user } = useAuthStore();
  const [courses, setCourses] = useState<QuestionBankCourse[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [questions, setQuestions] = useState<QuestionBankQuestion[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [selectedLessonId, setSelectedLessonId] = useState(ALL_LESSONS_VALUE);
  const [expandedQuestionIds, setExpandedQuestionIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isQuestionsLoading, setIsQuestionsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [showEditorDialog, setShowEditorDialog] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<QuestionBankQuestion | null>(null);
  const [editor, setEditor] = useState<QuestionEditorState>(() => createDefaultEditor(null));
  const [isSavingQuestion, setIsSavingQuestion] = useState(false);

  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [generateLessonId, setGenerateLessonId] = useState("");
  const [generateCount, setGenerateCount] = useState(5);
  const [generateDifficulty, setGenerateDifficulty] = useState<QuestionDifficulty>(QuestionDifficulty.EASY);
  const [generatePurpose, setGeneratePurpose] = useState<QuestionPurposeType>(QuestionPurposeType.SHARED);
  const [isGenerating, setIsGenerating] = useState(false);

  const canManage = user?.role === UserRole.ADMIN || user?.role === UserRole.INSTRUCTOR;

  const selectedCourse = useMemo(
    () => courses.find((course) => course.id === selectedCourseId) || null,
    [courses, selectedCourseId]
  );

  function createDefaultEditor(lessonId: string | null): QuestionEditorState {
    return {
      lesson_id: lessonId,
      question_text: "",
      explanation: "",
      difficulty: QuestionDifficulty.EASY,
      purpose_type: QuestionPurposeType.SHARED,
      options: ["", "", "", ""],
      correctIndex: 0,
    };
  }

  const loadCourses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const courseData = await questionBankApi.listCourses();
      setCourses(courseData);
      setSelectedCourseId((prev) => prev || courseData[0]?.id || "");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Không thể tải danh sách khóa học");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadLessons = useCallback(async (courseId: string) => {
    if (!courseId) {
      setLessons([]);
      return;
    }

    try {
      const lessonData = (await courseApi.getLessons(courseId)) as Lesson[];
      setLessons(lessonData);
      setGenerateLessonId((prev) => prev || lessonData[0]?.id || "");
    } catch {
      setLessons([]);
      setGenerateLessonId("");
    }
  }, []);

  const loadQuestions = useCallback(async () => {
    setIsQuestionsLoading(true);
    try {
      const questionData = await questionBankApi.listQuestions({
        course_id: selectedCourseId || undefined,
        lesson_id: selectedLessonId === ALL_LESSONS_VALUE ? undefined : selectedLessonId,
      });
      setQuestions(questionData);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Không thể tải ngân hàng câu hỏi");
    } finally {
      setIsQuestionsLoading(false);
    }
  }, [selectedCourseId, selectedLessonId]);

  useEffect(() => {
    if (canManage) {
      loadCourses();
    }
  }, [canManage, loadCourses]);

  useEffect(() => {
    if (!selectedCourseId) return;
    setSelectedLessonId(ALL_LESSONS_VALUE);
    setGenerateLessonId("");
    loadLessons(selectedCourseId);
  }, [selectedCourseId, loadLessons]);

  useEffect(() => {
    if (selectedCourseId) {
      loadQuestions();
    }
  }, [selectedCourseId, selectedLessonId, loadQuestions]);

  const openCreateDialog = () => {
    const scopedLessonId = selectedLessonId === ALL_LESSONS_VALUE ? null : selectedLessonId;
    setEditingQuestion(null);
    setEditor(createDefaultEditor(scopedLessonId));
    setShowEditorDialog(true);
  };

  const openEditDialog = (question: QuestionBankQuestion) => {
    const sortedOptions = [...question.options].sort((a, b) => a.order_index - b.order_index);
    const options = sortedOptions.map((option) => option.option_text);
    while (options.length < 4) {
      options.push("");
    }

    const correctIndex = sortedOptions.findIndex((option) => option.is_correct);
    setEditingQuestion(question);
    setEditor({
      lesson_id: question.lesson_id || null,
      question_text: question.question_text,
      explanation: question.explanation || "",
      difficulty: question.difficulty,
      purpose_type: question.purpose_type,
      options: options.slice(0, 4),
      correctIndex: correctIndex >= 0 && correctIndex < 4 ? correctIndex : 0,
    });
    setShowEditorDialog(true);
  };

  const saveQuestion = async () => {
    if (!selectedCourseId || !editor.question_text.trim()) return;
    if (editor.options.some((option) => !option.trim())) {
      alert("Vui lòng nhập đủ 4 đáp án.");
      return;
    }

    setIsSavingQuestion(true);
    try {
      const payload = {
        lesson_id: editor.lesson_id,
        question_text: editor.question_text.trim(),
        explanation: editor.explanation.trim() || null,
        difficulty: editor.difficulty,
        purpose_type: editor.purpose_type,
        options: editor.options.map((optionText, index) => ({
          option_text: optionText.trim(),
          is_correct: index === editor.correctIndex,
        })),
      };

      if (editingQuestion) {
        await questionBankApi.updateQuestion(editingQuestion.id, payload);
      } else {
        await questionBankApi.createQuestion({
          ...payload,
          course_id: selectedCourseId,
        });
      }

      await loadQuestions();
      setShowEditorDialog(false);
      setEditingQuestion(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Lưu câu hỏi thất bại");
    } finally {
      setIsSavingQuestion(false);
    }
  };

  const generateQuestions = async () => {
    if (!selectedCourseId || !generateLessonId) {
      alert("Vui lòng chọn khóa học và buổi học để tạo câu hỏi.");
      return;
    }
    if (generateCount < 1 || generateCount > 20) {
      alert("Số lượng câu hỏi cần nằm trong khoảng từ 1 đến 20.");
      return;
    }

    setIsGenerating(true);
    try {
      await questionBankApi.generateQuestions({
        course_id: selectedCourseId,
        lesson_id: generateLessonId,
        question_count: generateCount,
        difficulty: generateDifficulty,
        purpose_type: generatePurpose,
      });
      await loadQuestions();
      setShowGenerateDialog(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Tạo câu hỏi bằng AI thất bại");
    } finally {
      setIsGenerating(false);
    }
  };

  const deleteQuestion = async (question: QuestionBankQuestion) => {
    const confirmed = window.confirm("Bạn có chắc muốn xóa câu hỏi này?");
    if (!confirmed) return;

    try {
      await questionBankApi.deleteQuestion(question.id);
      await loadQuestions();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Xóa câu hỏi thất bại");
    }
  };

  const toggleExpanded = (questionId: string) => {
    setExpandedQuestionIds((prev) => {
      const next = new Set(prev);
      if (next.has(questionId)) {
        next.delete(questionId);
      } else {
        next.add(questionId);
      }
      return next;
    });
  };

  if (!canManage) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold text-slate-900">Ngân hàng câu hỏi</h1>
        <p className="mt-2 text-sm text-muted-foreground">Bạn không có quyền truy cập khu vực này.</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Ngân hàng câu hỏi</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {selectedCourse ? selectedCourse.title : "Chọn khóa học để xem câu hỏi"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={openCreateDialog} disabled={!selectedCourseId}>
            <Plus className="h-4 w-4 mr-2" />
            Tạo thủ công
          </Button>
          <Button
            onClick={() => {
              setGenerateLessonId(selectedLessonId === ALL_LESSONS_VALUE ? lessons[0]?.id || "" : selectedLessonId);
              setShowGenerateDialog(true);
            }}
            disabled={!selectedCourseId || lessons.length === 0}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Tạo câu hỏi
          </Button>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="space-y-2">
          <Label>Khóa học</Label>
          <Select value={selectedCourseId} onValueChange={setSelectedCourseId} disabled={isLoading || courses.length === 0}>
            <SelectTrigger>
              <SelectValue placeholder="Chọn khóa học" />
            </SelectTrigger>
            <SelectContent>
              {courses.map((course) => (
                <SelectItem key={course.id} value={course.id}>
                  {course.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Buổi học</Label>
          <Select value={selectedLessonId} onValueChange={setSelectedLessonId} disabled={!selectedCourseId}>
            <SelectTrigger>
              <SelectValue placeholder="Hiển thị tất cả" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_LESSONS_VALUE}>Tất cả buổi học</SelectItem>
              {lessons.map((lesson) => (
                <SelectItem key={lesson.id} value={lesson.id}>
                  {lesson.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <div className="rounded-lg border bg-white">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3">
          <p className="text-sm font-medium text-slate-900">Danh sách câu hỏi</p>
          <Badge variant="outline">{questions.length} câu hỏi</Badge>
        </div>
        <div className="grid grid-cols-[40px_minmax(0,1fr)] gap-3 border-b px-4 py-3 text-xs font-medium uppercase text-muted-foreground md:grid-cols-[48px_minmax(0,1fr)_140px]">
          <span />
          <span>Câu hỏi</span>
          <span className="hidden md:block">Mức độ</span>
        </div>

        {isLoading || isQuestionsLoading ? (
          <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Đang tải...
          </div>
        ) : questions.length === 0 ? (
          <div className="px-4 py-12 text-center text-sm text-muted-foreground">Chưa có câu hỏi trong phạm vi đã chọn.</div>
        ) : (
          <div className="divide-y">
            {questions.map((question) => {
              const isExpanded = expandedQuestionIds.has(question.id);
              return (
                <div key={question.id}>
                  <div className="grid grid-cols-[40px_minmax(0,1fr)] gap-3 px-4 py-3 md:grid-cols-[48px_minmax(0,1fr)_140px]">
                    <Button variant="ghost" size="icon" onClick={() => toggleExpanded(question.id)} aria-label="Mở chi tiết câu hỏi">
                      {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </Button>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-900">{question.question_text}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{question.course_title}</p>
                      <div className="mt-2 flex md:hidden">
                        <Badge variant={question.difficulty === QuestionDifficulty.HARD ? "destructive" : "secondary"}>
                          {difficultyLabels[question.difficulty]}
                        </Badge>
                      </div>
                    </div>
                    <div className="hidden items-start md:flex">
                      <Badge variant={question.difficulty === QuestionDifficulty.HARD ? "destructive" : "secondary"}>
                        {difficultyLabels[question.difficulty]}
                      </Badge>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="bg-slate-50 px-4 pb-4 md:pl-[64px]">
                      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_260px]">
                        <div className="space-y-3">
                          <div>
                            <p className="text-xs font-medium uppercase text-muted-foreground">Giải thích</p>
                            <p className="mt-1 text-sm text-slate-700">{question.explanation || "Chưa có giải thích."}</p>
                          </div>
                          <div className="space-y-2">
                            <p className="text-xs font-medium uppercase text-muted-foreground">Đáp án</p>
                            {[...question.options]
                              .sort((a, b) => a.order_index - b.order_index)
                              .map((option, index) => (
                                <div key={option.id} className="flex items-start gap-2 rounded-md border bg-white px-3 py-2 text-sm">
                                  <span className="font-medium">{String.fromCharCode(65 + index)}.</span>
                                  <span className="flex-1">{option.option_text}</span>
                                  {option.is_correct && <Badge>Đúng</Badge>}
                                </div>
                              ))}
                          </div>
                        </div>
                        <div className="space-y-3">
                          <div>
                            <p className="text-xs font-medium uppercase text-muted-foreground">Buổi học</p>
                            <p className="mt-1 text-sm text-slate-700">{question.lesson_title || "Chung khóa học"}</p>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="outline">{purposeLabels[question.purpose_type]}</Badge>
                            <Badge variant="outline">{difficultyLabels[question.difficulty]}</Badge>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Button variant="outline" size="sm" onClick={() => openEditDialog(question)}>
                              <Edit3 className="h-4 w-4 mr-2" />
                              Sửa
                            </Button>
                            <Button variant="destructive" size="sm" onClick={() => deleteQuestion(question)}>
                              <Trash2 className="h-4 w-4 mr-2" />
                              Xóa
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Tạo câu hỏi bằng AI</DialogTitle>
            <DialogDescription>Chọn buổi học làm ngữ cảnh sinh câu hỏi.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Buổi học</Label>
              <Select value={generateLessonId} onValueChange={setGenerateLessonId}>
                <SelectTrigger>
                  <SelectValue placeholder="Chọn buổi học" />
                </SelectTrigger>
                <SelectContent>
                  {lessons.map((lesson) => (
                    <SelectItem key={lesson.id} value={lesson.id}>
                      {lesson.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="space-y-2">
                <Label>Số câu</Label>
                <Input
                  type="number"
                  min={1}
                  max={20}
                  value={generateCount}
                  onChange={(event) => setGenerateCount(Number(event.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label>Mức độ</Label>
                <Select value={generateDifficulty} onValueChange={(value) => setGenerateDifficulty(value as QuestionDifficulty)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(QuestionDifficulty).map((difficulty) => (
                      <SelectItem key={difficulty} value={difficulty}>
                        {difficultyLabels[difficulty]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Mục đích</Label>
                <Select value={generatePurpose} onValueChange={(value) => setGeneratePurpose(value as QuestionPurposeType)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(QuestionPurposeType).map((purpose) => (
                      <SelectItem key={purpose} value={purpose}>
                        {purposeLabels[purpose]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowGenerateDialog(false)} disabled={isGenerating}>
              Hủy
            </Button>
            <Button onClick={generateQuestions} disabled={isGenerating || !generateLessonId || generateCount < 1 || generateCount > 20}>
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Đang tạo...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Tạo câu hỏi
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showEditorDialog} onOpenChange={setShowEditorDialog}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingQuestion ? "Sửa câu hỏi" : "Tạo câu hỏi thủ công"}</DialogTitle>
            <DialogDescription>{selectedCourse?.title || "Ngân hàng câu hỏi"}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid gap-3 md:grid-cols-3">
              <div className="space-y-2">
                <Label>Buổi học</Label>
                <Select
                  value={editor.lesson_id || ALL_LESSONS_VALUE}
                  onValueChange={(value) => setEditor((prev) => ({ ...prev, lesson_id: value === ALL_LESSONS_VALUE ? null : value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={ALL_LESSONS_VALUE}>Chung khóa học</SelectItem>
                    {lessons.map((lesson) => (
                      <SelectItem key={lesson.id} value={lesson.id}>
                        {lesson.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Mức độ</Label>
                <Select
                  value={editor.difficulty}
                  onValueChange={(value) => setEditor((prev) => ({ ...prev, difficulty: value as QuestionDifficulty }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(QuestionDifficulty).map((difficulty) => (
                      <SelectItem key={difficulty} value={difficulty}>
                        {difficultyLabels[difficulty]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Mục đích</Label>
                <Select
                  value={editor.purpose_type}
                  onValueChange={(value) => setEditor((prev) => ({ ...prev, purpose_type: value as QuestionPurposeType }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(QuestionPurposeType).map((purpose) => (
                      <SelectItem key={purpose} value={purpose}>
                        {purposeLabels[purpose]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Câu hỏi *</Label>
              <Textarea
                value={editor.question_text}
                onChange={(event) => setEditor((prev) => ({ ...prev, question_text: event.target.value }))}
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label>Giải thích</Label>
              <Textarea
                value={editor.explanation}
                onChange={(event) => setEditor((prev) => ({ ...prev, explanation: event.target.value }))}
                rows={3}
              />
            </div>

            <div className="space-y-3">
              <Label>Đáp án *</Label>
              {editor.options.map((option, index) => (
                <div key={index} className="grid grid-cols-[80px_minmax(0,1fr)] gap-2">
                  <Button
                    type="button"
                    variant={editor.correctIndex === index ? "default" : "outline"}
                    onClick={() => setEditor((prev) => ({ ...prev, correctIndex: index }))}
                  >
                    {editor.correctIndex === index ? "Đúng" : "Chọn"}
                  </Button>
                  <Input
                    value={option}
                    onChange={(event) => {
                      const value = event.target.value;
                      setEditor((prev) => {
                        const nextOptions = [...prev.options];
                        nextOptions[index] = value;
                        return { ...prev, options: nextOptions };
                      });
                    }}
                    placeholder={`Đáp án ${String.fromCharCode(65 + index)}`}
                  />
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditorDialog(false)} disabled={isSavingQuestion}>
              Hủy
            </Button>
            <Button onClick={saveQuestion} disabled={isSavingQuestion || !editor.question_text.trim()}>
              {isSavingQuestion ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Đang lưu...
                </>
              ) : (
                "Lưu câu hỏi"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
