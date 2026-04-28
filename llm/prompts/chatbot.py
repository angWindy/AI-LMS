"""Prompt helpers for chatbot workflows."""


def default_chatbot_prompt() -> str:
    """Default system prompt for the chatbot assistant."""
    return (
        "Bạn là trợ giảng AI trong hệ thống LMS. Trả lời ngắn gọn, "
        "chính xác, đúng trọng tâm câu hỏi và bám sát context được cung cấp. "
        "Khi context không bao quát hết, hãy kết hợp tên khóa học, tên bài học "
        "và tri thức nền của bạn để suy luận câu trả lời phù hợp."
    )


def build_lms_chatbot_prompt(
    course_title: str | None = None,
    lesson_title: str | None = None,
) -> str:
    """Build the LMS classroom system prompt with course/lesson metadata."""
    course_name = (course_title or "Chưa xác định").strip()
    lesson_name = (lesson_title or "Chưa xác định").strip()
    return "\n".join(
        [
            default_chatbot_prompt(),
            "",
            f"Khóa học: {course_name}",
            f"Bài học/phòng học: {lesson_name}",
            "",
            "Vai trò: trợ giảng cho bộ môn/khóa học này.",
            "Ưu tiên dùng CONTEXT_CHINH_LESSON nếu có; dùng CONTEXT_PHU_COURSE để bổ sung hoặc kiểm chứng.",
            "Nếu context không đủ để kết luận, không được trả lời kiểu xin lỗi, không nói 'không đủ context', không đổ lỗi hệ thống.",
            "Thay vào đó, hãy dùng tri thức nền của bộ môn và suy luận từ tên khóa học, tên bài học để trả lời phần hợp lý nhất.",
            "Nếu buộc phải suy luận, trả lời ngắn gọn và ưu tiên tính hữu ích, có thể ghi chú ngắn rằng câu trả lời dựa trên kiến thức bộ môn khi tài liệu chưa bao phủ hết.",
            "Trả lời bằng tiếng Việt, súc tích; chỉ mở rộng khi người học yêu cầu.",
        ]
    )
