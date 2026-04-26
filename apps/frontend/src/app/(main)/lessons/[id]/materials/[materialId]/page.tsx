"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download, ExternalLink, FileText, Loader2 } from "lucide-react";

import { lessonApi, Material } from "@/lib/api/lessons";
import { courseApi } from "@/lib/api";
import { CourseDetail } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const IMAGE_MIME_PREFIX = "image/";

export default function MaterialPreviewPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const lessonId = params.id as string;
  const materialId = params.materialId as string;
  const courseId = searchParams.get("courseId");
  const courseSlug = searchParams.get("courseSlug");
  const lessonTitleParam = searchParams.get("lessonTitle") || "Bài học";

  const [material, setMaterial] = useState<Material | null>(null);
  const [lessonTitle, setLessonTitle] = useState("");
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const materials = await lessonApi.getMaterials(lessonId);
        const targetMaterial = materials.find((item) => item.id === materialId);
        if (!targetMaterial) {
          setError("Không tìm thấy tài liệu");
          return;
        }
        setMaterial(targetMaterial);
        setLessonTitle(lessonTitleParam);

        if (courseId) {
          try {
            const courseData = await courseApi.getById(courseId);
            setCourse(courseData);
          } catch {
            // Course details are optional for this page.
          }
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || "Không thể tải tài liệu");
      } finally {
        setIsLoading(false);
      }
    };

    if (lessonId && materialId) {
      fetchData();
    }
  }, [lessonId, materialId, courseId, lessonTitleParam]);

  const previewType = useMemo(() => {
    if (!material?.file_url) return "unsupported" as const;

    const mime = material.mime_type || "";
    const lowerUrl = material.file_url.toLowerCase();

    if (mime.startsWith(IMAGE_MIME_PREFIX)) return "image" as const;
    if (mime.includes("pdf") || lowerUrl.endsWith(".pdf")) return "pdf" as const;

    if (
      lowerUrl.endsWith(".doc") ||
      lowerUrl.endsWith(".docx") ||
      lowerUrl.endsWith(".ppt") ||
      lowerUrl.endsWith(".pptx") ||
      lowerUrl.endsWith(".xls") ||
      lowerUrl.endsWith(".xlsx")
    ) {
      return "office" as const;
    }

    if (material.type === "link") return "link" as const;

    return "iframe" as const;
  }, [material]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !material) {
    return (
      <Card className="p-10 text-center">
        <CardTitle className="mb-3">Không thể mở tài liệu</CardTitle>
        <CardDescription className="mb-4">{error || "Dữ liệu không hợp lệ"}</CardDescription>
        <Button onClick={() => router.back()}>Quay lại</Button>
      </Card>
    );
  }

  const externalPreviewUrl =
    previewType === "office"
      ? `https://docs.google.com/gview?embedded=1&url=${encodeURIComponent(material.file_url || "")}`
      : material.file_url || "";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          {course && <Link href={`/courses/${course.slug}`}>{course.title}</Link>}
          {!course && courseSlug && <Link href={`/courses/${courseSlug}`}>Khóa học</Link>}
          {(course || courseSlug) && <span>&gt;</span>}
          <span>{lessonTitle || "Bài học"}</span>
          <span>&gt;</span>
          <span className="text-foreground font-medium">Tài liệu</span>
        </div>

        {material.file_url && (
          <Button asChild>
            <a href={material.file_url} target="_blank" rel="noopener noreferrer" download>
              <Download className="h-4 w-4 mr-2" />
              Tải xuống
            </a>
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {material.title}
          </CardTitle>
          {material.description && <CardDescription>{material.description}</CardDescription>}
        </CardHeader>
        <CardContent>
          {!material.file_url ? (
            <p className="text-sm text-muted-foreground">Tài liệu không có đường dẫn xem trước.</p>
          ) : previewType === "image" ? (
            <img
              src={material.file_url}
              alt={material.title}
              className="w-full max-h-[70vh] object-contain rounded-md border bg-white"
            />
          ) : previewType === "pdf" ? (
            <iframe
              src={`${material.file_url}#toolbar=1`}
              className="w-full h-[75vh] rounded-md border"
              title={material.title}
            />
          ) : previewType === "office" || previewType === "iframe" ? (
            <iframe
              src={externalPreviewUrl}
              className="w-full h-[75vh] rounded-md border"
              title={material.title}
            />
          ) : (
            <div className="rounded-md border p-6 text-center space-y-3">
              <p className="text-muted-foreground">Định dạng này chưa hỗ trợ xem trước trực tiếp.</p>
              <Button asChild variant="outline">
                <a href={material.file_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Mở tài liệu ở tab mới
                </a>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
