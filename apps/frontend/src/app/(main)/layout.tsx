"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { 
  BookOpen, 
  ChevronsLeft,
  ChevronsRight,
  GraduationCap, 
  Home, 
  LogOut, 
  UserCircle2,
  Users,
  PlusCircle,
  FolderOpen,
  Menu,
  X
} from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/lib/auth/store";
import { authApi } from "@/lib/api";
import { UserRole } from "@/types";
import { cn } from "@/lib/utils";

interface NavItem {
  title: string;
  href: string;
  icon: React.ElementType;
  roles?: UserRole[];
}

const navItems: NavItem[] = [
  { title: "Tài khoản", href: "/profile", icon: UserCircle2 },
  { title: "Dashboard", href: "/dashboard", icon: Home },
  { title: "Khóa học", href: "/courses", icon: BookOpen },
  { title: "Khóa học của tôi", href: "/courses/my", icon: FolderOpen, roles: [UserRole.INSTRUCTOR, UserRole.ADMIN] },
  { title: "Tạo khóa học", href: "/courses/create", icon: PlusCircle, roles: [UserRole.INSTRUCTOR, UserRole.ADMIN] },
  { title: "Đã đăng ký", href: "/courses/enrolled", icon: GraduationCap, roles: [UserRole.LEARNER] },
  { title: "Quản lý Users", href: "/users", icon: Users, roles: [UserRole.ADMIN] },
];

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, _hasHydrated, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);

  useEffect(() => {
    // Wait for zustand persist to hydrate before checking auth
    if (_hasHydrated && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, _hasHydrated, router]);

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore logout errors
    }
    logout();
    router.push("/login");
  };

  const filteredNavItems = navItems.filter((item) => {
    if (!item.roles) return true;
    return user && item.roles.includes(user.role);
  });

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  // Show loading while hydrating
  if (!_hasHydrated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Đang tải...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-all duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-auto lg:transition-[width]",
          sidebarCollapsed ? "lg:w-28" : "lg:w-64",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className={cn("flex items-center border-b h-16", sidebarCollapsed ? "justify-center px-2 lg:h-20" : "justify-between px-6")}>
            <Link
              href="/dashboard"
              className={cn("flex items-center", sidebarCollapsed ? "lg:flex-col lg:justify-center lg:gap-1 lg:w-full" : "space-x-2")}
            >
              <GraduationCap className="h-8 w-8 text-primary" />
              <span className={cn("font-bold", sidebarCollapsed ? "text-[11px] leading-tight tracking-wide" : "text-xl")}>
                AI-LMS
              </span>
            </Link>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className={cn("flex-1 py-4 space-y-1 overflow-y-auto", sidebarCollapsed ? "px-2" : "px-4")}>
            {filteredNavItems.map((item) => {
              const Icon = item.icon;
              const isAccountItem = item.href === "/profile";
              const isActive = isAccountItem ? pathname.startsWith("/profile") : pathname === item.href;
              const itemClassName = cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                sidebarCollapsed && "lg:flex-col lg:justify-center lg:gap-1 lg:px-1 lg:py-3 lg:min-h-[72px]",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-gray-600 hover:bg-gray-100"
              );

              if (isAccountItem) {
                return (
                  <DropdownMenu key={item.href}>
                    <DropdownMenuTrigger asChild>
                      <button
                        type="button"
                        className={cn(itemClassName, "w-full")}
                        aria-label="Mở menu tài khoản"
                      >
                        <Icon className={cn("h-5 w-5 shrink-0", sidebarCollapsed && "lg:h-7 lg:w-7")} />
                        <span
                          className={cn(
                            "truncate",
                            sidebarCollapsed && "lg:block lg:text-[11px] lg:leading-tight lg:text-center lg:line-clamp-2 lg:px-1"
                          )}
                        >
                          {item.title}
                        </span>
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                      side={sidebarCollapsed ? "right" : "bottom"}
                      align={sidebarCollapsed ? "start" : "center"}
                      className="w-64"
                    >
                      <DropdownMenuLabel className="font-normal">
                        <div className="flex flex-col space-y-1">
                          <p className="text-sm font-medium">{user.full_name}</p>
                          <p className="text-xs text-muted-foreground">{user.email}</p>
                        </div>
                      </DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem asChild>
                        <Link href="/profile" onClick={() => setSidebarOpen(false)}>
                          <UserCircle2 className="mr-2 h-4 w-4" />
                          <span>Tùy chỉnh Thông tin cá nhân</span>
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                        <LogOut className="mr-2 h-4 w-4" />
                        <span>Đăng xuất</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                );
              }

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={itemClassName}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon className={cn("h-5 w-5 shrink-0", sidebarCollapsed && "lg:h-7 lg:w-7")} />
                  <span
                    className={cn(
                      "truncate",
                      sidebarCollapsed && "lg:block lg:text-[11px] lg:leading-tight lg:text-center lg:line-clamp-2 lg:px-1"
                    )}
                  >
                    {item.title}
                  </span>
                </Link>
              );
            })}
          </nav>

          {/* User Info */}
          <div className={cn("p-4 border-t", sidebarCollapsed && "lg:px-2 lg:py-3")}>
            <div className={cn("flex items-center space-x-3", sidebarCollapsed && "lg:justify-center lg:space-x-0")}>
              <Avatar>
                <AvatarImage src={user.avatar_url || undefined} />
                <AvatarFallback>{getInitials(user.full_name)}</AvatarFallback>
              </Avatar>
              <div className={cn("flex-1 min-w-0", sidebarCollapsed && "lg:hidden")}>
                <p className="text-sm font-medium truncate">{user.full_name}</p>
                <p className="text-xs text-gray-500 capitalize">{user.role}</p>
              </div>
            </div>
          </div>

          <div className={cn("border-t p-3 flex justify-center", sidebarCollapsed && "lg:px-2")}>
            <Button
              variant="secondary"
              className={cn(
                "hidden lg:inline-flex",
                sidebarCollapsed ? "h-12 w-12" : "h-10 w-10"
              )}
              onClick={() => setSidebarCollapsed((prev) => !prev)}
              title={sidebarCollapsed ? "Mở rộng thanh điều hướng" : "Thu gọn thanh điều hướng"}
            >
              {sidebarCollapsed ? (
                <ChevronsRight className="h-5 w-5" />
              ) : (
                <ChevronsLeft className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <div className="mb-4 lg:hidden">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setSidebarOpen(true)}
              aria-label="Mở thanh điều hướng"
            >
              <Menu className="h-5 w-5" />
            </Button>
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}
