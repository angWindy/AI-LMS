"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, Play, Clock, TrendingUp, X, Loader2 } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { courseApi } from "@/lib/api";
import { Course } from "@/types";
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

export default function EnrolledCoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [unenrollCourse, setUnenrollCourse] = useState<Course | null>(null);
  const [isUnenrolling, setIsUnenrolling] = useState(false);

  const fetchCourses = async () => {
    try {
      const data = await courseApi.getEnrolledCourses();
      setCourses(data);
    } catch (err) {
      console.error("Failed to fetch enrolled courses:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  const handleUnenroll = async () => {
    if (!unenrollCourse) return;
    
    setIsUnenrolling(true);
    try {
      await courseApi.unenroll(unenrollCourse.id);
      setCourses(courses.filter(c => c.id !== unenrollCourse.id));
      setUnenrollCourse(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Không thể hủy đăng ký");
    } finally {
      setIsUnenrolling(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Khóa học đã đăng ký</h1>
          <p className="text-muted-foreground">Tiếp tục học các khóa học của bạn</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/courses">Khám phá thêm</Link>
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Đang học</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{courses.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Hoàn thành</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Thời gian học</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">-- giờ</div>
          </CardContent>
        </Card>
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
          <h3 className="text-xl font-medium mb-2">Chưa đăng ký khóa học nào</h3>
          <p className="text-muted-foreground mb-4">
            Khám phá và đăng ký các khóa học để bắt đầu học tập!
          </p>
          <Button asChild>
            <Link href="/courses">Khám phá khóa học</Link>
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <Card key={course.id} className="hover:shadow-lg transition-shadow h-full">
              <Link href={`/courses/${course.slug}`}>
                <div className="h-40 bg-gradient-to-br from-green-500 to-teal-600 rounded-t-lg flex items-center justify-center relative">
                  {course.thumbnail_url ? (
                    <img
                      src={course.thumbnail_url}
                      alt={course.title}
                      className="w-full h-full object-cover rounded-t-lg"
                    />
                  ) : (
                    <BookOpen className="h-16 w-16 text-white opacity-50" />
                  )}
                  {/* Play button overlay */}
                  <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 hover:opacity-100 transition-opacity">
                    <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center">
                      <Play className="h-6 w-6 text-primary ml-1" />
                    </div>
                  </div>
                </div>
              </Link>
              <CardHeader>
                <Link href={`/courses/${course.slug}`}>
                  <CardTitle className="text-lg line-clamp-2 hover:text-primary cursor-pointer">{course.title}</CardTitle>
                </Link>
                <CardDescription className="line-clamp-2">
                  {course.short_description || course.description || "Không có mô tả"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Progress bar */}
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Tiến độ</span>
                    <span className="font-medium">0%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary rounded-full transition-all"
                      style={{ width: "0%" }}
                    />
                  </div>
                </div>
                {/* Unenroll button */}
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
                  onClick={(e) => {
                    e.preventDefault();
                    setUnenrollCourse(course);
                  }}
                >
                  <X className="h-4 w-4 mr-2" />
                  Hủy đăng ký
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Unenroll Confirmation Dialog */}
      <AlertDialog open={!!unenrollCourse} onOpenChange={() => setUnenrollCourse(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xác nhận hủy đăng ký</AlertDialogTitle>
            <AlertDialogDescription>
              Bạn có chắc muốn hủy đăng ký khóa học &quot;{unenrollCourse?.title}&quot;? 
              Tiến độ học tập của bạn sẽ bị mất.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isUnenrolling}>Hủy</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleUnenroll}
              disabled={isUnenrolling}
              className="bg-red-600 hover:bg-red-700"
            >
              {isUnenrolling ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Đang xử lý...
                </>
              ) : (
                "Xác nhận hủy"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
