"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { BookOpen, Plus, Edit, Trash2, MoreVertical } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { courseApi } from "@/lib/api";
import { Course } from "@/types";

export default function MyCoursesPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const data = await courseApi.getMyCourses();
        setCourses(data);
      } catch (err) {
        console.error("Failed to fetch courses:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCourses();
  }, []);

  const handlePublish = async (courseId: string) => {
    try {
      await courseApi.publish(courseId);
      // Refresh list
      const data = await courseApi.getMyCourses();
      setCourses(data);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Không thể xuất bản khóa học");
    }
  };

  const handleDelete = async (courseId: string) => {
    if (!confirm("Bạn có chắc muốn xóa khóa học này?")) return;

    try {
      await courseApi.delete(courseId);
      setCourses(courses.filter((c) => c.id !== courseId));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Không thể xóa khóa học");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Khóa học của tôi</h1>
          <p className="text-muted-foreground">Quản lý các khóa học bạn đã tạo</p>
        </div>
        <Button asChild>
          <Link href="/courses/create">
            <Plus className="h-4 w-4 mr-2" />
            Tạo khóa học
          </Link>
        </Button>
      </div>

      {/* Course List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-40 bg-gray-200 rounded-t-lg" />
              <CardHeader>
                <div className="h-5 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-200 rounded w-1/2 mt-2" />
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : courses.length === 0 ? (
        <Card className="p-12 text-center">
          <BookOpen className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-xl font-medium mb-2">Chưa có khóa học nào</h3>
          <p className="text-muted-foreground mb-4">
            Bắt đầu tạo khóa học đầu tiên của bạn!
          </p>
          <Button asChild>
            <Link href="/courses/create">
              <Plus className="h-4 w-4 mr-2" />
              Tạo khóa học
            </Link>
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <Card
              key={course.id}
              className="overflow-hidden cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => router.push(`/courses/${course.slug}`)}
            >
              <div className="h-40 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center relative">
                {course.thumbnail_url ? (
                  <img
                    src={course.thumbnail_url}
                    alt={course.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <BookOpen className="h-16 w-16 text-white opacity-50" />
                )}
                {/* Actions dropdown */}
                <div className="absolute top-2 right-2">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="secondary"
                        size="icon"
                        className="h-8 w-8"
                        onClick={(event) => event.stopPropagation()}
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" onClick={(event) => event.stopPropagation()}>
                      <DropdownMenuItem onClick={() => router.push(`/courses/${course.slug}`)}>
                        <BookOpen className="h-4 w-4 mr-2" />
                        Xem
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Edit className="h-4 w-4 mr-2" />
                        Chỉnh sửa
                      </DropdownMenuItem>
                      {course.status === "draft" && (
                        <DropdownMenuItem onClick={() => handlePublish(course.id)}>
                          <BookOpen className="h-4 w-4 mr-2" />
                          Xuất bản
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem 
                        className="text-red-600"
                        onClick={() => handleDelete(course.id)}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Xóa
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-lg line-clamp-2">{course.title}</CardTitle>
                  <Badge variant={course.status === "published" ? "default" : "secondary"}>
                    {course.status === "published" ? "Đã xuất bản" : "Nháp"}
                  </Badge>
                </div>
                <CardDescription className="line-clamp-2">
                  {course.short_description || course.description || "Không có mô tả"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>Tạo: {new Date(course.created_at).toLocaleDateString("vi-VN")}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
