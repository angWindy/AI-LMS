"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, GraduationCap, Users, TrendingUp, Clock, Settings, Shield, Activity } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/lib/auth/store";
import { courseApi, userApi } from "@/lib/api";
import { UserRole, Course, User } from "@/types";

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [courses, setCourses] = useState<Course[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [totalCourses, setTotalCourses] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (user?.role === UserRole.ADMIN) {
          // Admin: fetch all data
          const [usersData, coursesResponse] = await Promise.all([
            userApi.getAll(),
            courseApi.getAll()
          ]);
          setAllUsers(usersData);
          setCourses(coursesResponse.items);
          setTotalCourses(coursesResponse.total);
        } else if (user?.role === UserRole.LEARNER) {
          const enrolled = await courseApi.getEnrolledCourses();
          setCourses(enrolled);
        } else if (user?.role === UserRole.INSTRUCTOR) {
          const myCourses = await courseApi.getMyCourses();
          setCourses(myCourses);
        }
      } catch (err) {
        console.error("Failed to fetch data:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user]);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Chào buổi sáng";
    if (hour < 18) return "Chào buổi chiều";
    return "Chào buổi tối";
  };

  const getRoleLabel = (role: UserRole) => {
    switch (role) {
      case UserRole.ADMIN:
        return "Quản trị viên";
      case UserRole.INSTRUCTOR:
        return "Giảng viên";
      case UserRole.LEARNER:
        return "Học viên";
    }
  };

  // Admin Dashboard
  if (user?.role === UserRole.ADMIN) {
    const totalUsers = allUsers.length;
    const adminCount = allUsers.filter(u => u.role === UserRole.ADMIN).length;
    const instructorCount = allUsers.filter(u => u.role === UserRole.INSTRUCTOR).length;
    const learnerCount = allUsers.filter(u => u.role === UserRole.LEARNER).length;
    const activeUsers = allUsers.filter(u => u.is_active).length;

    return (
      <div className="space-y-6">
        {/* Admin Welcome Section */}
        <div className="bg-gradient-to-r from-red-600 to-pink-600 rounded-xl p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="h-8 w-8" />
            <h1 className="text-2xl font-bold">
              {getGreeting()}, {user?.full_name}! 👋
            </h1>
          </div>
          <p className="text-red-100">
            Bảng điều khiển quản trị viên - Quản lý toàn bộ hệ thống AI-LMS
          </p>
        </div>

        {/* System Stats */}
        <div>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Thống kê hệ thống
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <Card className="border-blue-200 bg-blue-50">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-blue-700">Tổng người dùng</CardTitle>
                <Users className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-900">{totalUsers}</div>
                <p className="text-xs text-blue-600">{activeUsers} đang hoạt động</p>
              </CardContent>
            </Card>

            <Card className="border-red-200 bg-red-50">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-red-700">Admin</CardTitle>
                <Shield className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-900">{adminCount}</div>
                <p className="text-xs text-red-600">Quản trị viên</p>
              </CardContent>
            </Card>

            <Card className="border-purple-200 bg-purple-50">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-purple-700">Giảng viên</CardTitle>
                <GraduationCap className="h-4 w-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-900">{instructorCount}</div>
                <p className="text-xs text-purple-600">Người dạy</p>
              </CardContent>
            </Card>

            <Card className="border-green-200 bg-green-50">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-green-700">Học viên</CardTitle>
                <Users className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-900">{learnerCount}</div>
                <p className="text-xs text-green-600">Người học</p>
              </CardContent>
            </Card>

            <Card className="border-orange-200 bg-orange-50">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-orange-700">Khóa học</CardTitle>
                <BookOpen className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-900">{totalCourses}</div>
                <p className="text-xs text-orange-600">Tổng số khóa học</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Quick Actions for Admin */}
        <div>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Quản lý hệ thống
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Button asChild variant="outline" className="h-auto py-6 border-2">
              <Link href="/users" className="flex flex-col items-center">
                <Users className="h-8 w-8 mb-2 text-blue-600" />
                <span className="font-semibold">Quản lý người dùng</span>
                <span className="text-xs text-muted-foreground">{totalUsers} người dùng</span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto py-6 border-2">
              <Link href="/courses" className="flex flex-col items-center">
                <BookOpen className="h-8 w-8 mb-2 text-green-600" />
                <span className="font-semibold">Quản lý khóa học</span>
                <span className="text-xs text-muted-foreground">{totalCourses} khóa học</span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto py-6 border-2">
              <Link href="/courses/create" className="flex flex-col items-center">
                <GraduationCap className="h-8 w-8 mb-2 text-purple-600" />
                <span className="font-semibold">Tạo khóa học mới</span>
                <span className="text-xs text-muted-foreground">Thêm nội dung</span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto py-6 border-2">
              <Link href="/profile" className="flex flex-col items-center">
                <Settings className="h-8 w-8 mb-2 text-gray-600" />
                <span className="font-semibold">Cài đặt tài khoản</span>
                <span className="text-xs text-muted-foreground">Thông tin cá nhân</span>
              </Link>
            </Button>
          </div>
        </div>

        {/* Recent Users */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Người dùng mới nhất</h2>
            <Button variant="outline" asChild>
              <Link href="/users">Xem tất cả</Link>
            </Button>
          </div>
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="animate-pulse p-4">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gray-200 rounded-full" />
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-1/4" />
                      <div className="h-3 bg-gray-200 rounded w-1/3 mt-2" />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {allUsers.slice(0, 5).map((u) => (
                <Card key={u.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                        {u.full_name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium">{u.full_name}</p>
                        <p className="text-sm text-muted-foreground">{u.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={u.role === UserRole.ADMIN ? "destructive" : u.role === UserRole.INSTRUCTOR ? "default" : "secondary"}>
                        {getRoleLabel(u.role)}
                      </Badge>
                      {!u.is_active && (
                        <Badge variant="outline" className="text-red-500">Đã khóa</Badge>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Recent Courses */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Khóa học gần đây</h2>
            <Button variant="outline" asChild>
              <Link href="/courses">Xem tất cả</Link>
            </Button>
          </div>
          {courses.length === 0 ? (
            <Card className="p-8 text-center">
              <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">Chưa có khóa học nào</h3>
              <p className="text-muted-foreground mb-4">Hệ thống chưa có khóa học nào được tạo.</p>
              <Button asChild>
                <Link href="/courses/create">Tạo khóa học đầu tiên</Link>
              </Button>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {courses.slice(0, 3).map((course) => (
                <Link key={course.id} href={`/courses/${course.slug}`}>
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                    <div className="h-32 bg-gradient-to-br from-blue-500 to-purple-600 rounded-t-lg flex items-center justify-center">
                      <BookOpen className="h-12 w-12 text-white opacity-50" />
                    </div>
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-base line-clamp-1">{course.title}</CardTitle>
                        <Badge variant={course.status === "published" ? "default" : "secondary"} className="text-xs">
                          {course.status === "published" ? "Công khai" : "Nháp"}
                        </Badge>
                      </div>
                      <CardDescription className="line-clamp-2 text-xs">
                        {course.short_description || "Không có mô tả"}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Original Dashboard for Learner/Instructor
  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">
          {getGreeting()}, {user?.full_name}! 👋
        </h1>
        <p className="text-blue-100">
          Chào mừng bạn đến với AI-LMS. Vai trò của bạn: {user && getRoleLabel(user.role)}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Khóa học</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{courses.length}</div>
            <p className="text-xs text-muted-foreground">
              {user?.role === UserRole.LEARNER ? "Đang học" : "Đã tạo"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Bài học</CardTitle>
            <GraduationCap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-muted-foreground">Tổng số bài học</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Thời gian học</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-muted-foreground">Giờ học tập</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Tiến độ</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--%</div>
            <p className="text-xs text-muted-foreground">Hoàn thành trung bình</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Courses */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">
            {user?.role === UserRole.LEARNER ? "Đang học" : "Khóa học gần đây"}
          </h2>
          <Button variant="outline" asChild>
            <Link href="/courses">Xem tất cả</Link>
          </Button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="animate-pulse">
                <div className="h-40 bg-gray-200 rounded-t-lg" />
                <CardHeader>
                  <div className="h-4 bg-gray-200 rounded w-3/4" />
                  <div className="h-3 bg-gray-200 rounded w-1/2 mt-2" />
                </CardHeader>
              </Card>
            ))}
          </div>
        ) : courses.length === 0 ? (
          <Card className="p-8 text-center">
            <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">Chưa có khóa học nào</h3>
            <p className="text-muted-foreground mb-4">
              {user?.role === UserRole.LEARNER
                ? "Hãy khám phá và đăng ký các khóa học mới!"
                : "Bắt đầu tạo khóa học đầu tiên của bạn!"}
            </p>
            <Button asChild>
              <Link href={user?.role === UserRole.LEARNER ? "/courses" : "/courses/create"}>
                {user?.role === UserRole.LEARNER ? "Khám phá khóa học" : "Tạo khóa học"}
              </Link>
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.slice(0, 6).map((course) => (
              <Link key={course.id} href={`/courses/${course.slug}`}>
                <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                  <div className="h-40 bg-gradient-to-br from-blue-500 to-purple-600 rounded-t-lg flex items-center justify-center">
                    <BookOpen className="h-16 w-16 text-white opacity-50" />
                  </div>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg line-clamp-2">{course.title}</CardTitle>
                      <Badge variant={course.status === "published" ? "default" : "secondary"}>
                        {course.status === "published" ? "Đã xuất bản" : "Nháp"}
                      </Badge>
                    </div>
                    <CardDescription className="line-clamp-2">
                      {course.short_description || course.description || "Không có mô tả"}
                    </CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions - Only for Instructors (Admin has their own dashboard above) */}
      {user?.role === UserRole.INSTRUCTOR && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Hành động nhanh</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button asChild variant="outline" className="h-auto py-4">
              <Link href="/courses/create" className="flex flex-col items-center">
                <BookOpen className="h-6 w-6 mb-2" />
                <span>Tạo khóa học mới</span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto py-4">
              <Link href="/courses/my" className="flex flex-col items-center">
                <GraduationCap className="h-6 w-6 mb-2" />
                <span>Quản lý khóa học</span>
              </Link>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
