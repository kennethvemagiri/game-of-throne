import { METRIC_KEYS, STATUS_LABELS } from '../../lib/statuses';

const CARD_ICONS: Record<string, string> = {
  interview: '/interview-icon.png',
  assessment: '/assessment-icon.png',
  recruiter_inbound: '/recruiter-icon.png',
  needs_review: '/review-icon.png',
  acknowledged: '/acknowledged-icon.png',
  rejected: '/rejected-icon.png',
};

interface MetricCardsProps {
  counts: Record<string, number>;
  activeFilter: string | null;
  onFilter: (status: string | null) => void;
}

export function MetricCards({ counts, activeFilter, onFilter }: MetricCardsProps) {
  return (
    <div className="metric-cards">
      {METRIC_KEYS.map((key, i) => {
        const isActive = activeFilter === key;
        const icon = CARD_ICONS[key];
        return (
          <button
            key={key}
            type="button"
            className={`metric-card metric-card--${key}${isActive ? ' is-active' : ''}${icon ? ' has-icon' : ''} fade-in-stagger`}
            style={{ animationDelay: `${i * 0.06}s` }}
            onClick={() => onFilter(isActive ? null : key)}
            aria-pressed={isActive}
          >
            <span className="metric-card__label">{STATUS_LABELS[key]}</span>
            <span className="metric-card__value">{counts[key] ?? 0}</span>
            {icon && (
              <img src={icon} alt="" className="metric-card__icon" aria-hidden="true" />
            )}
          </button>
        );
      })}
    </div>
  );
}
