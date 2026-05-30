export const SENIORITY_LEVELS = [
  "Middle Developer",
  "Senior Developer",
  "Principal Developer",
  "Middle Data Engineer",
  "Senior Data Engineer",
  "Principal Data Engineer",
  "Software Architect",
  "Data Architect",
  "Middle Manager",
  "Senior Manager",
] as const;

export type SeniorityLevel = (typeof SENIORITY_LEVELS)[number];
