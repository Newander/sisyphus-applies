export const APPLICATION_STAGES = [
  "sent_cv",
  "recruiter_call",
  "receive_response",
  "interview_scheduled",
  "interview_finished",
  "offer",
  "rejected",
] as const;

export type ApplicationStage = (typeof APPLICATION_STAGES)[number];

export const applicationStageLabels: Record<ApplicationStage, string> = {
  sent_cv: "CV отправлено",
  recruiter_call: "Созвон с рекрутёром",
  receive_response: "Получен ответ",
  interview_scheduled: "Интервью назначено",
  interview_finished: "Интервью завершено",
  offer: "Оффер",
  rejected: "Отказ",
};
