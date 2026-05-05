"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Maximize,
  Minimize,
  Loader2,
  Video,
  ClipboardList,
  FileText,
  MessageSquare,
  ExternalLink,
} from "lucide-react";

import { Lesson } from "@/lib/api/lessons";
import { assignmentApi, courseApi } from "@/lib/api";
import { Assignment, CourseDetail } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChatbotStore } from "@/components/chat/store";
import { TeachingImagePayload } from "@/lib/api/chatbot";

interface VideoRoomLesson {
  id: string;
  title: string;
  description?: string;
  video_url?: string;
  course_id?: string;
}

function getVideoEmbedUrl(url: string) {
  if (url.includes("youtube.com/watch")) {
    const videoId = new URL(url).searchParams.get("v");
    return videoId ? `https://www.youtube.com/embed/${videoId}` : url;
  }
  if (url.includes("youtu.be/")) {
    const videoId = url.split("youtu.be/")[1]?.split("?")[0];
    return videoId ? `https://www.youtube.com/embed/${videoId}` : url;
  }
  if (url.includes("vimeo.com")) {
    return url.replace("vimeo.com", "player.vimeo.com/video");
  }
  return url;
}

type LessonVideoSourceKind =
  | "youtube"
  | "vimeo"
  | "zoom"
  | "teams"
  | "google-meet"
  | "direct-file"
  | "web-embed";

const DIRECT_VIDEO_EXTENSIONS = [".mp4", ".webm", ".mov", ".m4v", ".ogg", ".m3u8"];

type ExtendedDisplayCaptureVideoConstraints = MediaTrackConstraints & {
  preferCurrentTab?: boolean;
  selfBrowserSurface?: "include" | "exclude";
  surfaceSwitching?: "include" | "exclude";
};

function tryParseUrl(url: string): URL | null {
  try {
    return new URL(url);
  } catch {
    return null;
  }
}

function detectLessonVideoSource(url: string): LessonVideoSourceKind {
  const normalized = url.trim().toLowerCase();
  const parsed = tryParseUrl(url);
  const host = parsed?.hostname.toLowerCase() || "";

  if (host.includes("youtube.com") || host.endsWith("youtu.be")) {
    return "youtube";
  }

  if (host.includes("vimeo.com")) {
    return "vimeo";
  }

  if (host.includes("zoom.us")) {
    return "zoom";
  }

  if (host.includes("teams.microsoft.com") || normalized.startsWith("msteams:")) {
    return "teams";
  }

  if (host.includes("meet.google.com")) {
    return "google-meet";
  }

  if (
    normalized.startsWith("blob:") ||
    normalized.startsWith("data:video") ||
    DIRECT_VIDEO_EXTENSIONS.some((extension) => normalized.includes(extension))
  ) {
    return "direct-file";
  }

  return "web-embed";
}

function isMeetingSource(kind: LessonVideoSourceKind) {
  return kind === "zoom" || kind === "teams" || kind === "google-meet";
}

function getMeetingPlatformLabel(kind: LessonVideoSourceKind | null) {
  if (kind === "zoom") return "Zoom";
  if (kind === "teams") return "Microsoft Teams";
  if (kind === "google-meet") return "Google Meet";
  return "nền tảng họp trực tuyến";
}

function formatPlaybackTime(seconds: number) {
  const totalSeconds = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const remainingSeconds = totalSeconds % 60;

  if (hours > 0) {
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
  }

  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function waitForVideoMetadata(video: HTMLVideoElement): Promise<void> {
  if (video.readyState >= 1) {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const cleanup = () => {
      video.onloadedmetadata = null;
      video.onerror = null;
    };

    video.onloadedmetadata = () => {
      cleanup();
      resolve();
    };

    video.onerror = () => {
      cleanup();
      reject(new Error("Không thể đọc metadata video screenshot."));
    };
  });
}

function toBase64FromDataUrl(dataUrl: string): string | null {
  const commaIndex = dataUrl.indexOf(",");
  if (commaIndex < 0) {
    return null;
  }
  return dataUrl.slice(commaIndex + 1);
}

export default function LessonVideoRoomPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const lessonId = params.id as string;
  const courseId = searchParams.get("courseId");
  const courseSlug = searchParams.get("courseSlug");
  const lessonTitle = searchParams.get("lessonTitle") || "Bài học";
  const lessonVideoUrl = searchParams.get("videoUrl") || "";

  const playerWrapperRef = useRef<HTMLDivElement>(null);
  const lessonVideoRef = useRef<HTMLVideoElement>(null);
  const screenCaptureStreamRef = useRef<MediaStream | null>(null);
  const screenCaptureVideoRef = useRef<HTMLVideoElement | null>(null);
  const screenCaptureSurfaceRef = useRef<string | null>(null);

  const [lesson, setLesson] = useState<VideoRoomLesson | null>(null);
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [lessonAssignments, setLessonAssignments] = useState<Assignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isChatbotPopupOpen, setIsChatbotPopupOpen] = useState(false);

  const stopScreenCaptureSession = useCallback(() => {
    screenCaptureStreamRef.current?.getTracks().forEach((track) => track.stop());
    screenCaptureStreamRef.current = null;

    if (screenCaptureVideoRef.current) {
      screenCaptureVideoRef.current.pause();
      screenCaptureVideoRef.current.srcObject = null;
      screenCaptureVideoRef.current = null;
    }

    screenCaptureSurfaceRef.current = null;
  }, []);

  const ensureScreenCaptureSession = useCallback(async (): Promise<HTMLVideoElement | null> => {
    const activeStream = screenCaptureStreamRef.current;
    const activeVideo = screenCaptureVideoRef.current;
    const activeTrack = activeStream?.getVideoTracks()[0];

    if (activeStream && activeVideo && activeTrack && activeTrack.readyState === "live") {
      if (activeVideo.paused) {
        await activeVideo.play().catch(() => null);
      }
      return activeVideo;
    }

    stopScreenCaptureSession();

    if (!navigator.mediaDevices?.getDisplayMedia) {
      return null;
    }

    const wasWrapperFullscreen =
      !!document.fullscreenElement &&
      !!playerWrapperRef.current &&
      document.fullscreenElement === playerWrapperRef.current;

    try {
      const captureVideoConstraints: ExtendedDisplayCaptureVideoConstraints = {
        displaySurface: "browser",
        frameRate: { max: 5 },
        preferCurrentTab: true,
        selfBrowserSurface: "include",
        surfaceSwitching: "include",
      };

      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: captureVideoConstraints,
        audio: false,
      });

      const track = stream.getVideoTracks()[0];
      const trackSettings = track?.getSettings();
      screenCaptureSurfaceRef.current = trackSettings?.displaySurface || null;

      const captureVideo = document.createElement("video");
      captureVideo.srcObject = stream;
      captureVideo.playsInline = true;
      captureVideo.muted = true;

      await waitForVideoMetadata(captureVideo);
      await captureVideo.play();

      track?.addEventListener("ended", () => {
        stopScreenCaptureSession();
      });

      screenCaptureStreamRef.current = stream;
      screenCaptureVideoRef.current = captureVideo;

      if (wasWrapperFullscreen && !document.fullscreenElement && playerWrapperRef.current) {
        await playerWrapperRef.current.requestFullscreen().catch(() => null);
      }

      return captureVideo;
    } catch (error) {
      console.error("Cannot initialize screen capture session:", error);
      stopScreenCaptureSession();
      return null;
    }
  }, [stopScreenCaptureSession]);

  const captureTeachingImage = useCallback(async (): Promise<TeachingImagePayload | null> => {
    const video = lessonVideoRef.current;
    if (video && video.videoWidth > 0 && video.videoHeight > 0) {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const context = canvas.getContext("2d");
      if (!context) {
        return null;
      }

      try {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const dataBase64 = toBase64FromDataUrl(canvas.toDataURL("image/jpeg", 0.9));
        if (!dataBase64) {
          return null;
        }

        return {
          mime_type: "image/jpeg",
          data_base64: dataBase64,
          description: `Lesson video frame for \"${lesson?.title || lessonTitle}\" at ${formatPlaybackTime(video.currentTime)}`,
          source: "lesson_video_frame",
        };
      } catch (error) {
        console.error("Unable to capture native lesson frame:", error);
      }
    }

    if (!navigator.mediaDevices?.getDisplayMedia) {
      return null;
    }

    try {
      const captureVideo = await ensureScreenCaptureSession();
      if (!captureVideo) {
        return null;
      }

      await new Promise((resolve) => requestAnimationFrame(() => resolve(null)));

      const sourceWidth = captureVideo.videoWidth;
      const sourceHeight = captureVideo.videoHeight;
      if (sourceWidth <= 0 || sourceHeight <= 0) {
        return null;
      }

      const sourceCanvas = document.createElement("canvas");
      sourceCanvas.width = sourceWidth;
      sourceCanvas.height = sourceHeight;

      const sourceContext = sourceCanvas.getContext("2d");
      if (!sourceContext) {
        return null;
      }
      sourceContext.drawImage(captureVideo, 0, 0, sourceWidth, sourceHeight);

      const wrapperRect = playerWrapperRef.current?.getBoundingClientRect();
      let cropX = 0;
      let cropY = 0;
      let cropWidth = sourceWidth;
      let cropHeight = sourceHeight;

      const canCropByPlayerBounds = screenCaptureSurfaceRef.current === "browser";
      if (
        canCropByPlayerBounds &&
        wrapperRect &&
        wrapperRect.width > 0 &&
        wrapperRect.height > 0 &&
        window.innerWidth > 0 &&
        window.innerHeight > 0
      ) {
        const scaleX = sourceWidth / window.innerWidth;
        const scaleY = sourceHeight / window.innerHeight;

        cropX = Math.max(0, Math.floor(wrapperRect.left * scaleX));
        cropY = Math.max(0, Math.floor(wrapperRect.top * scaleY));
        cropWidth = Math.max(1, Math.floor(wrapperRect.width * scaleX));
        cropHeight = Math.max(1, Math.floor(wrapperRect.height * scaleY));

        if (cropX + cropWidth > sourceWidth) {
          cropWidth = Math.max(1, sourceWidth - cropX);
        }
        if (cropY + cropHeight > sourceHeight) {
          cropHeight = Math.max(1, sourceHeight - cropY);
        }
      }

      const croppedCanvas = document.createElement("canvas");
      croppedCanvas.width = cropWidth;
      croppedCanvas.height = cropHeight;

      const croppedContext = croppedCanvas.getContext("2d");
      if (!croppedContext) {
        return null;
      }

      croppedContext.drawImage(
        sourceCanvas,
        cropX,
        cropY,
        cropWidth,
        cropHeight,
        0,
        0,
        cropWidth,
        cropHeight,
      );

      const dataBase64 = toBase64FromDataUrl(croppedCanvas.toDataURL("image/jpeg", 0.9));
      if (!dataBase64) {
        return null;
      }

      return {
        mime_type: "image/jpeg",
        data_base64: dataBase64,
        description: `Lesson video screenshot for \"${lesson?.title || lessonTitle}\"`,
        source: "lesson_screen_capture",
      };
    } catch (error) {
      console.error("Unable to capture lesson screenshot:", error);
      return null;
    }
  }, [ensureScreenCaptureSession, lesson?.title, lessonTitle]);

  useEffect(() => {
    return () => {
      stopScreenCaptureSession();
    };
  }, [stopScreenCaptureSession]);

  const toggleFullscreen = async () => {
    if (!playerWrapperRef.current) return;

    if (!document.fullscreenElement) {
      await playerWrapperRef.current.requestFullscreen?.();
      return;
    }

    await document.exitFullscreen?.();
  };

  useEffect(() => {
    // Reset chatbot store correctly when lesson changes
    useChatbotStore.getState().reset();
  }, [lessonId]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        let lessonData: Lesson | undefined;

        if (courseId) {
          try {
            const courseData = await courseApi.getById(courseId);
            setCourse(courseData);

            try {
              const assignments = await assignmentApi.listByCourse(courseData.id, true);
              const lessonAssignmentsForVideo = assignments
                .filter((item) => item.lesson_id === lessonId)
                .sort((a, b) => a.order_index - b.order_index);
              setLessonAssignments(lessonAssignmentsForVideo);
            } catch {
              setLessonAssignments([]);
            }
          } catch {
            // Optional for breadcrumb only.
            setLessonAssignments([]);
          }

          try {
            const lessons = await courseApi.getLessons(courseId);
            lessonData = (lessons as Lesson[]).find((item) => item.id === lessonId);
          } catch {
            // Fall back to query context.
          }
        }
        else {
          setLessonAssignments([]);
        }

        if (lessonData) {
          setLesson({
            id: lessonData.id,
            title: lessonData.title,
            description: lessonData.description,
            video_url: lessonData.video_url,
            course_id: lessonData.course_id,
          });
        } else {
          setLesson({
            id: lessonId,
            title: lessonTitle,
            description: undefined,
            video_url: lessonVideoUrl || undefined,
            course_id: courseId || undefined,
          });
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || "Không thể tải phòng học");
      } finally {
        setIsLoading(false);
      }
    };

    if (lessonId) {
      fetchData();
    }
  }, [lessonId, courseId, lessonTitle, lessonVideoUrl]);

  useEffect(() => {
    const onFullscreenChange = () => {
      const fullscreenElement = document.fullscreenElement as HTMLElement | null;
      const wrapper = playerWrapperRef.current;

      if (!fullscreenElement) {
        setIsFullscreen(false);
        setIsChatbotPopupOpen(false);
        return;
      }

      const isWrapperFullscreen = !!wrapper && fullscreenElement === wrapper;
      setIsFullscreen(isWrapperFullscreen);

      if (!isWrapperFullscreen) {
        setIsChatbotPopupOpen(false);
      }
    };

    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <Card className="p-10 text-center">
        <CardTitle className="mb-3">Không thể mở phòng học video</CardTitle>
        <CardDescription className="mb-4">{error || "Bài học không tồn tại"}</CardDescription>
        <Button onClick={() => router.back()}>Quay lại</Button>
      </Card>
    );
  }

  const videoSourceKind = lesson.video_url ? detectLessonVideoSource(lesson.video_url) : null;
  const canUseScreenCapture =
    typeof window !== "undefined" &&
    typeof navigator !== "undefined" &&
    !!navigator.mediaDevices?.getDisplayMedia;
  const canCaptureTeachingImage = !!lesson.video_url && (videoSourceKind === "direct-file" || canUseScreenCapture);
  const meetingPlatformLabel = getMeetingPlatformLabel(videoSourceKind);
  const isMeetingVideoSource = !!videoSourceKind && isMeetingSource(videoSourceKind);
  const teachingImageCapture = canCaptureTeachingImage ? captureTeachingImage : undefined;
  const videoFrameClass = isFullscreen ? "h-full w-full" : "w-full aspect-video";
  const playerShellClass = isFullscreen
    ? "relative flex h-screen w-screen overflow-hidden bg-black"
    : "relative w-full overflow-hidden rounded-xl bg-black";
  const playerPaneClass = isFullscreen
    ? "relative flex h-full min-w-0 flex-1 items-center justify-center bg-black"
    : "relative w-full bg-black";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        {course && <Link href={`/courses/${course.slug}`}>{course.title}</Link>}
        {!course && courseSlug && <Link href={`/courses/${courseSlug}`}>Khóa học</Link>}
        {(course || courseSlug) && <span>&gt;</span>}
        <span>{lesson.title}</span>
        <span>&gt;</span>
        <span className="text-foreground font-medium">Phòng học video</span>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_380px] 2xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="min-w-0 space-y-4">
          <div ref={playerWrapperRef} className={playerShellClass}>
            <div className={playerPaneClass}>
              {lesson.video_url ? (
                videoSourceKind === "youtube" || videoSourceKind === "vimeo" ? (
                  <iframe
                    src={getVideoEmbedUrl(lesson.video_url)}
                    title={lesson.title}
                    className={videoFrameClass}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                ) : videoSourceKind === "direct-file" ? (
                  <video
                    ref={lessonVideoRef}
                    src={lesson.video_url}
                    controls
                    className={`${videoFrameClass} ${isFullscreen ? "object-contain" : ""}`}
                  />
                ) : isMeetingVideoSource ? (
                  <div className={`${videoFrameClass} flex flex-col items-center justify-center gap-4 px-6 text-center text-white/90`}>
                    <p className="text-sm md:text-base font-medium">
                      Bài học đang liên kết với {meetingPlatformLabel}.
                    </p>
                    <p className="text-xs md:text-sm text-white/70 max-w-xl">
                      Nguồn {meetingPlatformLabel} không nhúng trực tiếp trong LMS. Hãy mở phòng học bằng nút bên dưới; khi gửi câu hỏi, chatbot có thể yêu cầu quyền screenshot màn hình.
                    </p>
                    <Button asChild>
                      <a href={lesson.video_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Mở {meetingPlatformLabel}
                      </a>
                    </Button>
                  </div>
                ) : (
                  <iframe
                    src={lesson.video_url}
                    title={lesson.title}
                    className={videoFrameClass}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                )
              ) : (
                <div className={`${videoFrameClass} flex items-center justify-center text-white/70`}>
                  Chưa có video cho bài học này.
                </div>
              )}
            </div>

            {isFullscreen && (
              <>
                {!isChatbotPopupOpen && (
                  <Button
                    type="button"
                    size="icon"
                    className="absolute right-4 top-4 z-30 h-11 w-11 rounded-full shadow-lg"
                    onClick={() => setIsChatbotPopupOpen(true)}
                    title="Mở chatbot học tập"
                  >
                    <MessageSquare className="h-5 w-5" />
                  </Button>
                )}

                {isChatbotPopupOpen && (
                  <aside className="h-full w-[360px] shrink-0 border-l border-white/10 bg-background shadow-2xl lg:w-[400px]">
                    <ChatWindow
                      courseId={lesson.course_id}
                      lessonId={lesson.id}
                      lessonTitle={lesson.title}
                      captureTeachingImage={teachingImageCapture}
                      onClose={() => setIsChatbotPopupOpen(false)}
                      isPopup={true}
                      fitContainer={true}
                      className="rounded-none border-0 shadow-none"
                    />
                  </aside>
                )}
              </>
            )}
          </div>

          <div className="flex items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold">{lesson.title}</h1>
              <p className="text-sm text-muted-foreground">Phòng học online theo kiểu xem video bài giảng.</p>
              <p className="text-xs text-muted-foreground mt-1">Sử dụng nút Phóng to của LMS để bật chatbot trong toàn màn hình.</p>
              {isMeetingVideoSource && (
                <p className="text-xs text-amber-600 mt-1">
                  Nguồn {meetingPlatformLabel} cần mở tab/app ngoài; khi gửi câu hỏi chatbot có thể yêu cầu quyền screenshot màn hình.
                </p>
              )}
            </div>
            <Button variant="outline" onClick={toggleFullscreen}>
              {isFullscreen ? (
                <>
                  <Minimize className="h-4 w-4 mr-2" />
                  Thu nhỏ
                </>
              ) : (
                <>
                  <Maximize className="h-4 w-4 mr-2" />
                  Phóng to
                </>
              )}
            </Button>
          </div>

          {lesson.description && (
            <Card>
              <CardHeader>
                <CardTitle>Mô tả bài giảng</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground whitespace-pre-wrap">{lesson.description}</p>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Điều hướng nhanh</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Link
                  href={course ? `/courses/${course.slug}` : courseSlug ? `/courses/${courseSlug}` : "/courses"}
                  className="w-full border rounded-md px-3 py-2 hover:bg-gray-50 flex items-center gap-2 text-sm"
                >
                  <Video className="h-4 w-4" />
                  Quay về nội dung khóa học
                </Link>
                {lessonAssignments.length > 0 &&
                  lessonAssignments.map((assignment, assignmentIndex) => (
                    <Link
                      key={assignment.id}
                      href={`/lessons/${lessonId}/assignment?${new URLSearchParams({
                        courseId: course?.id || courseId || "",
                        courseSlug: course?.slug || courseSlug || "",
                        lessonTitle: lesson.title,
                        assignmentId: assignment.id,
                      }).toString()}`}
                      className="w-full border rounded-md px-3 py-2 hover:bg-gray-50 flex items-center gap-2 text-sm"
                    >
                      <ClipboardList className="h-4 w-4" />
                      {assignment.title || `Đi tới bài tập ${assignmentIndex + 1}`}
                    </Link>
                  ))}
                {isMeetingVideoSource && lesson.video_url && (
                  <a
                    href={lesson.video_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full border rounded-md px-3 py-2 hover:bg-gray-50 flex items-center gap-2 text-sm"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Mở {meetingPlatformLabel}
                  </a>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Trạng thái video</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Chế độ thường: xem ngay trong trang nếu nguồn hỗ trợ nhúng/video trực tiếp.
                </p>
                <p className="flex items-center gap-2">
                  <Maximize className="h-4 w-4" />
                  Chế độ phóng to: toàn màn hình.
                </p>
                <p className="text-xs">
                  {canCaptureTeachingImage
                    ? "Chatbot tự động quyết định khi nào cần ảnh bài giảng dựa trên nội dung câu hỏi, rồi chụp frame video hoặc screenshot vùng player."
                    : "Trình duyệt hiện tại chưa hỗ trợ Screen Capture API, nên chatbot sẽ trả lời bằng ngữ cảnh văn bản."}
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        <aside className="min-h-[560px] xl:sticky xl:top-6 xl:h-[calc(100vh-8rem)]">
          <ChatWindow
            courseId={lesson.course_id}
            lessonId={lesson.id}
            lessonTitle={lesson.title}
            captureTeachingImage={teachingImageCapture}
            fitContainer={true}
            className="h-full"
          />
        </aside>
      </div>
    </div>
  );
}
