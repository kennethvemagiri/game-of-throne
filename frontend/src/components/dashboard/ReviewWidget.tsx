import type { Application } from '../../api/client';
import { formatDate } from '../../lib/dates';
import { REVIEW_ACTIONS, STATUS_LABELS } from '../../lib/statuses';

interface ReviewWidgetProps {
  applications: Application[];
  onAssign: (id: string, status: string) => void;
}

export function ReviewWidget({ applications, onAssign }: ReviewWidgetProps) {
  const queue = applications.filter(
    (a) => a.status === 'needs_review' && a.review?.reviewed !== true,
  );

  if (!queue.length) {
    return (
      <div className="widget panel">
        <h3>Needs review</h3>
        <p className="empty-state empty-state--compact">
          All caught up. You have no applications that need review.
        </p>
      </div>
    );
  }

  return (
    <div className="widget panel">
      <h3>Needs review</h3>
      <ul className="review-list">
        {queue.map((app) => (
          <li key={app.id} className="review-item">
            <div className="review-item__head">
              <strong>{app.company || 'Unknown'}</strong>
              <span>{app.role || 'Role unknown'}</span>
            </div>
            <p className="review-item__meta">{formatDate(app.receivedAt)}</p>
            {app.suggestedStatus ? (
              <span className="chip chip--suggested">
                Suggested: {STATUS_LABELS[app.suggestedStatus] || app.suggestedStatus} ·{' '}
                {app.confidence}
              </span>
            ) : (
              <span className="chip chip--suggested">
                Low confidence · {app.confidence || 'unknown'}
              </span>
            )}
            <p className="review-item__snippet">{app.snippet || app.subject}</p>
            <div className="review-item__actions">
              {REVIEW_ACTIONS.map((status) => (
                <button
                  key={status}
                  type="button"
                  className={`btn${status === app.suggestedStatus ? ' btn--primary' : ''}`}
                  onClick={() => onAssign(app.id, status)}
                >
                  {STATUS_LABELS[status]}
                </button>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
