"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ChevronRight,
  Eye,
  Link2,
  Loader2,
  Plus,
  Save,
  Shuffle,
  Trash2,
  Upload,
  Video,
} from "lucide-react";

import { assignmentApi, courseApi, lessonApi, Lesson, Material } from "@/lib/api";
import { useAuthStore } from "@/lib/auth/store";
import { Assignment, CourseDetail, QuestionDifficulty, QuestionPurposeType, UserRole } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface MaterialUploadForm {
  title: string;
  description: string;
  type: "document" | "link";
  externalUrl: string;
  file: File | null;
}

interface AssignmentEditorQuestion {
  question_text: string;
  difficulty: QuestionDifficulty;
  purpose_type: QuestionPurposeType;
  options: string[];
  correctIndex: number;
}

interface LessonVideoItem {
  id: string;
  title: string;
  url: string;
  source: "material" | "legacy";
}

export default function LessonStudioPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuthStore();

  const slug = params.slug as string;
  const lessonId = params.lessonId as string;

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [lessonAssignments, setLessonAssignments] = useState<Assignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showVideoDialog, setShowVideoDialog] = useState(false);
  const [videoSource, setVideoSource] = useState("");
  const [videoInputMode, setVideoInputMode] = useState<"file" | "url">("url");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [isSavingVideo, setIsSavingVideo] = useState(false);

  const [showMaterialDialog, setShowMaterialDialog] = useState(false);
  const [isSavingMaterial, setIsSavingMaterial] = useState(false);
  const [materialForm, setMaterialForm] = useState<MaterialUploadForm>({
    title: "",
    description: "",
    type: "document",
    externalUrl: "",
    file: null,
  });

  const [showAssignmentDialog, setShowAssignmentDialog] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null);
  const [assignmentTitle, setAssignmentTitle] = useState("");
  const [assignmentQuestions, setAssignmentQuestions] = useState<AssignmentEditorQuestion[]>([]);
  const [isSavingAssignment, setIsSavingAssignment] = useState(false);
  const [showQuestionBankAssignmentDialog, setShowQuestionBankAssignmentDialog] = useState(false);
  const [bankAssignmentTitle, setBankAssignmentTitle] = useState("");
  const [bankAssignmentCount, setBankAssignmentCount] = useState(10);
  const [isGeneratingBankAssignment, setIsGeneratingBankAssignment] = useState(false);

  const [isPublishingAssignmentId, setIsPublishingAssignmentId] = useState<string | null>(null);
  const [deletingAssignmentId, setDeletingAssignmentId] = useState<string | null>(null);

  const fetchLessonStudioData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const courseData = await courseApi.getBySlug(slug);
      setCourse(courseData);

      const lessonsData = (await courseApi.getLessons(courseData.id)) as Lesson[];
      const targetLesson = lessonsData.find((item) => item.id === lessonId);
      if (!targetLesson) {
        setError("Không tìm thấy lesson trong khóa học này");
        return;
      }

      let materials: Material[] = [];
      try {
        materials = await lessonApi.getMaterials(targetLesson.id);
      } catch {
        materials = [];
      }

      setLesson({ ...targetLesson, materials });

      let assignments: Assignment[] = [];
      try {
        const assignmentData = await assignmentApi.listByCourse(courseData.id, true);
        assignments = assignmentData
          .filter((item) => item.lesson_id === targetLesson.id)
          .sort((a, b) => a.order_index - b.order_index);
      } catch {
        assignments = [];
      }

      setLessonAssignments(assignments);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Không thể tải Lesson Studio");
    } finally {
      setIsLoading(false);
    }
  }, [slug, lessonId]);

  useEffect(() => {
    if (slug && lessonId) {
      fetchLessonStudioData();
    }
  }, [slug, lessonId, fetchLessonStudioData]);

  const isInstructor = !!course && user?.id === course.instructor_id;
  const isAdmin = user?.role === UserRole.ADMIN;
  const canManage = isInstructor || isAdmin;

  const lessonVideos = useMemo<LessonVideoItem[]>(() => {
    if (!lesson) return [];

    const videoMaterials = (lesson.materials || [])
      .filter((material) => material.type === "video" && !!material.file_url)
      .map((material) => ({
        id: material.id,
        title: material.title,
        url: material.file_url!,
        source: "material" as const,
      }));

    const hasLegacyVideo = !!lesson.video_url && !videoMaterials.some((video) => video.url === lesson.video_url);

    if (!hasLegacyVideo) {
      return videoMaterials;
    }

    return [
      ...videoMaterials,
      {
        id: `legacy-${lesson.id}`,
        title: `${lesson.title} - Video legacy`,
        url: lesson.video_url!,
        source: "legacy" as const,
      },
    ];
  }, [lesson]);

  const lessonDocuments = useMemo(() => {
    if (!lesson) return [];
    return (lesson.materials || []).filter((material) => material.type === "document" || material.type === "link");
  }, [lesson]);

  const buildLessonContextQuery = (selectedVideoUrl?: string, selectedVideoTitle?: string, assignmentId?: string) => {
    if (!course || !lesson) return "";

    const params = new URLSearchParams({
      courseId: course.id,
      courseSlug: course.slug,
      lessonTitle: lesson.title,
    });

    if (selectedVideoUrl) {
      params.set("videoUrl", selectedVideoUrl);
    }

    if (selectedVideoTitle) {
      params.set("videoTitle", selectedVideoTitle);
    }

    if (assignmentId) {
      params.set("assignmentId", assignmentId);
    }

    return params.toString();
  };

  const resetMaterialForm = () => {
    setMaterialForm({
      title: "",
      description: "",
      type: "document",
      externalUrl: "",
      file: null,
    });
  };

  const handleSaveVideoSource = async () => {
    if (!lesson) return;
    if (videoInputMode === "file" && !videoFile) {
      alert("Vui lòng chọn file video từ máy.");
      return;
    }

    if (videoInputMode === "url" && !videoSource.trim()) {
      alert("Vui lòng nhập URL video.");
      return;
    }

    if (videoInputMode === "file" && videoFile && videoFile.size > 500 * 1024 * 1024) {
      alert("File video vượt quá giới hạn 500MB.");
      return;
    }

    setIsSavingVideo(true);
    try {
      let createdVideoMaterial: Material | null = null;

      if (videoInputMode === "file" && videoFile) {
        createdVideoMaterial = await lessonApi.uploadMaterial(lesson.id, {
          title: `${lesson.title} - Buổi học trực tiếp`,
          type: "video",
          file: videoFile,
        });
      } else {
        createdVideoMaterial = await lessonApi.uploadMaterial(lesson.id, {
          title: `${lesson.title} - Buổi học trực tiếp`,
          type: "video",
          external_url: videoSource.trim(),
        });
      }

      if (!createdVideoMaterial?.file_url) {
        throw new Error("Không lấy được đường dẫn video sau khi tạo.");
      }

      let updatedLesson: Lesson | null = null;
      if (!lesson.video_url) {
        updatedLesson = await lessonApi.update(lesson.id, {
          video_url: createdVideoMaterial.file_url,
        });
      }

      setLesson((prev) => {
        if (!prev) return prev;

        const nextMaterials = [...(prev.materials || []), createdVideoMaterial!];
        if (updatedLesson) {
          return { ...prev, ...updatedLesson, materials: nextMaterials };
        }

        return { ...prev, materials: nextMaterials };
      });

      setShowVideoDialog(false);
      setVideoFile(null);
      setVideoSource("");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Thêm video thất bại");
    } finally {
      setIsSavingVideo(false);
    }
  };

  const handleDeleteMaterial = async (materialId: string) => {
    if (!lesson) return;

    const confirmed = window.confirm("Bạn có chắc muốn xóa tài liệu này?");
    if (!confirmed) return;

    try {
      const targetMaterial = (lesson.materials || []).find((material) => material.id === materialId);
      await lessonApi.deleteMaterial(materialId);

      let nextLesson = {
        ...lesson,
        materials: (lesson.materials || []).filter((material) => material.id !== materialId),
      };

      if (
        targetMaterial?.type === "video" &&
        lesson.video_url &&
        targetMaterial.file_url === lesson.video_url
      ) {
        const nextVideoUrl = (nextLesson.materials || [])
          .filter((material) => material.type === "video" && !!material.file_url)
          .map((material) => material.file_url)
          .find((value) => !!value);

        const updatedLesson = await lessonApi.update(lesson.id, {
          video_url: nextVideoUrl || null,
        });

        nextLesson = {
          ...nextLesson,
          ...updatedLesson,
          materials: nextLesson.materials,
        };
      }

      setLesson(nextLesson);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Xóa tài liệu thất bại");
    }
  };

  const handleUploadMaterial = async () => {
    if (!lesson) return;
    if (materialForm.type === "document" && !materialForm.file) {
      alert("Vui lòng chọn file tài liệu để tải lên.");
      return;
    }

    if (materialForm.type === "link" && !materialForm.externalUrl.trim()) {
      alert("Vui lòng nhập đường dẫn URL.");
      return;
    }

    setIsSavingMaterial(true);
    try {
      const created = await lessonApi.uploadMaterial(lesson.id, {
        title: materialForm.title.trim() || undefined,
        description: materialForm.description.trim() || undefined,
        type: materialForm.type,
        file: materialForm.type === "document" ? materialForm.file || undefined : undefined,
        external_url: materialForm.type === "link" ? materialForm.externalUrl.trim() || undefined : undefined,
      });

      setLesson((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          materials: [...(prev.materials || []), created],
        };
      });

      setShowMaterialDialog(false);
      resetMaterialForm();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Tải tài liệu thất bại");
    } finally {
      setIsSavingMaterial(false);
    }
  };

  const createDefaultQuestion = (): AssignmentEditorQuestion => ({
    question_text: "",
    difficulty: QuestionDifficulty.EASY,
    purpose_type: QuestionPurposeType.SHARED,
    options: ["", "", "", ""],
    correctIndex: 0,
  });

  const mapAssignmentToEditorQuestions = (assignment: Assignment): AssignmentEditorQuestion[] => {
    const mapped = [...assignment.questions]
      .sort((a, b) => a.order_index - b.order_index)
      .map((question) => {
        const sortedOptions = [...question.options].sort((a, b) => a.order_index - b.order_index);
        const options = sortedOptions.map((option) => option.option_text);

        while (options.length < 4) {
          options.push("");
        }

        const correctIndex = sortedOptions.findIndex((option) => option.is_correct);

        return {
          question_text: question.question_text,
          difficulty: question.difficulty,
          purpose_type: question.purpose_type,
          options: options.slice(0, 4),
          correctIndex: correctIndex >= 0 && correctIndex < 4 ? correctIndex : 0,
        };
      });

    return mapped.length > 0 ? mapped : [createDefaultQuestion()];
  };

  const handleOpenAssignmentDialog = (assignment?: Assignment) => {
    if (!lesson) return;

    if (assignment) {
      setEditingAssignment(assignment);
      setAssignmentTitle(assignment.title);
      setAssignmentQuestions(mapAssignmentToEditorQuestions(assignment));
    } else {
      setEditingAssignment(null);
      setAssignmentTitle(`${lesson.title} - Bài tập`);
      setAssignmentQuestions([createDefaultQuestion()]);
    }

    setShowAssignmentDialog(true);
  };

  const updateQuestionField = (index: number, key: "question_text", value: string) => {
    setAssignmentQuestions((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [key]: value };
      return next;
    });
  };

  const updateQuestionOption = (questionIndex: number, optionIndex: number, value: string) => {
    setAssignmentQuestions((prev) => {
      const next = [...prev];
      const options = [...next[questionIndex].options];
      options[optionIndex] = value;
      next[questionIndex] = { ...next[questionIndex], options };
      return next;
    });
  };

  const handleSaveAssignment = async () => {
    if (!course || !lesson || !assignmentTitle.trim()) return;

    const hasInvalidQuestion = assignmentQuestions.some(
      (question) =>
        !question.question_text.trim() ||
        question.options.some((option) => !option.trim()) ||
        question.correctIndex < 0 ||
        question.correctIndex > 3
    );

    if (hasInvalidQuestion) {
      alert("Vui lòng nhập đầy đủ nội dung câu hỏi và 4 đáp án cho mỗi câu.");
      return;
    }

    setIsSavingAssignment(true);
    try {
      const payload = {
        lesson_id: lesson.id,
        title: assignmentTitle.trim(),
        questions: assignmentQuestions.map((question) => ({
          question_text: question.question_text.trim(),
          difficulty: question.difficulty,
          purpose_type: question.purpose_type,
          options: question.options.map((optionText, index) => ({
            option_text: optionText.trim(),
            is_correct: index === question.correctIndex,
          })),
        })),
      };

      if (editingAssignment) {
        const updated = await assignmentApi.update(editingAssignment.id, {
          title: payload.title,
          questions: payload.questions,
        });

        setLessonAssignments((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      } else {
        const created = await assignmentApi.create(course.id, payload);
        setLessonAssignments((prev) => [...prev, created].sort((a, b) => a.order_index - b.order_index));
      }

      setShowAssignmentDialog(false);
      setEditingAssignment(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || (editingAssignment ? "Cập nhật bài tập thất bại" : "Tạo bài tập thất bại"));
    } finally {
      setIsSavingAssignment(false);
    }
  };

  const handleOpenQuestionBankAssignmentDialog = () => {
    if (!lesson) return;
    setBankAssignmentTitle(`${lesson.title} - Bài tập ôn tập`);
    setBankAssignmentCount(10);
    setShowQuestionBankAssignmentDialog(true);
  };

  const handleGenerateQuestionBankAssignment = async () => {
    if (!course || !lesson) return;

    if (bankAssignmentCount < 1 || bankAssignmentCount > 100) {
      alert("Số câu phải nằm trong khoảng 1 đến 100.");
      return;
    }

    setIsGeneratingBankAssignment(true);
    try {
      const created = await assignmentApi.generateFromBank(course.id, {
        lesson_id: lesson.id,
        question_count: bankAssignmentCount,
        title: bankAssignmentTitle.trim() || undefined,
      });

      setLessonAssignments((prev) => [...prev, created].sort((a, b) => a.order_index - b.order_index));
      setShowQuestionBankAssignmentDialog(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Tạo bài tập ôn tập từ ngân hàng câu hỏi thất bại");
    } finally {
      setIsGeneratingBankAssignment(false);
    }
  };

  const handlePublishAssignment = async (assignmentId: string) => {
    setIsPublishingAssignmentId(assignmentId);
    try {
      const published = await assignmentApi.publish(assignmentId);
      setLessonAssignments((prev) => prev.map((item) => (item.id === published.id ? published : item)));

      if (editingAssignment?.id === assignmentId) {
        setEditingAssignment(published);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || "Xuất bản assignment thất bại");
    } finally {
      setIsPublishingAssignmentId(null);
    }
  };

  const handleDeleteAssignment = async (assignmentId: string) => {
    const confirmed = window.confirm("Bạn có chắc muốn xóa assignment này?");
    if (!confirmed) return;

    setDeletingAssignmentId(assignmentId);
    try {
      await assignmentApi.delete(assignmentId);
      setLessonAssignments((prev) => prev.filter((item) => item.id !== assignmentId));

      if (editingAssignment?.id === assignmentId) {
        setShowAssignmentDialog(false);
        setEditingAssignment(null);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || "Xóa assignment thất bại");
    } finally {
      setDeletingAssignmentId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !course || !lesson) {
    return (
      <Card className="p-10 text-center">
        <CardTitle className="mb-3">Không thể mở Lesson Studio</CardTitle>
        <CardDescription className="mb-4">{error || "Dữ liệu không hợp lệ"}</CardDescription>
        <Button onClick={() => router.push(`/courses/${slug}`)}>Quay lại khóa học</Button>
      </Card>
    );
  }

  if (!canManage) {
    return (
      <Card className="p-10 text-center">
        <CardTitle className="mb-3">Không có quyền truy cập</CardTitle>
        <CardDescription className="mb-4">Chỉ giảng viên sở hữu khóa học hoặc admin mới có thể quản lý Lesson Studio.</CardDescription>
        <Button onClick={() => router.push(`/courses/${slug}`)}>Quay lại khóa học</Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={() => router.push(`/courses/${slug}`)}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Quay lại khóa học
      </Button>

      <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <Link href="/courses" className="hover:text-foreground">Khóa học</Link>
        <span>&gt;</span>
        <Link href={`/courses/${course.slug}`} className="hover:text-foreground">{course.title}</Link>
        <span>&gt;</span>
        <span>{lesson.title}</span>
        <span>&gt;</span>
        <span className="font-medium text-foreground">Lesson Studio</span>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Lesson Studio</p>
            <h1 className="text-2xl font-semibold text-slate-900 mt-1">{lesson.title}</h1>
            <p className="text-sm text-muted-foreground mt-1">Không gian quản lý chi tiết cho từng lesson.</p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">{lessonDocuments.length} tài liệu</Badge>
            <Badge variant="outline">{lessonVideos.length} buổi trực tiếp</Badge>
            <Badge variant="outline">{lessonAssignments.length} assignment</Badge>
            <Badge variant={lesson.is_published ? "default" : "secondary"}>
              {lesson.is_published ? "Đã xuất bản" : "Nháp"}
            </Badge>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle>Buổi học trực tiếp</CardTitle>
                  <CardDescription>Lesson có thể chứa nhiều video/phòng học.</CardDescription>
                </div>
                <Button onClick={() => setShowVideoDialog(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Thêm video
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {lessonVideos.length === 0 ? (
                <p className="text-sm text-muted-foreground">Chưa có buổi học trực tiếp nào.</p>
              ) : (
                <div className="space-y-2">
                  {lessonVideos.map((video, index) => (
                    <div key={video.id} className="rounded-lg border p-3 flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium">{video.title || `Buổi học ${index + 1}`}</p>
                        <p className="text-xs text-muted-foreground">
                          {video.source === "legacy" ? "Nguồn legacy" : "Nguồn material"}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" asChild>
                          <Link href={`/lessons/${lesson.id}/video?${buildLessonContextQuery(video.url, video.title)}`}>
                            <Video className="h-4 w-4 mr-2" />
                            Mở
                          </Link>
                        </Button>
                        {video.source === "material" && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-red-600 hover:text-red-700"
                            onClick={() => handleDeleteMaterial(video.id)}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Xóa
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle>Assignments</CardTitle>
                  <CardDescription>Một lesson có thể có nhiều bài tập.</CardDescription>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" onClick={handleOpenQuestionBankAssignmentDialog}>
                    <Shuffle className="h-4 w-4 mr-2" />
                    Tạo bài ôn tập
                  </Button>
                  <Button variant="outline" onClick={() => handleOpenAssignmentDialog()}>
                    <Plus className="h-4 w-4 mr-2" />
                    Tạo thủ công
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {lessonAssignments.length === 0 ? (
                <p className="text-sm text-muted-foreground">Chưa có assignment nào.</p>
              ) : (
                <div className="space-y-3">
                  {lessonAssignments.map((assignment, index) => (
                    <div key={assignment.id} className="rounded-lg border p-3 space-y-3">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-medium">{assignment.title || `Assignment ${index + 1}`}</p>
                          <p className="text-xs text-muted-foreground">{assignment.questions.length} câu hỏi</p>
                        </div>
                        <Badge variant={assignment.is_published ? "default" : "secondary"}>
                          {assignment.is_published ? "Đã xuất bản" : "Nháp"}
                        </Badge>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" asChild>
                          <Link href={`/lessons/${lesson.id}/assignment?${buildLessonContextQuery(undefined, undefined, assignment.id)}`}>
                            <ChevronRight className="h-4 w-4 mr-2" />
                            Mở trang bài tập
                          </Link>
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleOpenAssignmentDialog(assignment)}>
                          <Save className="h-4 w-4 mr-2" />
                          Sửa
                        </Button>
                        {!assignment.is_published && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handlePublishAssignment(assignment.id)}
                            disabled={isPublishingAssignmentId === assignment.id}
                          >
                            {isPublishingAssignmentId === assignment.id ? (
                              <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Đang xuất bản...
                              </>
                            ) : (
                              <>
                                <Eye className="h-4 w-4 mr-2" />
                                Xuất bản
                              </>
                            )}
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-600 hover:text-red-700"
                          onClick={() => handleDeleteAssignment(assignment.id)}
                          disabled={deletingAssignmentId === assignment.id}
                        >
                          {deletingAssignmentId === assignment.id ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Đang xóa...
                            </>
                          ) : (
                            <>
                              <Trash2 className="h-4 w-4 mr-2" />
                              Xóa
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle>Tài liệu lesson</CardTitle>
                  <CardDescription>Tài liệu document/link cho lesson.</CardDescription>
                </div>
                <Button variant="outline" onClick={() => {
                  resetMaterialForm();
                  setShowMaterialDialog(true);
                }}>
                  <Upload className="h-4 w-4 mr-2" />
                  Thêm
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {lessonDocuments.length === 0 ? (
                <p className="text-sm text-muted-foreground">Chưa có tài liệu cho lesson.</p>
              ) : (
                <div className="space-y-2">
                  {lessonDocuments.map((material) => (
                    <div key={material.id} className="rounded-lg border p-3 flex items-center justify-between gap-3">
                      <Link
                        href={`/lessons/${lesson.id}/materials/${material.id}?${buildLessonContextQuery()}`}
                        className="flex-1 text-sm hover:text-primary"
                      >
                        {material.title}
                      </Link>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-600 hover:text-red-700"
                        onClick={() => handleDeleteMaterial(material.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Điều hướng nhanh</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button asChild variant="outline" className="w-full justify-start">
                <Link href={`/courses/${course.slug}`}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Quay lại khóa học
                </Link>
              </Button>
              <Button variant="outline" className="w-full justify-start" onClick={fetchLessonStudioData}>
                <Loader2 className="h-4 w-4 mr-2" />
                Làm mới dữ liệu
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      <Dialog open={showVideoDialog} onOpenChange={setShowVideoDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Thêm buổi học trực tiếp</DialogTitle>
            <DialogDescription>Lesson: {lesson.title}</DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Nguồn video (chọn 1)</Label>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant={videoInputMode === "file" ? "default" : "outline"}
                  onClick={() => {
                    setVideoInputMode("file");
                    setVideoSource("");
                  }}
                >
                  Upload từ Local
                </Button>
                <Button
                  type="button"
                  variant={videoInputMode === "url" ? "default" : "outline"}
                  onClick={() => {
                    setVideoInputMode("url");
                    setVideoFile(null);
                  }}
                >
                  Dùng URL
                </Button>
              </div>
            </div>

            {videoInputMode === "file" ? (
              <div className="space-y-2">
                <Label htmlFor="studio-video-file">Tải file video</Label>
                <Input
                  id="studio-video-file"
                  type="file"
                  accept="video/*"
                  onChange={(e) => setVideoFile(e.target.files && e.target.files.length > 0 ? e.target.files[0] : null)}
                />
                <p className="text-xs text-muted-foreground">Hỗ trợ tối đa 500MB theo cấu hình hiện tại.</p>
              </div>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="studio-video-url" className="flex items-center gap-2">
                  <Link2 className="h-4 w-4" />
                  Video URL
                </Label>
                <Input
                  id="studio-video-url"
                  value={videoSource}
                  onChange={(e) => setVideoSource(e.target.value)}
                  placeholder="https://meet.google.com/... hoặc https://youtube.com/watch?v=..."
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVideoDialog(false)} disabled={isSavingVideo}>
              Hủy
            </Button>
            <Button onClick={handleSaveVideoSource} disabled={isSavingVideo}>
              {isSavingVideo ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Đang thêm...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Thêm video
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showMaterialDialog} onOpenChange={setShowMaterialDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Tải tài liệu cho lesson</DialogTitle>
            <DialogDescription>Lesson: {lesson.title}</DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="material-title">Tiêu đề tài liệu</Label>
              <Input
                id="material-title"
                value={materialForm.title}
                onChange={(e) => setMaterialForm({ ...materialForm, title: e.target.value })}
                placeholder="Bỏ trống để dùng tên file hoặc URL"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="material-description">Mô tả</Label>
              <Textarea
                id="material-description"
                rows={3}
                value={materialForm.description}
                onChange={(e) => setMaterialForm({ ...materialForm, description: e.target.value })}
                placeholder="Mô tả ngắn về tài liệu"
              />
            </div>

            <div className="space-y-2">
              <Label>Loại tài liệu</Label>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant={materialForm.type === "document" ? "default" : "outline"}
                  onClick={() => setMaterialForm((prev) => ({ ...prev, type: "document", externalUrl: "" }))}
                >
                  Document
                </Button>
                <Button
                  type="button"
                  variant={materialForm.type === "link" ? "default" : "outline"}
                  onClick={() => setMaterialForm((prev) => ({ ...prev, type: "link", file: null }))}
                >
                  Link
                </Button>
              </div>
            </div>

            {materialForm.type === "document" ? (
              <div className="space-y-2">
                <Label htmlFor="material-file">Tải file tài liệu</Label>
                <Input
                  id="material-file"
                  type="file"
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.zip,.rar"
                  onChange={(e) =>
                    setMaterialForm({
                      ...materialForm,
                      file: e.target.files && e.target.files.length > 0 ? e.target.files[0] : null,
                    })
                  }
                />
              </div>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="material-external-url" className="flex items-center gap-2">
                  <Link2 className="h-4 w-4" />
                  URL tài liệu
                </Label>
                <Input
                  id="material-external-url"
                  value={materialForm.externalUrl}
                  onChange={(e) => setMaterialForm({ ...materialForm, externalUrl: e.target.value })}
                  placeholder="https://..."
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMaterialDialog(false)} disabled={isSavingMaterial}>
              Hủy
            </Button>
            <Button
              onClick={handleUploadMaterial}
              disabled={
                isSavingMaterial ||
                (materialForm.type === "document" && !materialForm.file) ||
                (materialForm.type === "link" && !materialForm.externalUrl.trim())
              }
            >
              {isSavingMaterial ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Đang tải...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Đăng tài liệu
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showQuestionBankAssignmentDialog} onOpenChange={setShowQuestionBankAssignmentDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Tạo bài tập ôn tập</DialogTitle>
            <DialogDescription>Hệ thống chọn ngẫu nhiên câu hỏi Luyện tập/Dùng chung theo tỉ lệ Dễ/Trung bình/Khó 40/40/20.</DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="bank-assignment-title">Tiêu đề bài tập</Label>
              <Input
                id="bank-assignment-title"
                value={bankAssignmentTitle}
                onChange={(event) => setBankAssignmentTitle(event.target.value)}
                placeholder="Ví dụ: Bài tập ôn tập buổi 1"
              />
            </div>

            <div className="max-w-40 space-y-2">
              <Label htmlFor="bank-assignment-count">Số câu *</Label>
              <Input
                id="bank-assignment-count"
                type="number"
                min={1}
                max={100}
                value={bankAssignmentCount}
                onChange={(event) => setBankAssignmentCount(Number(event.target.value))}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowQuestionBankAssignmentDialog(false)} disabled={isGeneratingBankAssignment}>
              Hủy
            </Button>
            <Button
              onClick={handleGenerateQuestionBankAssignment}
              disabled={isGeneratingBankAssignment || bankAssignmentCount < 1 || bankAssignmentCount > 100}
            >
              {isGeneratingBankAssignment ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Đang tạo...
                </>
              ) : (
                <>
                  <Shuffle className="h-4 w-4 mr-2" />
                  Tạo nháp
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showAssignmentDialog} onOpenChange={setShowAssignmentDialog}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingAssignment ? "Rà soát Assignment" : "Tạo Assignment cho Lesson"}</DialogTitle>
            <DialogDescription>
              Lesson: {lesson.title}
              {editingAssignment
                ? editingAssignment.is_published
                  ? " (Trạng thái: Đã xuất bản)"
                  : " (Trạng thái: Nháp chưa xuất bản)"
                : ""}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="assignment-title">Tiêu đề bài tập *</Label>
              <Input
                id="assignment-title"
                value={assignmentTitle}
                onChange={(e) => setAssignmentTitle(e.target.value)}
                placeholder="Ví dụ: Quiz bài 1"
              />
            </div>

            {assignmentQuestions.map((question, questionIndex) => (
              <div key={questionIndex} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium">Câu hỏi {questionIndex + 1}</p>
                  {assignmentQuestions.length > 1 && (
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => setAssignmentQuestions((prev) => prev.filter((_, idx) => idx !== questionIndex))}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Xóa
                    </Button>
                  )}
                </div>

                <div className="space-y-2">
                  <Label>Nội dung câu hỏi *</Label>
                  <Textarea
                    rows={2}
                    value={question.question_text}
                    onChange={(e) => updateQuestionField(questionIndex, "question_text", e.target.value)}
                    placeholder="Nhập câu hỏi"
                  />
                </div>

                <div className="space-y-2">
                  <Label>4 đáp án (chọn 1 đáp án đúng)</Label>
                  <div className="space-y-2">
                    {question.options.map((option, optionIndex) => (
                      <div key={optionIndex} className="flex items-center gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant={question.correctIndex === optionIndex ? "default" : "outline"}
                          onClick={() => {
                            setAssignmentQuestions((prev) => {
                              const next = [...prev];
                              next[questionIndex] = { ...next[questionIndex], correctIndex: optionIndex };
                              return next;
                            });
                          }}
                        >
                          {question.correctIndex === optionIndex ? "Đúng" : "Chọn"}
                        </Button>
                        <Input
                          value={option}
                          onChange={(e) => updateQuestionOption(questionIndex, optionIndex, e.target.value)}
                          placeholder={`Đáp án ${optionIndex + 1}`}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}

            <Button
              type="button"
              variant="outline"
              onClick={() => setAssignmentQuestions((prev) => [...prev, createDefaultQuestion()])}
            >
              <Plus className="h-4 w-4 mr-2" />
              Thêm câu hỏi
            </Button>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAssignmentDialog(false)} disabled={isSavingAssignment}>
              Hủy
            </Button>
            {editingAssignment && !editingAssignment.is_published && (
              <Button
                variant="outline"
                onClick={() => handlePublishAssignment(editingAssignment.id)}
                disabled={isSavingAssignment || isPublishingAssignmentId === editingAssignment.id}
              >
                {isPublishingAssignmentId === editingAssignment.id ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Đang xuất bản...
                  </>
                ) : (
                  <>
                    <Eye className="h-4 w-4 mr-2" />
                    Xuất bản
                  </>
                )}
              </Button>
            )}
            <Button onClick={handleSaveAssignment} disabled={isSavingAssignment || !assignmentTitle.trim()}>
              {isSavingAssignment ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {editingAssignment ? "Đang lưu nháp..." : "Đang tạo nháp..."}
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  {editingAssignment ? "Lưu thay đổi" : "Tạo assignment nháp"}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
