import type { SuggestedJob } from '../../api/client';

interface SuggestedJobsWidgetProps {
  jobs: SuggestedJob[];
  onReject: (id: string) => void;
  onOpen: (job: SuggestedJob) => void;
  preview?: boolean;
  onViewAll?: () => void;
}

export function SuggestedJobsWidget({
  jobs,
  onReject,
  onOpen,
  preview = false,
  onViewAll,
}: SuggestedJobsWidgetProps) {
  const list = preview ? jobs.slice(0, 3) : jobs;

  return (
    <div className="widget panel">
      <div className="widget__head">
        <h3>Suggested jobs</h3>
        {preview && jobs.length > 0 && onViewAll && (
          <button type="button" className="widget__link btn--link" onClick={onViewAll}>
            View all
          </button>
        )}
      </div>
      {!list.length ? (
        <div className="empty-state empty-state--compact">
          <svg className="empty-state__icon" width="36" height="36" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ margin: '0 0 0.5rem' }}>
            <rect x="5" y="10" width="26" height="18" rx="3" />
            <path d="M12 10V7a6 6 0 0 1 12 0v3" />
          </svg>
          <p style={{ margin: 0 }}>No new suggestions right now.</p>
        </div>
      ) : (
        <ul className="suggested-list">
          {list.map((job) => (
            <li key={job.id} className="suggested-item">
              <div className="suggested-item__head">
                <strong>{job.company}</strong>
                <span className="chip chip--source">{job.source}</span>
              </div>
              <p className="suggested-item__role">{job.role}</p>
              <p className="suggested-item__snippet">{job.snippet}</p>
              <div className="suggested-item__actions">
                <button type="button" className="btn btn--ghost" onClick={() => onReject(job.id)}>
                  Reject
                </button>
                <button type="button" className="btn btn--primary" onClick={() => onOpen(job)}>
                  View job
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
