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
      <div className="widget panel review-widget">
        <h3>Needs review</h3>
        <div className="empty-state">
          <svg className="empty-state__icon" width="40" height="40" viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="20" cy="20" r="15" />
            <polyline points="14,20 18,24 26,16" />
          </svg>
          <p>All caught up. No applications need review.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="widget panel review-widget">
      <h3>Needs review ({queue.length})</h3>
      <div className="review-scroll">
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
    </div>
  );
}
