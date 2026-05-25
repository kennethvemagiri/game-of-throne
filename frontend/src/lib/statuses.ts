export const STATUS_LABELS: Record<string, string> = {
  interview: 'Interview',
  assessment: 'Assessment',
  recruiter_inbound: 'Recruiter',
  needs_review: 'Needs Review',
  rejected: 'Rejected',
  acknowledged: 'Acknowledged',
  applied: 'Applied',
};

export const METRIC_KEYS = [
  'interview',
  'assessment',
  'recruiter_inbound',
  'needs_review',
  'acknowledged',
  'rejected',
] as const;

export const REVIEW_ACTIONS = [
  'interview',
  'assessment',
  'recruiter_inbound',
  'acknowledged',
  'rejected',
] as const;

export type ApplicationStatus = keyof typeof STATUS_LABELS;

export const STATUS_COLORS: Record<string, string> = {
  interview: '#2a5a3f',
  assessment: '#b45309',
  recruiter_inbound: '#1e6b52',
  needs_review: '#92600a',
  acknowledged: '#1a6b7a',
  rejected: '#9c3a3a',
  applied: '#5b5499',
};
