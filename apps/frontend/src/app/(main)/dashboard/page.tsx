"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BookOpen,
  GraduationCap,
  Library,
  PlusCircle,
  Settings,
  Shield,
  UserRound,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { courseApi, userApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth/store";
import { Course, User, UserRole } from "@/types";

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
          const [usersData, coursesResponse] = await Promise.all([
            userApi.getAll(),
            courseApi.getAll(),
          ]);
          setAllUsers(usersData);
          setCourses(coursesResponse.items);
          setTotalCourses(coursesResponse.total);
        } else if (user?.role === UserRole.LEARNER) {
          const coursesResponse = await courseApi.getAll();
          setCourses(coursesResponse.items);
          setTotalCourses(coursesResponse.total);
        } else if (user?.role === UserRole.INSTRUCTOR) {
          const myCourses = await courseApi.getMyCourses();
          setCourses(myCourses);
          setTotalCourses(myCourses.length);
        }
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user]);

  const roleLabel = useMemo(() => {
    switch (user?.role) {
      case UserRole.ADMIN:
        return "Quản trị viên";
      case UserRole.INSTRUCTOR:
        return "Giảng viên";
      case UserRole.LEARNER:
        return "Học viên";
      default:
        return "Người dùng";
    }
  }, [user?.role]);

  const publishedCourses = courses.filter((course) => course.status === "published").length;
  const draftCourses = courses.filter((course) => course.status === "draft").length;

  if (user?.role === UserRole.ADMIN) {
    const totalUsers = allUsers.length;
    const activeUsers = allUsers.filter((item) => item.is_active).length;
    const instructorCount = allUsers.filter((item) => item.role === UserRole.INSTRUCTOR).length;
    const learnerCount = allUsers.filter((item) => item.role === UserRole.LEARNER).length;

    return (
      <div className="space-y-6">
        <section className="rounded-lg border bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <Badge variant="secondary" className="mb-3">
                <Shield className="mr-1 h-3.5 w-3.5" />
                {roleLabel}
              </Badge>
              <h1 className="text-2xl font-semibold text-slate-950">Bảng điều khiển hệ thống</h1>
              <p className="mt-2 text-sm text-muted-foreground">
                Theo dõi người dùng, khóa học và các khu vực quản trị chính.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button asChild>
                <Link href="/users">
                  <Users className="mr-2 h-4 w-4" />
                  Quản lý người dùng
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/courses/create">
                  <PlusCircle className="mr-2 h-4 w-4" />
                  Tạo khóa học
                </Link>
              </Button>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard icon={Users} label="Người dùng" value={totalUsers} hint={`${activeUsers} tài khoản hoạt động`} />
          <MetricCard icon={GraduationCap} label="Giảng viên" value={instructorCount} hint="Tài khoản có quyền dạy" />
          <MetricCard icon={UserRound} label="Học viên" value={learnerCount} hint="Tài khoản học tập" />
          <MetricCard icon={BookOpen} label="Khóa học" value={totalCourses} hint={`${publishedCourses} khóa học công khai`} />
        </section>

        <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Người dùng mới nhất</CardTitle>
                <CardDescription>5 tài khoản gần đây trong hệ thống</CardDescription>
              </div>
              <Button asChild variant="ghost" size="sm">
                <Link href="/users">
                  Xem tất cả
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoading ? (
                <LoadingRows />
              ) : (
                allUsers.slice(0, 5).map((item) => (
                  <UserRow key={item.id} user={item} roleLabel={getRoleLabel(item.role)} />
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Khóa học gần đây</CardTitle>
                <CardDescription>Nội dung đang có trên nền tảng</CardDescription>
              </div>
              <Button asChild variant="ghost" size="sm">
                <Link href="/courses">
                  Mở danh sách
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent>
              <CourseList courses={courses.slice(0, 5)} isLoading={isLoading} emptyText="Chưa có khóa học nào." />
            </CardContent>
          </Card>
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <Badge variant="secondary" className="mb-3">
              <Activity className="mr-1 h-3.5 w-3.5" />
              {roleLabel}
            </Badge>
            <h1 className="text-2xl font-semibold text-slate-950">
              {user?.role === UserRole.INSTRUCTOR ? "Không gian giảng dạy" : "Không gian học tập"}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {user?.role === UserRole.INSTRUCTOR
                ? "Quản lý khóa học và tiếp tục xây dựng nội dung đang dạy."
                : "Xem nhanh các khóa học đang mở và tiếp tục học từ danh sách khóa học."}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {user?.role === UserRole.INSTRUCTOR && (
              <Button asChild>
                <Link href="/courses/create">
                  <PlusCircle className="mr-2 h-4 w-4" />
                  Tạo khóa học
                </Link>
              </Button>
            )}
            <Button asChild variant={user?.role === UserRole.INSTRUCTOR ? "outline" : "default"}>
              <Link href={user?.role === UserRole.INSTRUCTOR ? "/courses/my" : "/courses"}>
                <Library className="mr-2 h-4 w-4" />
                {user?.role === UserRole.INSTRUCTOR ? "Quản lý khóa học" : "Khám phá khóa học"}
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <MetricCard
          icon={BookOpen}
          label={user?.role === UserRole.INSTRUCTOR ? "Khóa học đã tạo" : "Khóa học có thể học"}
          value={totalCourses}
          hint={user?.role === UserRole.INSTRUCTOR ? `${draftCourses} bản nháp` : "Khóa học đang công khai"}
        />
        <MetricCard icon={Activity} label="Đang công khai" value={publishedCourses} hint="Có thể truy cập ngay" />
        <MetricCard
          icon={Settings}
          label="Tác vụ nhanh"
          value={user?.role === UserRole.INSTRUCTOR ? 2 : 1}
          hint={user?.role === UserRole.INSTRUCTOR ? "Tạo và quản lý khóa học" : "Mở danh mục khóa học"}
        />
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">
              {user?.role === UserRole.INSTRUCTOR ? "Khóa học gần đây" : "Khóa học có thể học"}
            </h2>
            <p className="text-sm text-muted-foreground">Danh sách rút gọn từ dữ liệu hiện có.</p>
          </div>
          <Button variant="outline" asChild>
            <Link href={user?.role === UserRole.INSTRUCTOR ? "/courses/my" : "/courses"}>Xem tất cả</Link>
          </Button>
        </div>
        <CourseGrid courses={courses.slice(0, 6)} isLoading={isLoading} userRole={user?.role} />
      </section>
    </div>
  );
}

function getRoleLabel(role: UserRole) {
  switch (role) {
    case UserRole.ADMIN:
      return "Quản trị viên";
    case UserRole.INSTRUCTOR:
      return "Giảng viên";
    case UserRole.LEARNER:
      return "Học viên";
  }
}

function MetricCard({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: typeof BookOpen;
  label: string;
  value: number;
  hint: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className="h-4 w-4 text-slate-500" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold text-slate-950">{value}</div>
        <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
      </CardContent>
    </Card>
  );
}

function UserRow({ user, roleLabel }: { user: User; roleLabel: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border p-3">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 font-medium text-slate-700">
          {user.full_name.charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">{user.full_name}</p>
          <p className="truncate text-xs text-muted-foreground">{user.email}</p>
        </div>
      </div>
      <div className="ml-3 flex shrink-0 items-center gap-2">
        <Badge variant={user.role === UserRole.ADMIN ? "destructive" : user.role === UserRole.INSTRUCTOR ? "default" : "secondary"}>
          {roleLabel}
        </Badge>
        {!user.is_active && <Badge variant="outline">Đã khóa</Badge>}
      </div>
    </div>
  );
}

function CourseList({
  courses,
  isLoading,
  emptyText,
}: {
  courses: Course[];
  isLoading: boolean;
  emptyText: string;
}) {
  if (isLoading) return <LoadingRows />;
  if (courses.length === 0) {
    return <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">{emptyText}</p>;
  }

  return (
    <div className="space-y-3">
      {courses.map((course) => (
        <Link
          key={course.id}
          href={`/courses/${course.slug}`}
          className="flex items-center justify-between rounded-md border p-3 transition-colors hover:bg-slate-50"
        >
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{course.title}</p>
            <p className="truncate text-xs text-muted-foreground">
              {course.short_description || course.description || "Chưa có mô tả"}
            </p>
          </div>
          <Badge variant={course.status === "published" ? "default" : "secondary"} className="ml-3 shrink-0">
            {course.status === "published" ? "Công khai" : "Nháp"}
          </Badge>
        </Link>
      ))}
    </div>
  );
}

function CourseGrid({
  courses,
  isLoading,
  userRole,
}: {
  courses: Course[];
  isLoading: boolean;
  userRole?: UserRole;
}) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {[1, 2, 3].map((item) => (
          <Card key={item} className="animate-pulse">
            <div className="h-28 rounded-t-lg bg-slate-100" />
            <CardHeader>
              <div className="h-4 w-3/4 rounded bg-slate-100" />
              <div className="mt-2 h-3 w-1/2 rounded bg-slate-100" />
            </CardHeader>
          </Card>
        ))}
      </div>
    );
  }

  if (courses.length === 0) {
    return (
      <Card className="p-8 text-center">
        <BookOpen className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
        <h3 className="mb-2 text-lg font-medium">Chưa có khóa học nào</h3>
        <p className="mb-4 text-muted-foreground">
          {userRole === UserRole.LEARNER ? "Hiện chưa có khóa học công khai nào." : "Bắt đầu tạo khóa học đầu tiên của bạn."}
        </p>
        <Button asChild>
          <Link href={userRole === UserRole.LEARNER ? "/courses" : "/courses/create"}>
            {userRole === UserRole.LEARNER ? "Khám phá khóa học" : "Tạo khóa học"}
          </Link>
        </Button>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      {courses.map((course) => (
        <Link key={course.id} href={`/courses/${course.slug}`}>
          <Card className="h-full transition-shadow hover:shadow-md">
            <div className="flex h-28 items-center justify-center rounded-t-lg bg-slate-100">
              <BookOpen className="h-10 w-10 text-slate-400" />
            </div>
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <CardTitle className="line-clamp-2 text-base">{course.title}</CardTitle>
                <Badge variant={course.status === "published" ? "default" : "secondary"} className="shrink-0">
                  {course.status === "published" ? "Công khai" : "Nháp"}
                </Badge>
              </div>
              <CardDescription className="line-clamp-2">
                {course.short_description || course.description || "Chưa có mô tả"}
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>
      ))}
    </div>
  );
}

function LoadingRows() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((item) => (
        <div key={item} className="animate-pulse rounded-md border p-3">
          <div className="h-4 w-2/3 rounded bg-slate-100" />
          <div className="mt-2 h-3 w-1/2 rounded bg-slate-100" />
        </div>
      ))}
    </div>
  );
}
