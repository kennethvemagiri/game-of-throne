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
}

export function PipelineTable({ applications, statusFilter, dateFrom, dateTo, onArchive }: PipelineTableProps) {
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
    return <p className="empty-state">No applications in pipeline.</p>;
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
        Showing 1 to {list.length} of {list.length} applications
      </p>
    </>
  );
}
