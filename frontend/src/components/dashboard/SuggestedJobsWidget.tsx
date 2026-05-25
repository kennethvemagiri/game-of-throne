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
        <p className="empty-state empty-state--compact">No new suggestions right now.</p>
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
