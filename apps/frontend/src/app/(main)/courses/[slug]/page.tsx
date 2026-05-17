"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  BookOpen, 
  Clock, 
  ChevronRight,
  ChevronDown,
  ChevronUp,
  ArrowLeft,
  Plus,
  Edit,
  Trash2,
  Video,
  FileText,
  ClipboardCheck,
  ClipboardList,
  GripVertical,
  Eye,
  EyeOff,
  Loader2,
  Upload
} from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { assignmentApi, courseApi, lessonApi, Lesson, Material } from "@/lib/api";
import { useAuthStore } from "@/lib/auth/store";
import { Assignment, AssignmentType, CourseDetail, UserRole } from "@/types";

interface MaterialUploadForm {
  title: string;
  description: string;
  type: "document" | "link" | "video";
  externalUrl: string;
  file: File | null;
  videoInputMode: "file" | "url";
}

interface LessonVideoItem {
  id: string;
  title: string;
  url: string;
  source: "material" | "legacy";
}

type LearningFilter = "description" | "home" | "document" | "assignments" | "classroom";

const learningFilterOptions: { value: LearningFilter; label: string }[] = [
  { value: "description", label: "Mô tả" },
  { value: "home", label: "Home" },
  { value: "document", label: "Document" },
  { value: "assignments", label: "Assigaments" },
  { value: "classroom", label: "Classroom" },
];

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuthStore();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [courseMaterials, setCourseMaterials] = useState<Material[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Lesson management state
  const [showLessonDialog, setShowLessonDialog] = useState(false);
  const [editingLesson, setEditingLesson] = useState<Lesson | null>(null);
  const [lessonForm, setLessonForm] = useState({
    title: "",
    description: "",
    content: "",
    is_preview: false,
  });
  const [isSavingLesson, setIsSavingLesson] = useState(false);
  const [deletingLessonId, setDeletingLessonId] = useState<string | null>(null);

  // Material management state
  const [showMaterialDialog, setShowMaterialDialog] = useState(false);
  const [isSavingMaterial, setIsSavingMaterial] = useState(false);
  const [materialForm, setMaterialForm] = useState<MaterialUploadForm>({
    title: "",
    description: "",
    type: "document",
    externalUrl: "",
    file: null,
    videoInputMode: "url",
  });
  const [collapsedLessonIds, setCollapsedLessonIds] = useState<Set<string>>(new Set());
  const [learningFilter, setLearningFilter] = useState<LearningFilter>("home");
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [testTitle, setTestTitle] = useState("");
  const [testQuestionCount, setTestQuestionCount] = useState(20);
  const [testLessonIds, setTestLessonIds] = useState<string[]>([]);
  const [isGeneratingTest, setIsGeneratingTest] = useState(false);

  const slug = params.slug as string;

  const fetchCourseData = useCallback(async () => {
    try {
      const courseData = await courseApi.getBySlug(slug);
      setCourse(courseData);

      const isOwner = !!user && (
        user.role === UserRole.ADMIN || user.id === courseData.instructor_id
      );
      
      // Fetch lessons using course ID (not slug)
      try {
        const lessonsData = await courseApi.getLessons(courseData.id);
        const lessonsWithMaterials = await Promise.all(
          lessonsData.map(async (lesson: Lesson) => {
            try {
              const materials = await lessonApi.getMaterials(lesson.id);
              return { ...lesson, materials };
            } catch {
              return { ...lesson, materials: [] };
            }
          })
        );
        setLessons(lessonsWithMaterials);
      } catch {
        setLessons([]);
      }

      try {
        const courseMaterialsData = await courseApi.getMaterials(courseData.id);
        setCourseMaterials(courseMaterialsData);
      } catch {
        setCourseMaterials([]);
      }

      try {
        const assignmentData = await assignmentApi.listByCourse(courseData.id, isOwner);
        setAssignments(assignmentData);
      } catch {
        setAssignments([]);
      }
      
    } catch (err: any) {
      setError(err.response?.data?.detail || "Không thể tải khóa học");
    } finally {
      setIsLoading(false);
    }
  }, [slug, user]);

  useEffect(() => {
    if (slug) {
      fetchCourseData();
    }
  }, [slug, fetchCourseData]);

  const handleOpenLessonDialog = (lesson?: Lesson) => {
    if (lesson) {
      setEditingLesson(lesson);
      setLessonForm({
        title: lesson.title,
        description: lesson.description || "",
        content: lesson.content || "",
        is_preview: lesson.is_preview,
      });
    } else {
      setEditingLesson(null);
      setLessonForm({
        title: "",
        description: "",
        content: "",
        is_preview: false,
      });
    }
    setShowLessonDialog(true);
  };

  const handleSaveLesson = async () => {
    if (!course || !lessonForm.title.trim()) return;

    setIsSavingLesson(true);
    try {
      if (editingLesson) {
        const updated = await lessonApi.update(editingLesson.id, {
          title: lessonForm.title,
          description: lessonForm.description || undefined,
          content: lessonForm.content || undefined,
          is_preview: lessonForm.is_preview,
        });

        setLessons((prev) =>
          prev.map((lesson) => (lesson.id === updated.id ? { ...lesson, ...updated } : lesson))
        );
      } else {
        const newLesson = await lessonApi.create(course.id, {
          title: lessonForm.title,
          description: lessonForm.description || undefined,
          content: lessonForm.content || undefined,
          is_preview: lessonForm.is_preview,
          order_index: lessons.length,
        });

        setLessons((prev) => [...prev, newLesson]);
      }

      setShowLessonDialog(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Lưu bài học thất bại");
    } finally {
      setIsSavingLesson(false);
    }
  };

  const handleDeleteLesson = async (lessonId: string) => {
    try {
      await lessonApi.delete(lessonId);
      setLessons((prev) => prev.filter((lesson) => lesson.id !== lessonId));
      setDeletingLessonId(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Xóa bài học thất bại");
    }
  };

  const handleTogglePublish = async (lesson: Lesson) => {
    try {
      const updated = await lessonApi.update(lesson.id, {
        is_published: !lesson.is_published,
      });
      setLessons((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Cập nhật thất bại");
    }
  };

  const resetMaterialForm = () => {
    setMaterialForm({
      title: "",
      description: "",
      type: "document",
      externalUrl: "",
      file: null,
      videoInputMode: "url",
    });
  };

  const handleOpenMaterialDialog = () => {
    resetMaterialForm();
    setShowMaterialDialog(true);
  };

  const handleUploadMaterial = async () => {
    if (!course) return;
    if (materialForm.type === "document" && !materialForm.file) {
      alert("Vui lòng chọn file tài liệu để tải lên.");
      return;
    }

    if (materialForm.type === "link" && !materialForm.externalUrl.trim()) {
      alert("Vui lòng nhập đường dẫn URL.");
      return;
    }

    if (materialForm.type === "video") {
      if (materialForm.videoInputMode === "file" && !materialForm.file) {
        alert("Vui lòng chọn file video.");
        return;
      }
      if (materialForm.videoInputMode === "url" && !materialForm.externalUrl.trim()) {
        alert("Vui lòng nhập URL video.");
        return;
      }
    }

    if (materialForm.file && materialForm.externalUrl.trim() && materialForm.type !== "video") {
      alert("Chỉ được chọn một nguồn dữ liệu.");
      return;
    }

    setIsSavingMaterial(true);
    try {
      const shouldUseFile =
        materialForm.type === "document" ||
        (materialForm.type === "video" && materialForm.videoInputMode === "file");
      const shouldUseUrl =
        materialForm.type === "link" ||
        (materialForm.type === "video" && materialForm.videoInputMode === "url");

      const payload = {
        title: materialForm.title.trim() || undefined,
        description: materialForm.description.trim() || undefined,
        type: materialForm.type,
        file: shouldUseFile ? materialForm.file || undefined : undefined,
        external_url: shouldUseUrl ? materialForm.externalUrl.trim() || undefined : undefined,
      };

      const created = await courseApi.uploadMaterial(course.id, payload);
      setCourseMaterials((prev) => [...prev, created]);

      setShowMaterialDialog(false);
      resetMaterialForm();
    } catch (err: any) {
      if (err?.response?.status === 413) {
        alert("Tệp tải lên quá lớn. Vui lòng chọn tệp nhỏ hơn 100MB.");
      } else {
        alert(err.response?.data?.detail || "Tải tài liệu thất bại");
      }
    } finally {
      setIsSavingMaterial(false);
    }
  };

  const handleDeleteMaterial = async (materialId: string) => {
    const confirmed = window.confirm("Bạn có chắc muốn xóa tài liệu này?");
    if (!confirmed) return;

    try {
      await courseApi.deleteMaterial(materialId);
      setCourseMaterials((prev) => prev.filter((material) => material.id !== materialId));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Xóa tài liệu thất bại");
    }
  };

  const handleOpenTestDialog = () => {
    setTestTitle(`${course?.title || "Khóa học"} - Bài kiểm tra`);
    setTestQuestionCount(20);
    setTestLessonIds(lessons.map((lesson) => lesson.id));
    setShowTestDialog(true);
  };

  const handleGenerateTest = async () => {
    if (!course) return;
    if (testQuestionCount < 1 || testQuestionCount > 100) {
      alert("Số câu phải nằm trong khoảng 1-100.");
      return;
    }

    setIsGeneratingTest(true);
    try {
      const created = await assignmentApi.generateTest(course.id, {
        title: testTitle.trim() || undefined,
        question_count: testQuestionCount,
        lesson_ids: testLessonIds,
      });
      setAssignments((prev) => [...prev, created].sort((a, b) => a.order_index - b.order_index));
      setShowTestDialog(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Tạo bài kiểm tra thất bại");
    } finally {
      setIsGeneratingTest(false);
    }
  };

  const handlePublishTest = async (assignmentId: string) => {
    try {
      const published = await assignmentApi.publish(assignmentId);
      setAssignments((prev) => prev.map((assignment) => (assignment.id === published.id ? published : assignment)));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Xuất bản bài kiểm tra thất bại");
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const getLearningItems = (lesson: Lesson) => {
    const lessonMaterials = lesson.materials || [];
    const materials = lessonMaterials.filter(
      (material) => material.type === "document" || material.type === "link"
    );

    const videoMaterials: LessonVideoItem[] = lessonMaterials
      .filter((material) => material.type === "video" && !!material.file_url)
      .map((material) => ({
        id: material.id,
        title: material.title,
        url: material.file_url!,
        source: "material",
      }));

    const hasLegacyVideo = !!lesson.video_url && !videoMaterials.some((video) => video.url === lesson.video_url);
    const videos = hasLegacyVideo
      ? [
          ...videoMaterials,
          {
            id: `legacy-${lesson.id}`,
            title: `${lesson.title} - Video legacy`,
            url: lesson.video_url!,
            source: "legacy" as const,
          },
        ]
      : videoMaterials;

    const lessonAssignments = assignments
      .filter((assignment) => assignment.assignment_type !== AssignmentType.TEST && assignment.lesson_id === lesson.id)
      .sort((a, b) => a.order_index - b.order_index);

    return {
      materials,
      videos,
      lessonAssignments,
    };
  };

  const lessonMatchesFilter = (lesson: Lesson, filter: LearningFilter) => {
    if (filter === "description" || filter === "home") return true;

    const { materials, videos, lessonAssignments } = getLearningItems(lesson);

    if (filter === "document") return materials.length > 0;
    if (filter === "assignments") return lessonAssignments.length > 0;
    return videos.length > 0;
  };

  const buildLessonContextQuery = (lesson: Lesson, selectedVideoUrl?: string, selectedVideoTitle?: string) => {
    if (!course) return "";

    const params = new URLSearchParams({
      courseId: course.id,
      courseSlug: course.slug,
      lessonTitle: lesson.title,
    });

    const resolvedVideoUrl = selectedVideoUrl || lesson.video_url;
    if (resolvedVideoUrl) {
      params.set("videoUrl", resolvedVideoUrl);
    }

    if (selectedVideoTitle) {
      params.set("videoTitle", selectedVideoTitle);
    }

    return params.toString();
  };

  const isLessonCollapsed = (lessonId: string) => collapsedLessonIds.has(lessonId);

  const toggleLessonCollapse = (lessonId: string) => {
    setCollapsedLessonIds((prev) => {
      const next = new Set(prev);
      if (next.has(lessonId)) {
        next.delete(lessonId);
      } else {
        next.add(lessonId);
      }
      return next;
    });
  };

  const renderLessonLearningPaths = (lesson: Lesson, index: number) => {
    const { materials, videos, lessonAssignments } = getLearningItems(lesson);
    const isCollapsed = isLessonCollapsed(lesson.id);
    const showMaterials = materials.length > 0 && (learningFilter === "home" || learningFilter === "document");
    const showVideo = videos.length > 0 && (learningFilter === "home" || learningFilter === "classroom");
    const showAssignment = lessonAssignments.length > 0 && (learningFilter === "home" || learningFilter === "assignments");
    const hasAnyLearningContent = showMaterials || showVideo || showAssignment;

    return (
      <div key={lesson.id} className="rounded-xl border border-slate-200 bg-white overflow-hidden">
        <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
              {index + 1}
            </div>
            <div>
              <p className="font-semibold">{lesson.title}</p>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                {lesson.is_preview && (
                  <Badge variant="outline" className="text-xs">Xem trước</Badge>
                )}
                {!lesson.is_published && (
                  <Badge variant="secondary" className="text-xs">Nháp</Badge>
                )}
              </div>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => toggleLessonCollapse(lesson.id)}
          >
            {isCollapsed ? (
              <>
                <ChevronDown className="h-4 w-4 mr-1" />
                
              </>
            ) : (
              <>
                <ChevronUp className="h-4 w-4 mr-1" />
                
              </>
            )}
          </Button>
        </div>

        {!isCollapsed && (
          <div className="p-4 space-y-4">
            {showMaterials && (
              <div className="space-y-2 rounded-lg border border-blue-100 bg-blue-50/40 p-3">
                <p className="text-sm font-semibold text-blue-900">Tài liệu của Lesson</p>
                <div className="space-y-2">
                  {materials.map((material) => (
                    <Link
                      key={material.id}
                      href={`/lessons/${lesson.id}/materials/${material.id}?${buildLessonContextQuery(lesson)}`}
                      className="w-full border rounded-md px-3 py-2 bg-white hover:bg-gray-50 flex items-center justify-between"
                    >
                      <span className="flex items-center gap-2 text-sm font-medium">
                        <FileText className="h-4 w-4" />
                        {material.title}
                      </span>
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {showVideo && (
              <div className="space-y-2 rounded-lg border border-emerald-100 bg-emerald-50/40 p-3">
                <p className="text-sm font-semibold text-emerald-900">Buổi học trực tiếp</p>
                <div className="space-y-2">
                  {videos.map((video, videoIndex) => (
                    <Link
                      key={video.id}
                      href={`/lessons/${lesson.id}/video?${buildLessonContextQuery(lesson, video.url, video.title)}`}
                      className="w-full border rounded-md px-3 py-2 bg-white hover:bg-gray-50 flex items-center justify-between"
                    >
                      <span className="flex items-center gap-2 text-sm font-medium">
                        <Video className="h-4 w-4" />
                        {video.title || `Buổi học ${videoIndex + 1}`}
                      </span>
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </Link>
                  ))}
                </div>
              </div>
            )}

              {showAssignment && (
                <div className="space-y-2 rounded-lg border border-amber-100 bg-amber-50/40 p-3">
                  <p className="text-sm font-semibold text-amber-900">Bài tập của Lesson</p>
                  <div className="space-y-2">
                    {lessonAssignments.map((assignment, assignmentIndex) => (
                      <Link
                        key={assignment.id}
                        href={`/lessons/${lesson.id}/assignment?${buildLessonContextQuery(lesson)}&assignmentId=${assignment.id}`}
                        className="w-full border rounded-md px-3 py-2 bg-white hover:bg-gray-50 flex items-center justify-between"
                      >
                        <span className="flex items-center gap-2 text-sm font-medium">
                          <ClipboardList className="h-4 w-4" />
                          {assignment.title || `Bài tập ${assignmentIndex + 1}`}
                        </span>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </Link>
                    ))}
                  </div>
                </div>
              )}

            {!hasAnyLearningContent && (
              <p className="text-sm text-muted-foreground italic">
                  {learningFilter === "document"
                    ? "Lesson này chưa có tài liệu."
                    : learningFilter === "assignments"
                      ? "Lesson này chưa có bài tập."
                      : learningFilter === "classroom"
                        ? "Lesson này chưa có bài giảng video."
                        : "Lesson này chưa có tài liệu, video hoặc bài tập."}
              </p>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderLearningFilterControls = () => (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 md:sticky md:top-6">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-600">Điều hướng khóa học</p>
      <div className="space-y-2">
      {learningFilterOptions.map((option) => (
        <Button
          key={option.value}
          type="button"
          size="sm"
          className="w-full justify-start"
          variant={learningFilter === option.value ? "default" : "outline"}
          onClick={() => setLearningFilter(option.value)}
        >
          {option.label}
        </Button>
      ))}
      </div>
    </div>
  );

  const renderDescriptionSection = () => (
    <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-4">
      <div>
        <h3 className="text-base font-semibold text-slate-900">Mô tả khóa học</h3>
        <p className="mt-2 text-sm text-muted-foreground whitespace-pre-wrap">
          {course?.description || "Khóa học hiện chưa có mô tả chi tiết."}
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Badge variant="outline">{course?.level || "Không xác định cấp độ"}</Badge>
        <Badge variant="outline">{course?.category || "Không xác định danh mục"}</Badge>
        <Badge variant="secondary">{lessons.length} lesson</Badge>
      </div>
    </div>
  );

  const renderCourseMaterialSection = () => (
    <div className="space-y-3 rounded-xl border border-indigo-200 bg-indigo-50/40 p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-base font-semibold text-indigo-900">Tài liệu môn học</p>
          <p className="text-xs text-muted-foreground">Các tài liệu chung cho toàn bộ khóa học</p>
        </div>
        {canEdit && (
          <Button size="sm" variant="outline" onClick={() => handleOpenMaterialDialog()}>
            <Upload className="h-4 w-4 mr-2" />
            Tải tài liệu khóa học
          </Button>
        )}
      </div>
      {courseMaterials.length === 0 ? (
        <p className="text-sm text-muted-foreground">Chưa có tài liệu cấp khóa học</p>
      ) : (
        <div className="space-y-2">
          {courseMaterials.map((material) => {
            const content = material.file_url ? (
              <a
                href={material.file_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 w-full border rounded-md px-3 py-2 bg-white hover:bg-gray-50 flex items-center justify-between"
              >
                <span className="flex items-center gap-2 text-sm font-medium">
                  <FileText className="h-4 w-4" />
                  {material.title}
                </span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </a>
            ) : (
              <div className="flex-1 w-full border rounded-md px-3 py-2 bg-white text-sm text-muted-foreground">
                {material.title}
              </div>
            );

            return (
              <div key={material.id} className="flex items-center gap-2">
                {content}
                {canEdit && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-red-600 hover:text-red-700"
                    onClick={() => handleDeleteMaterial(material.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  const renderCourseTestSection = () => {
    const courseTests = assignments
      .filter((assignment) => assignment.assignment_type === AssignmentType.TEST)
      .sort((a, b) => a.order_index - b.order_index);

    return (
      <div className="space-y-3 rounded-xl border border-rose-200 bg-rose-50/40 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-base font-semibold text-rose-900">Bài kiểm tra</p>
            <p className="text-xs text-muted-foreground">Bài kiểm tra cấp khóa học, không thuộc lesson riêng lẻ</p>
          </div>
          {canEdit && (
            <Button size="sm" variant="outline" onClick={handleOpenTestDialog}>
              <ClipboardCheck className="h-4 w-4 mr-2" />
              Tạo bài kiểm tra
            </Button>
          )}
        </div>

        {courseTests.length === 0 ? (
          <p className="text-sm text-muted-foreground">Chưa có bài kiểm tra cấp khóa học</p>
        ) : (
          <div className="space-y-2">
            {courseTests.map((assignment, index) => (
              <div key={assignment.id} className="flex items-center gap-2">
                <Link
                  href={`/courses/${course?.slug}/tests/${assignment.id}`}
                  className="flex-1 border rounded-md px-3 py-2 bg-white hover:bg-gray-50 flex items-center justify-between"
                >
                  <span className="flex items-center gap-2 text-sm font-medium">
                    <ClipboardCheck className="h-4 w-4" />
                    {assignment.title || `Bài kiểm tra ${index + 1}`}
                    {!assignment.is_published && <Badge variant="secondary">Nháp</Badge>}
                  </span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </Link>
                {canEdit && !assignment.is_published && (
                  <Button size="sm" variant="outline" onClick={() => handlePublishTest(assignment.id)}>
                    Xuất bản
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4" />
        <div className="h-64 bg-gray-200 rounded" />
        <div className="h-32 bg-gray-200 rounded" />
      </div>
    );
  }

  if (error || !course) {
    return (
      <Card className="p-12 text-center">
        <BookOpen className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
        <h3 className="text-xl font-medium mb-2">Không tìm thấy khóa học</h3>
        <p className="text-muted-foreground mb-4">{error}</p>
        <Button asChild>
          <Link href="/courses">Quay lại danh sách</Link>
        </Button>
      </Card>
    );
  }

  const isInstructor = user?.id === course.instructor_id;
  const isAdmin = user?.role === UserRole.ADMIN;
  const canEdit = isInstructor || isAdmin;
  const filteredLessons = lessons.filter((lesson) => lessonMatchesFilter(lesson, learningFilter));
  const activeFilterLabel = learningFilterOptions.find((option) => option.value === learningFilter)?.label || "Home";
  const lessonCountDescription =
    learningFilter === "home"
      ? `${lessons.length} bài học`
      : learningFilter === "description"
        ? "Thông tin khóa học"
      : `${filteredLessons.length}/${lessons.length} bài học phù hợp`;

  return (
    <div className="space-y-4">
      {/* Back button */}
      <Button variant="ghost" onClick={() => router.back()}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Quay lại
      </Button>

      <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <Link href="/courses" className="hover:text-foreground">
          Khóa học
        </Link>
        <span>&gt;</span>
        <span>{course.title}</span>
        <span>&gt;</span>
        <span className="font-medium text-foreground">{activeFilterLabel}</span>
      </div>

      {/* Course Header */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="space-y-6">
          {/* Course Info */}
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Môn học</p>
                <h1 className="text-2xl font-semibold text-slate-900">{course.title}</h1>
                <div className="flex gap-2 flex-wrap">
                  <Badge variant={course.status === "published" ? "default" : "secondary"}>
                    {course.status === "published" ? "Đã xuất bản" : "Nháp"}
                  </Badge>
                  {course.level && <Badge variant="outline">{course.level}</Badge>}
                  {course.category && <Badge variant="outline">{course.category}</Badge>}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
                  {lessons.length} buổi học
                </div>
              </div>
            </div>
          </div>

          {/* Course Content - Tabs for Teacher/Admin */}
          {canEdit ? (
            <Tabs defaultValue="lessons" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="lessons">Danh sách bài học</TabsTrigger>
                <TabsTrigger value="manage">Quản lý bài học</TabsTrigger>
              </TabsList>
              
              <TabsContent value="lessons">
                <Card>
                  <CardHeader>
                    <CardTitle>Nội dung khóa học</CardTitle>
                    <CardDescription>{lessonCountDescription}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[220px_minmax(0,1fr)]">
                      {renderLearningFilterControls()}

                      <div>
                        {learningFilter === "description" ? (
                          renderDescriptionSection()
                        ) : (
                          <>
                            {(learningFilter === "home" || learningFilter === "document") && renderCourseMaterialSection()}
                            {(learningFilter === "home" || learningFilter === "assignments") && (
                              <div className="mt-4">{renderCourseTestSection()}</div>
                            )}
                            <div className="mt-6 mb-3">
                              <h3 className="text-sm font-semibold text-slate-800">Nội dung theo từng Lesson</h3>
                              <p className="text-xs text-muted-foreground">Mỗi lesson có tài liệu, video và bài tập riêng</p>
                            </div>
                            {lessons.length === 0 ? (
                              <p className="text-muted-foreground text-center py-8">
                                Chưa có bài học nào. Chuyển sang tab &quot;Quản lý bài học&quot; để tạo.
                              </p>
                            ) : filteredLessons.length === 0 ? (
                              <p className="text-muted-foreground text-center py-8">
                                Không có nội dung phù hợp với bộ lọc hiện tại.
                              </p>
                            ) : (
                              <div className="space-y-5">
                                {filteredLessons.map((lesson, index) => renderLessonLearningPaths(lesson, index))}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="manage">
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Quản lý bài học</CardTitle>
                        <CardDescription>
                          Danh sách lesson tổng quan. Bấm &quot;Mở Lesson Studio&quot; để quản lý chi tiết video, tài liệu và assignment.
                        </CardDescription>
                      </div>
                      <Button onClick={() => handleOpenLessonDialog()}>
                        <Plus className="h-4 w-4 mr-2" />
                        Thêm bài học
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {lessons.length === 0 ? (
                      <div className="text-center py-12">
                        <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                        <h3 className="text-lg font-medium mb-2">Chưa có bài học</h3>
                        <p className="text-muted-foreground mb-4">
                          Bắt đầu bằng việc tạo bài học đầu tiên cho khóa học này
                        </p>
                        <Button onClick={() => handleOpenLessonDialog()}>
                          <Plus className="h-4 w-4 mr-2" />
                          Tạo bài học đầu tiên
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {lessons.map((lesson, index) => {
                          const { materials: lessonDocuments, videos: lessonVideos, lessonAssignments } = getLearningItems(lesson);

                          return (
                          <div
                            key={lesson.id}
                            className="p-4 border rounded-lg space-y-4"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <div className="flex items-center gap-3">
                                <GripVertical className="h-5 w-5 text-muted-foreground cursor-move" />
                                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                                  {index + 1}
                                </div>
                                <div>
                                  <p className="font-medium">{lesson.title}</p>
                                  <div className="flex items-center gap-2 text-sm text-muted-foreground flex-wrap">
                                    <span>{lessonDocuments.length} tài liệu</span>
                                    <span>•</span>
                                    <span>{lessonAssignments.length} bài tập</span>
                                    <span>•</span>
                                    <span className="flex items-center gap-1">
                                      <Video className="h-3 w-3" /> {lessonVideos.length} buổi trực tiếp
                                    </span>
                                    {lesson.is_preview && (
                                      <Badge variant="outline" className="text-xs">Xem trước</Badge>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>

                            <div className="flex flex-wrap items-center gap-2">
                              <Button asChild>
                                <Link href={`/courses/${course.slug}/lessons/${lesson.id}/studio`}>
                                  <ChevronRight className="h-4 w-4 mr-2" />
                                  Mở Lesson Studio
                                </Link>
                              </Button>

                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleTogglePublish(lesson)}
                                title={lesson.is_published ? "Ẩn bài học" : "Xuất bản"}
                              >
                                {lesson.is_published ? (
                                  <>
                                    <Eye className="h-4 w-4 mr-2 text-green-600" />
                                    Đã xuất bản
                                  </>
                                ) : (
                                  <>
                                    <EyeOff className="h-4 w-4 mr-2 text-muted-foreground" />
                                    Đang nháp
                                  </>
                                )}
                              </Button>

                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleOpenLessonDialog(lesson)}
                              >
                                <Edit className="h-4 w-4 mr-2" />
                                Sửa lesson
                              </Button>

                              <Button
                                variant="outline"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                                onClick={() => setDeletingLessonId(lesson.id)}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Xóa lesson
                              </Button>
                            </div>
                          </div>
                          );
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          ) : (
            /* Regular Course Content for Students */
            <Card>
              <CardHeader>
                <CardTitle>Nội dung khóa học</CardTitle>
                <CardDescription>{lessonCountDescription}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-[220px_minmax(0,1fr)]">
                  {renderLearningFilterControls()}

                  <div>
                    {learningFilter === "description" ? (
                      renderDescriptionSection()
                    ) : (
                      <>
                        {(learningFilter === "home" || learningFilter === "document") && renderCourseMaterialSection()}
                        {(learningFilter === "home" || learningFilter === "assignments") && (
                          <div className="mt-4">{renderCourseTestSection()}</div>
                        )}
                        <div className="mt-6 mb-3">
                          <h3 className="text-sm font-semibold text-slate-800">Nội dung theo từng Lesson</h3>
                          <p className="text-xs text-muted-foreground">Mỗi lesson có tài liệu, video và bài tập riêng</p>
                        </div>
                        {lessons.length === 0 ? (
                          <p className="text-muted-foreground text-center py-8">
                            Chưa có bài học nào
                          </p>
                        ) : filteredLessons.length === 0 ? (
                          <p className="text-muted-foreground text-center py-8">
                            Không có nội dung phù hợp với bộ lọc hiện tại.
                          </p>
                        ) : (
                          <div className="space-y-5">
                            {filteredLessons.map((lesson, index) => renderLessonLearningPaths(lesson, index))}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Course Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle>Tổng quan khóa học</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                  <span>{lessons.length} bài học</span>
                </div>
                {course.estimated_duration && (
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>{Math.round(course.estimated_duration / 60)} giờ học</span>
                  </div>
                )}
              </div>

              {canEdit && (
                <div className="space-y-2">
                  <Button className="w-full" variant="outline" onClick={() => handleOpenLessonDialog()}>
                    <Plus className="h-4 w-4 mr-2" />
                    Thêm bài học mới
                  </Button>
                  <Button className="w-full" variant="outline" onClick={handleOpenTestDialog}>
                    <ClipboardCheck className="h-4 w-4 mr-2" />
                    Tạo bài kiểm tra
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Instructor Card */}
          <Card>
            <CardHeader>
              <CardTitle>Giảng viên</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3">
                <Avatar className="h-12 w-12">
                  <AvatarImage src={course.instructor.avatar_url || undefined} />
                  <AvatarFallback>
                    {getInitials(course.instructor.full_name)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium">{course.instructor.full_name}</p>
                  <p className="text-sm text-muted-foreground">{course.instructor.email}</p>
                </div>
              </div>
              {course.instructor.bio && (
                <p className="mt-4 text-sm text-muted-foreground">
                  {course.instructor.bio}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Lesson Dialog */}
      <Dialog open={showLessonDialog} onOpenChange={setShowLessonDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingLesson ? "Chỉnh sửa bài học" : "Thêm bài học mới"}
            </DialogTitle>
            <DialogDescription>
              {editingLesson 
                ? "Cập nhật thông tin bài học" 
                : "Tạo bài học mới cho khóa học này"
              }
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="lesson-title">Tiêu đề bài học *</Label>
              <Input
                id="lesson-title"
                value={lessonForm.title}
                onChange={(e) => setLessonForm({ ...lessonForm, title: e.target.value })}
                placeholder="Nhập tiêu đề bài học"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lesson-description">Mô tả ngắn</Label>
              <Input
                id="lesson-description"
                value={lessonForm.description}
                onChange={(e) => setLessonForm({ ...lessonForm, description: e.target.value })}
                placeholder="Mô tả ngắn về bài học"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lesson-content">Nội dung bài học</Label>
              <Textarea
                id="lesson-content"
                value={lessonForm.content}
                onChange={(e) => setLessonForm({ ...lessonForm, content: e.target.value })}
                placeholder="Nội dung chi tiết của bài học (hỗ trợ Markdown)"
                rows={6}
              />
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="lesson-preview"
                checked={lessonForm.is_preview}
                onCheckedChange={(checked) => setLessonForm({ ...lessonForm, is_preview: checked })}
              />
              <Label htmlFor="lesson-preview">
                Cho phép xem trước (không cần đăng ký)
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLessonDialog(false)} disabled={isSavingLesson}>
              Hủy
            </Button>
            <Button onClick={handleSaveLesson} disabled={isSavingLesson || !lessonForm.title.trim()}>
              {isSavingLesson ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Đang lưu...
                </>
              ) : (
                editingLesson ? "Cập nhật" : "Tạo bài học"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Lesson Confirmation */}
      <AlertDialog open={!!deletingLessonId} onOpenChange={() => setDeletingLessonId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xác nhận xóa bài học</AlertDialogTitle>
            <AlertDialogDescription>
              Bạn có chắc muốn xóa bài học này? Hành động này không thể hoàn tác.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deletingLessonId && handleDeleteLesson(deletingLessonId)}
              className="bg-red-600 hover:bg-red-700"
            >
              Xóa bài học
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Test Generation Dialog */}
      <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Tạo Bài kiểm tra</DialogTitle>
            <DialogDescription>
              Hệ thống chọn câu hỏi từ ngân hàng câu hỏi theo tỉ lệ độ khó 40/40/20 và phạm vi lesson đã chọn.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="test-title">Tiêu đề bài kiểm tra</Label>
              <Input
                id="test-title"
                value={testTitle}
                onChange={(event) => setTestTitle(event.target.value)}
                placeholder="Ví dụ: Kiểm tra giữa khóa"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="test-question-count">Số câu *</Label>
              <Input
                id="test-question-count"
                type="number"
                min={1}
                max={100}
                value={testQuestionCount}
                onChange={(event) => setTestQuestionCount(Number(event.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label>Khoanh vùng lesson</Label>
              <div className="max-h-56 space-y-2 overflow-y-auto rounded-md border p-3">
                {lessons.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Khóa học chưa có lesson.</p>
                ) : (
                  lessons.map((lesson, index) => {
                    const checked = testLessonIds.includes(lesson.id);
                    return (
                      <label key={lesson.id} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(event) => {
                            setTestLessonIds((prev) =>
                              event.target.checked
                                ? [...prev, lesson.id]
                                : prev.filter((lessonId) => lessonId !== lesson.id)
                            );
                          }}
                        />
                        <span>{index + 1}. {lesson.title}</span>
                      </label>
                    );
                  })
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Bỏ trống toàn bộ để lấy câu hỏi cấp khóa học từ mọi lesson.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTestDialog(false)} disabled={isGeneratingTest}>
              Hủy
            </Button>
            <Button
              onClick={handleGenerateTest}
              disabled={isGeneratingTest || testQuestionCount < 1 || testQuestionCount > 100}
            >
              {isGeneratingTest ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Đang tạo...
                </>
              ) : (
                "Tạo bài kiểm tra"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Material Upload Dialog */}
      <Dialog open={showMaterialDialog} onOpenChange={setShowMaterialDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Tải tài liệu cho Course</DialogTitle>
            <DialogDescription>Tài liệu này sẽ hiển thị ở cấp khóa học</DialogDescription>
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
              <div className="grid grid-cols-3 gap-2">
                {(["document", "link", "video"] as const).map((type) => (
                  <Button
                    key={type}
                    type="button"
                    variant={materialForm.type === type ? "default" : "outline"}
                    onClick={() =>
                      setMaterialForm((prev) => ({
                        ...prev,
                        type,
                        file: null,
                        externalUrl: "",
                        videoInputMode: type === "video" ? prev.videoInputMode : "url",
                      }))
                    }
                  >
                    {type}
                  </Button>
                ))}
              </div>
            </div>

            {materialForm.type === "document" && (
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
            )}

            {materialForm.type === "link" && (
              <div className="space-y-2">
                <Label htmlFor="material-external-url">URL tài liệu</Label>
                <Input
                  id="material-external-url"
                  value={materialForm.externalUrl}
                  onChange={(e) => setMaterialForm({ ...materialForm, externalUrl: e.target.value })}
                  placeholder="https://..."
                />
              </div>
            )}

            {materialForm.type === "video" && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Nguồn video (chọn 1)</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      type="button"
                      variant={materialForm.videoInputMode === "file" ? "default" : "outline"}
                      onClick={() =>
                        setMaterialForm((prev) => ({
                          ...prev,
                          videoInputMode: "file",
                          externalUrl: "",
                        }))
                      }
                    >
                      Upload file
                    </Button>
                    <Button
                      type="button"
                      variant={materialForm.videoInputMode === "url" ? "default" : "outline"}
                      onClick={() =>
                        setMaterialForm((prev) => ({
                          ...prev,
                          videoInputMode: "url",
                          file: null,
                        }))
                      }
                    >
                      Dùng URL
                    </Button>
                  </div>
                </div>

                {materialForm.videoInputMode === "file" ? (
                  <div className="space-y-2">
                    <Label htmlFor="material-video-file">Tải file video</Label>
                    <Input
                      id="material-video-file"
                      type="file"
                      accept="video/*"
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
                    <Label htmlFor="material-video-url">URL video</Label>
                    <Input
                      id="material-video-url"
                      value={materialForm.externalUrl}
                      onChange={(e) => setMaterialForm({ ...materialForm, externalUrl: e.target.value })}
                      placeholder="https://teams.microsoft.com/l/meetup-join/..."
                    />
                  </div>
                )}
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
                (materialForm.type === "link" && !materialForm.externalUrl.trim()) ||
                (materialForm.type === "video" &&
                  materialForm.videoInputMode === "file" &&
                  !materialForm.file) ||
                (materialForm.type === "video" &&
                  materialForm.videoInputMode === "url" &&
                  !materialForm.externalUrl.trim())
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
    </div>
  );
}
