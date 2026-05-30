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
  sent_cv: "CV Sent",
  recruiter_call: "Recruiter Call",
  receive_response: "Response Received",
  interview_scheduled: "Interview Scheduled",
  interview_finished: "Interview Completed",
  offer: "Offer",
  rejected: "Rejected",
};
