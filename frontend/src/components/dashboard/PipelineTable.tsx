import { useState } from 'react';
import type { Application } from '../../api/client';
import { formatDate } from '../../lib/dates';
import { StatusBadge } from '../ui/StatusBadge';

interface PipelineTableProps {
  applications: Application[];
  statusFilter: string;
  dateFrom?: string;
  dateTo?: string;
  onArchive?: (id: string) => Promise<void>;
  variant?: 'table' | 'cards';
}

function getInitials(company?: string | null) {
  const raw = (company || '').trim();
  if (!raw) return '?';
  const parts = raw.split(/\s+/).filter(Boolean);
  const first = parts[0]?.[0] || '';
  const last = parts.length > 1 ? parts[parts.length - 1]?.[0] || '' : '';
  return (first + last).toUpperCase().slice(0, 2) || '?';
}

export function PipelineTable({
  applications,
  statusFilter,
  dateFrom,
  dateTo,
  onArchive,
  variant = 'table',
}: PipelineTableProps) {
  let list = applications.filter((a) => a.status !== 'needs_review');
  if (statusFilter) {
    list = list.filter((a) => a.status === statusFilter);
  }
  if (dateFrom) {
    const from = new Date(dateFrom);
    list = list.filter((a) => {
      if (!a.receivedAt) return false;
      return new Date(a.receivedAt) >= from;
    });
  }
  if (dateTo) {
    const to = new Date(dateTo);
    to.setHours(23, 59, 59, 999);
    list = list.filter((a) => {
      if (!a.receivedAt) return true;
      return new Date(a.receivedAt) <= to;
    });
  }

  const [dismissing, setDismissing] = useState<string | null>(null);

  const handleDismiss = async (id: string) => {
    if (!onArchive) return;
    setDismissing(id);
    setTimeout(async () => {
      await onArchive(id);
      setDismissing(null);
    }, 300);
  };

  if (!list.length) {
    return (
      <div className="empty-state">
        <svg className="empty-state__icon" width="40" height="40" viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <rect x="6" y="8" width="28" height="24" rx="3" />
          <line x1="6" y1="15" x2="34" y2="15" />
          <line x1="14" y1="8" x2="14" y2="15" />
          <line x1="26" y1="8" x2="26" y2="15" />
        </svg>
        <p>No applications in pipeline.</p>
      </div>
    );
  }

  if (variant === 'cards') {
    return (
      <>
        <div className="pipeline-cards" role="list">
          {list.map((app) => {
            const company = app.company || 'Unknown';
            const updateText = app.snippet || app.subject || '—';

            return (
              <article
                key={app.id}
                role="listitem"
                className={`pipeline-card${dismissing === app.id ? ' is-dismissing' : ''}`}
              >
                <div className="pipeline-card__head">
                  <div className="pipeline-card__brand">
                    <span className="pipeline-card__avatar" aria-hidden="true">
                      {getInitials(company)}
                    </span>
                    <div className="pipeline-card__title">
                      <strong className="pipeline-card__company">{company}</strong>
                      <div className="pipeline-card__meta">{formatDate(app.receivedAt)}</div>
                    </div>
                  </div>

                  {onArchive && (
                    <button
                      type="button"
                      className="btn-dismiss"
                      onClick={() => handleDismiss(app.id)}
                      disabled={dismissing === app.id}
                      aria-label={`Move ${company} to archive`}
                      title="Archive"
                    >
                      🗑️
                    </button>
                  )}
                </div>

                <div className="pipeline-card__rows">
                  <div className="pipeline-card__row">
                    <div className="pipeline-card__label">Role</div>
                    <div className="pipeline-card__value">{app.role || '—'}</div>
                  </div>

                  <div className="pipeline-card__row">
                    <div className="pipeline-card__label">Status</div>
                    <div className="pipeline-card__value">
                      <StatusBadge status={app.status} />
                    </div>
                  </div>

                  <div className="pipeline-card__row pipeline-card__row--update">
                    <div className="pipeline-card__label">Update</div>
                    <div className="pipeline-card__value pipeline-card__update">
                      <span className="snippet-trigger">
                        {updateText}
                        {(app.subject || app.snippet) && (
                          <span className="snippet-popover">
                            {app.subject && <strong>{app.subject}</strong>}
                            {app.subject && app.snippet && <br />}
                            {app.snippet}
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>

        <p className="pipeline-table__footer">
          Showing {list.length} {list.length === 1 ? 'application' : 'applications'}
        </p>
      </>
    );
  }

  return (
    <>
      <div className="pipeline-table-wrap">
        <table className="pipeline-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Role</th>
              <th>Date</th>
              <th>Status</th>
              <th>Latest update</th>
              {onArchive && <th className="pipeline-table__th-dismiss" aria-label="Actions" />}
            </tr>
          </thead>
          <tbody>
            {list.map((app) => (
              <tr
                key={app.id}
                className={dismissing === app.id ? 'is-dismissing' : ''}
              >
                <td data-label="Company">{app.company || 'Unknown'}</td>
                <td data-label="Role">{app.role || '—'}</td>
                <td data-label="Date">{formatDate(app.receivedAt)}</td>
                <td data-label="Status">
                  <StatusBadge status={app.status} />
                </td>
                <td data-label="Update" className="pipeline-table__snippet">
                  <span className="snippet-trigger">
                    {app.snippet || app.subject || '—'}
                    {(app.subject || app.snippet) && (
                      <span className="snippet-popover">
                        {app.subject && <strong>{app.subject}</strong>}
                        {app.subject && app.snippet && <br />}
                        {app.snippet}
                      </span>
                    )}
                  </span>
                </td>
                {onArchive && (
                  <td className="pipeline-table__dismiss-cell">
                    <button
                      type="button"
                      className="btn-dismiss"
                      onClick={() => handleDismiss(app.id)}
                      disabled={dismissing === app.id}
                      aria-label={`Dismiss ${app.company || 'application'}`}
                      title="Dismiss from pipeline"
                    >
                      ✕
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="pipeline-table__footer">
        Showing {list.length} {list.length === 1 ? 'application' : 'applications'}
      </p>
    </>
  );
}
