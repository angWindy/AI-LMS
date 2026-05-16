"use client";

import { ReactNode, useRef, useEffect, useState } from "react";
import { SendHorizontal, Loader2, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { chatbotApi, TeachingImagePayload } from "@/lib/api/chatbot";
import { useChatbotStore, ChatMessage } from "./store";

interface ChatWindowProps {
  mode?: "lesson" | "assignment";
  courseId?: string;
  lessonId?: string;
  lessonTitle?: string;
  assignmentId?: string;
  assignmentTitle?: string;
  onClose?: () => void;
  className?: string;
  isPopup?: boolean;
  fitContainer?: boolean;
  captureTeachingImage?: () => Promise<TeachingImagePayload | null> | TeachingImagePayload | null;
}

function renderInlineMarkdown(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }

    const token = match[0];
    const content = token.startsWith("**")
      ? token.slice(2, -2)
      : token.slice(1, -1);

    nodes.push(
      token.startsWith("**") ? (
        <strong key={`${match.index}-${token}`} className="font-semibold">
          {content}
        </strong>
      ) : (
        <em key={`${match.index}-${token}`} className="italic">
          {content}
        </em>
      )
    );

    lastIndex = match.index + token.length;
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }

  return nodes;
}

function ChatMarkdown({ content }: { content: string }) {
  const lines = content.split(/\r?\n/);
  const blocks: ReactNode[] = [];
  let listItems: ReactNode[][] = [];
  let listType: "ordered" | "unordered" | null = null;

  const flushList = () => {
    if (!listItems.length) return;
    const ListTag = listType === "ordered" ? "ol" : "ul";
    const listClass =
      listType === "ordered"
        ? "my-1 list-decimal space-y-1 pl-5"
        : "my-1 list-disc space-y-1 pl-5";
    blocks.push(
      <ListTag key={`list-${blocks.length}`} className={listClass}>
        {listItems.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ListTag>
    );
    listItems = [];
    listType = null;
  };

  lines.forEach((line, index) => {
    const unorderedMatch = line.match(/^\s*[-*]\s+(.+)$/);
    const orderedMatch = line.match(/^\s*\d+[.)]\s+(.+)$/);
    if (unorderedMatch || orderedMatch) {
      const currentType = orderedMatch ? "ordered" : "unordered";
      if (listType && listType !== currentType) {
        flushList();
      }
      listType = currentType;
      listItems.push(renderInlineMarkdown((orderedMatch || unorderedMatch)?.[1] || ""));
      return;
    }

    flushList();

    if (!line.trim()) {
      blocks.push(<div key={`space-${index}`} className="h-2" />);
      return;
    }

    blocks.push(
      <p key={`line-${index}`} className="my-1 leading-relaxed">
        {renderInlineMarkdown(line)}
      </p>
    );
  });

  flushList();

  return <>{blocks}</>;
}

export function ChatWindow({
  mode = "lesson",
  courseId,
  lessonId,
  lessonTitle,
  assignmentId,
  assignmentTitle,
  onClose,
  className = "",
  isPopup = false,
  fitContainer = false,
  captureTeachingImage,
}: ChatWindowProps) {
  const { messages, setMessages, input, setInput, isLoading, setIsLoading, conversationId, setConversationId } = useChatbotStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [imageStatus, setImageStatus] = useState<string | null>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setInput("");
    setImageStatus(null);
    
    // Add user message instantly
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: userText,
    };
    
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      if (mode === "assignment" && !assignmentId) {
        throw new Error("Không tìm thấy bài tập để mở trợ lý.");
      }

      const teachingImages: TeachingImagePayload[] = [];

      if (mode === "lesson" && captureTeachingImage) {
        try {
          const capturedImage = await captureTeachingImage();
          if (capturedImage) {
            teachingImages.push(capturedImage);
            setImageStatus("Đã gửi ảnh bài giảng để backend tự quyết định có cần dùng hay không.");
          }
        } catch (captureError) {
          console.error("Cannot capture teaching image:", captureError);
          setImageStatus("Không thể chụp ảnh bài giảng lúc gửi câu hỏi.");
        }
      }

      const response = mode === "assignment"
        ? await chatbotApi.askAssignment({
            question: userText,
            assignment_id: assignmentId || "",
            conversation_id: conversationId,
          })
        : await chatbotApi.ask({
            question: userText,
            conversation_id: conversationId,
            conversation_title: lessonTitle ? `Q&A: ${lessonTitle}` : undefined,
            course_id: courseId,
            lesson_id: lessonId,
            teaching_images: teachingImages.length > 0 ? teachingImages : undefined,
          });
      
      setConversationId(response.conversation_id);
      
      const assistantMsg: ChatMessage = {
        id: Date.now().toString() + "_bot",
        role: "assistant",
        content: response.answer,
      };
      
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error: any) {
      console.error("Chatbot API error:", error);
      const detail = error.response?.data?.detail;
      const content = detail === "GOOGLE_AI_API_KEY is not configured."
        ? "Hệ thống chưa được cấu hình API Key cho Google Gemini. Vui lòng kiểm tra lại thiết lập."
        : (detail || error.message || "Xin lỗi, đã có lỗi xảy ra. Không thể kết nối với hệ thống AI.");
        
      const errorMsg: ChatMessage = {
        id: Date.now().toString() + "_error",
        role: "assistant",
        content,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleQuickAction = (text: string) => {
    setInput(text);
    // Can't directly submit here because state updates batching, 
    // better to trigger indirectly or just use setInput
  };

  const title = mode === "assignment" ? "Trợ lý bài tập" : "Trợ lý AI";
  const subtitle = mode === "assignment"
    ? (assignmentTitle ? `Bài tập: ${assignmentTitle}` : "Gợi ý khi làm bài")
    : (lessonTitle ? `Phòng học: ${lessonTitle}` : "Sẵn sàng hỗ trợ");
  const emptyTitle = mode === "assignment" ? "Bạn đang vướng ở đâu?" : "Bạn cần trợ giúp gì?";
  const emptyDescription = mode === "assignment"
    ? "Mô tả phần bạn chưa hiểu để nhận gợi ý từng bước."
    : "Hỏi về nội dung bài học, thuật ngữ khó hiểu, hoặc yêu cầu tóm tắt.";
  const quickActions = mode === "assignment"
    ? [
        "Gợi ý cách bắt đầu câu này.",
        "Nhắc lại kiến thức cần dùng cho bài này.",
      ]
    : [
        "Tóm tắt nội dung chính của bài học này.",
        "Tạo 3 câu hỏi trắc nghiệm dựa trên bài học này.",
      ];

  const sizeClass = fitContainer ? "h-full min-h-0" : isPopup ? "h-[min(640px,calc(100vh-5rem))]" : "min-h-[560px]";

  return (
    <div className={`flex min-h-0 flex-col overflow-hidden rounded-lg border bg-background shadow-sm ${sizeClass} ${className}`}>
      {/* Header */}
      <div className="flex shrink-0 items-center justify-between gap-3 border-b bg-muted/30 px-4 py-3">
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <Sparkles className="h-5 w-5 shrink-0 text-primary" />
          <div className="flex min-w-0 flex-1 flex-col">
            <span className="text-sm font-semibold">{title}</span>
            <span className="truncate text-[10px] text-muted-foreground">{subtitle}</span>
          </div>
        </div>
        {isPopup && onClose && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0 rounded-full"
            onClick={onClose}
            aria-label="Đóng chatbot"
            title="Đóng chatbot"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Messages list */}
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-3 opacity-70">
            <Sparkles className="h-10 w-10 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">{emptyTitle}</p>
              <p className="mt-1 text-xs text-muted-foreground">{emptyDescription}</p>
            </div>
            
            <div className="flex flex-wrap gap-2 justify-center mt-4 w-full">
              {quickActions.map((action) => (
                <span
                  key={action}
                  onClick={() => handleQuickAction(action)}
                  className="cursor-pointer rounded-full border px-3 py-1 text-xs transition-colors hover:bg-muted"
                >
                  {action}
                </span>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              <Avatar className="h-8 w-8 shrink-0">
                {msg.role === "assistant" ? (
                  <>
                    <AvatarImage src="/bot-avatar.png" />
                    <AvatarFallback className="bg-primary/10 text-primary">AI</AvatarFallback>
                  </>
                ) : (
                  <>
                    <AvatarImage src="/user-avatar.png" />
                    <AvatarFallback className="bg-secondary">U</AvatarFallback>
                  </>
                )}
              </Avatar>
              <div
                className={`flex flex-col max-w-[80%] ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`rounded-2xl px-4 py-2 text-sm ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground rounded-tr-sm"
                      : "bg-muted rounded-tl-sm"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <ChatMarkdown content={msg.content} />
                  ) : (
                    <span className="whitespace-pre-wrap">{msg.content}</span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex gap-3">
            <Avatar className="h-8 w-8 shrink-0">
              <AvatarFallback className="bg-primary/10 text-primary">AI</AvatarFallback>
            </Avatar>
            <div className="rounded-2xl px-4 py-3 bg-muted rounded-tl-sm flex items-center justify-center">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground m-1" />
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="shrink-0 border-t bg-background p-3 space-y-2">
        <p className="text-[11px] text-muted-foreground">
          {mode === "assignment"
            ? "Trợ lý chỉ đưa gợi ý học tập, không cung cấp đáp án trực tiếp."
            : "Backend tự quyết định khi nào cần dùng ảnh bài giảng."}
        </p>

        {imageStatus && <p className="text-[11px] text-muted-foreground">{imageStatus}</p>}

        <div className="relative flex items-center">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nhập câu hỏi... (Shift + Enter để xuống dòng)"
            className="min-h-[44px] max-h-[120px] resize-none pr-12 rounded-xl"
            rows={1}
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 bottom-1.5 h-8 w-8 rounded-full"
          >
            <SendHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
