"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { ArrowLeft } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { courseApi } from "@/lib/api";

const courseSchema = z.object({
  title: z.string().min(3, "Tiêu đề phải có ít nhất 3 ký tự"),
  description: z.string().optional(),
  short_description: z.string().max(500, "Mô tả ngắn tối đa 500 ký tự").optional(),
  category: z.string().optional(),
  level: z.string().optional(),
  language: z.string(),
});

type CourseFormData = z.infer<typeof courseSchema>;

export default function CreateCoursePage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<CourseFormData>({
    resolver: zodResolver(courseSchema),
    defaultValues: {
      language: "vi",
      title: "",
    },
  });

  const onSubmit = async (data: CourseFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      const course = await courseApi.create(data);
      router.push(`/courses/${course.slug}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Tạo khóa học thất bại");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Back button */}
      <Button variant="ghost" onClick={() => router.back()}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Quay lại
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>Tạo khóa học mới</CardTitle>
          <CardDescription>
            Điền thông tin để tạo khóa học. Bạn có thể chỉnh sửa sau.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-6">
            {error && (
              <div className="p-3 text-sm text-red-500 bg-red-50 border border-red-200 rounded-md">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="title">Tiêu đề khóa học *</Label>
              <Input
                id="title"
                placeholder="VD: Lập trình Python cơ bản"
                {...register("title")}
              />
              {errors.title && (
                <p className="text-sm text-red-500">{errors.title.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="short_description">Mô tả ngắn</Label>
              <Input
                id="short_description"
                placeholder="Mô tả ngắn gọn về khóa học"
                {...register("short_description")}
              />
              {errors.short_description && (
                <p className="text-sm text-red-500">{errors.short_description.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Mô tả chi tiết</Label>
              <Textarea
                id="description"
                placeholder="Mô tả đầy đủ về nội dung khóa học..."
                rows={5}
                {...register("description")}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Danh mục</Label>
                <Select onValueChange={(value) => setValue("category", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn danh mục" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="programming">Lập trình</SelectItem>
                    <SelectItem value="design">Thiết kế</SelectItem>
                    <SelectItem value="business">Kinh doanh</SelectItem>
                    <SelectItem value="marketing">Marketing</SelectItem>
                    <SelectItem value="language">Ngoại ngữ</SelectItem>
                    <SelectItem value="other">Khác</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Trình độ</Label>
                <Select onValueChange={(value) => setValue("level", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn trình độ" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="beginner">Cơ bản</SelectItem>
                    <SelectItem value="intermediate">Trung cấp</SelectItem>
                    <SelectItem value="advanced">Nâng cao</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Ngôn ngữ</Label>
              <Select 
                defaultValue="vi"
                onValueChange={(value) => setValue("language", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Chọn ngôn ngữ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="vi">Tiếng Việt</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-4">
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "Đang tạo..." : "Tạo khóa học"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Hủy
              </Button>
            </div>
          </CardContent>
        </form>
      </Card>
    </div>
  );
}
