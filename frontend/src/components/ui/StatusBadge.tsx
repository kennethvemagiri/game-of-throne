import type { CSSProperties } from 'react';
import { STATUS_COLORS, STATUS_LABELS } from '../../lib/statuses';

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const label = STATUS_LABELS[status] || status;
  const color = STATUS_COLORS[status] || '#64748b';

  return (
    <span
      className="status-badge"
      style={{ '--badge-color': color } as CSSProperties}
    >
      {label.toUpperCase()}
    </span>
  );
}
