import { CourseLevel } from "@/types";

export const COURSE_LEVEL_VALUES = [
  CourseLevel.ELEMENTARY,
  CourseLevel.MIDDLE_SCHOOL,
  CourseLevel.HIGH_SCHOOL,
  CourseLevel.HIGHER_EDUCATION,
] as const;

export const COURSE_LEVEL_OPTIONS = [
  { value: CourseLevel.ELEMENTARY, label: "Tiểu học" },
  { value: CourseLevel.MIDDLE_SCHOOL, label: "Trung học cơ sở" },
  { value: CourseLevel.HIGH_SCHOOL, label: "Trung học phổ thông" },
  { value: CourseLevel.HIGHER_EDUCATION, label: "Đại học và sau đại học" },
] as const;

export function getCourseLevelLabel(level: CourseLevel | string | null | undefined) {
  return (
    COURSE_LEVEL_OPTIONS.find((option) => option.value === level)?.label ||
    "Chưa xác định"
  );
}
