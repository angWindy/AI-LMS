"use client";

import { useRef, useEffect, useId, useState } from "react";
import Image from "next/image";
import { SendHorizontal, Loader2, Sparkles, X, ImagePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { chatbotApi, TeachingImagePayload } from "@/lib/api/chatbot";
import { useChatbotStore, ChatMessage } from "./store";

const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
const ALLOWED_IMAGE_MIME_TYPES: TeachingImagePayload["mime_type"][] = [
  "image/png",
  "image/jpeg",
  "image/webp",
  "image/gif",
];

interface PendingImageAttachment {
  name: string;
  previewUrl: string;
  payload: TeachingImagePayload;
}

function isAllowedImageMimeType(mimeType: string): mimeType is TeachingImagePayload["mime_type"] {
  return ALLOWED_IMAGE_MIME_TYPES.includes(mimeType as TeachingImagePayload["mime_type"]);
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = () => {
      if (typeof reader.result !== "string") {
        reject(new Error("Invalid file reader output"));
        return;
      }

      const commaIndex = reader.result.indexOf(",");
      if (commaIndex < 0) {
        reject(new Error("Invalid data URL"));
        return;
      }

      resolve(reader.result.slice(commaIndex + 1));
    };

    reader.onerror = () => reject(reader.error || new Error("Cannot read image file"));
    reader.readAsDataURL(file);
  });
}

interface ChatWindowProps {
  courseId?: string;
  lessonId?: string;
  lessonTitle?: string;
  onClose?: () => void;
  className?: string;
  isPopup?: boolean;
  captureTeachingImage?: () => Promise<TeachingImagePayload | null> | TeachingImagePayload | null;
}

export function ChatWindow({
  courseId,
  lessonId,
  lessonTitle,
  onClose,
  className = "",
  isPopup = false,
  captureTeachingImage,
}: ChatWindowProps) {
  const { messages, setMessages, input, setInput, isLoading, setIsLoading, conversationId, setConversationId } = useChatbotStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const teachingImageSwitchId = useId();

  const [useTeachingImage, setUseTeachingImage] = useState(false);
  const [attachedImage, setAttachedImage] = useState<PendingImageAttachment | null>(null);
  const [imageStatus, setImageStatus] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (attachedImage) {
        URL.revokeObjectURL(attachedImage.previewUrl);
      }
    };
  }, [attachedImage]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleAttachImage = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) {
      return;
    }

    if (!isAllowedImageMimeType(file.type)) {
      setImageStatus("Định dạng ảnh chưa được hỗ trợ. Vui lòng dùng PNG, JPEG, WEBP hoặc GIF.");
      return;
    }

    if (file.size > MAX_IMAGE_BYTES) {
      setImageStatus("Ảnh quá lớn. Mỗi ảnh tối đa 10MB.");
      return;
    }

    try {
      const dataBase64 = await fileToBase64(file);
      const previewUrl = URL.createObjectURL(file);

      setAttachedImage({
        name: file.name,
        previewUrl,
        payload: {
          mime_type: file.type,
          data_base64: dataBase64,
          description: `Ảnh đính kèm từ người học: ${file.name}`,
          source: "chat_input_upload",
        },
      });
      setImageStatus("Đã thêm ảnh vào câu hỏi.");
    } catch (error) {
      console.error("Cannot process selected image:", error);
      setImageStatus("Không thể đọc ảnh đã chọn. Vui lòng thử lại.");
    }
  };

  const handleRemoveAttachedImage = () => {
    setAttachedImage(null);
    setImageStatus(null);
  };

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
      const teachingImages: TeachingImagePayload[] = [];

      if (useTeachingImage) {
        if (!captureTeachingImage) {
          setImageStatus("Nguồn bài giảng hiện tại không hỗ trợ chụp ảnh tự động.");
        } else {
          try {
            const capturedImage = await captureTeachingImage();
            if (capturedImage) {
              teachingImages.push(capturedImage);
            } else {
              setImageStatus("Không lấy được ảnh bài giảng tự động từ nguồn video hiện tại.");
            }
          } catch (captureError) {
            console.error("Cannot capture teaching image:", captureError);
            setImageStatus("Không thể chụp ảnh bài giảng lúc gửi câu hỏi.");
          }
        }
      }

      if (attachedImage) {
        teachingImages.push(attachedImage.payload);
      }

      const response = await chatbotApi.ask({
        question: userText,
        conversation_id: conversationId,
        conversation_title: lessonTitle ? `Q&A: ${lessonTitle}` : undefined,
        course_id: courseId,
        lesson_id: lessonId,
        teaching_images: teachingImages.length > 0 ? teachingImages : undefined,
      });
      
      setConversationId(response.conversation_id);
      setAttachedImage(null);
      
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
        : (detail || "Xin lỗi, đã có lỗi xảy ra. Không thể kết nối với hệ thống AI.");
        
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

  return (
    <div className={`flex flex-col bg-background border rounded-xl overflow-hidden shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3 bg-muted/30">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <div className="flex flex-col">
            <span className="text-sm font-semibold">Trợ lý AI</span>
            <span className="text-[10px] text-muted-foreground">{lessonTitle ? `Phòng học: ${lessonTitle}` : "Sẵn sàng hỗ trợ"}</span>
          </div>
        </div>
        {isPopup && onClose && (
          <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Messages list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef} style={{ minHeight: isPopup ? "300px" : "400px", maxHeight: isPopup ? "400px" : "600px" }}>
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-3 opacity-70">
            <Sparkles className="h-10 w-10 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">Bạn cần trợ giúp gì?</p>
              <p className="text-xs text-muted-foreground mt-1">Hỏi về nội dung bài học, thuật ngữ khó hiểu, hoặc yêu cầu tóm tắt.</p>
            </div>
            
            <div className="flex flex-wrap gap-2 justify-center mt-4 w-full">
              <span onClick={() => handleQuickAction("Tóm tắt nội dung chính của bài học này.")} className="text-xs border rounded-full px-3 py-1 cursor-pointer hover:bg-muted transition-colors">
                Tóm tắt bài học
              </span>
              <span onClick={() => handleQuickAction("Tạo 3 câu hỏi trắc nghiệm dựa trên bài học này.")} className="text-xs border rounded-full px-3 py-1 cursor-pointer hover:bg-muted transition-colors">
                Cho bài tập nhỏ
              </span>
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
                  className={`rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground rounded-tr-sm"
                      : "bg-muted rounded-tl-sm"
                  }`}
                >
                  {msg.content}
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
      <form onSubmit={handleSubmit} className="border-t p-3 bg-background space-y-2">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <Switch
              id={teachingImageSwitchId}
              checked={useTeachingImage}
              onCheckedChange={setUseTeachingImage}
            />
            <Label htmlFor={teachingImageSwitchId} className="text-xs text-muted-foreground">
              Dùng ảnh bài giảng khi gửi
            </Label>
          </div>

          <div>
            <input
              ref={imageInputRef}
              type="file"
              accept={ALLOWED_IMAGE_MIME_TYPES.join(",")}
              onChange={handleAttachImage}
              className="hidden"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-8 px-2.5 text-xs"
              onClick={() => imageInputRef.current?.click()}
            >
              <ImagePlus className="h-3.5 w-3.5 mr-1.5" />
              Thêm ảnh
            </Button>
          </div>
        </div>

        {useTeachingImage && !captureTeachingImage && (
          <p className="text-[11px] text-amber-600">
            Bài giảng hiện tại không hỗ trợ chụp ảnh tự động. Bạn vẫn có thể đính kèm ảnh thủ công.
          </p>
        )}

        {attachedImage && (
          <div className="flex items-center gap-3 rounded-lg border bg-muted/40 p-2">
            <Image
              src={attachedImage.previewUrl}
              alt={attachedImage.name}
              width={80}
              height={56}
              unoptimized
              className="h-14 w-20 rounded-md border object-cover bg-white"
            />
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium truncate">{attachedImage.name}</p>
              <p className="text-[11px] text-muted-foreground">Ảnh sẽ được gửi kèm câu hỏi.</p>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-7 w-7 rounded-full"
              onClick={handleRemoveAttachedImage}
              title="Xóa ảnh đính kèm"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

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
