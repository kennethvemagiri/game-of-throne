interface SkeletonProps {
  variant?: 'text' | 'card' | 'row';
  width?: string;
  height?: string;
  count?: number;
  className?: string;
}

export function Skeleton({
  variant = 'text',
  width,
  height,
  count = 1,
  className = '',
}: SkeletonProps) {
  const items = Array.from({ length: count }, (_, i) => (
    <div
      key={i}
      className={`skeleton skeleton--${variant} ${className}`}
      style={{ width, height }}
      aria-hidden="true"
    />
  ));

  if (count > 1) {
    return <div className="skeleton-group">{items}</div>;
  }

  return items[0];
}

export function MetricCardsSkeleton() {
  return (
    <div className="metric-cards">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="skeleton skeleton--card" aria-hidden="true" />
      ))}
    </div>
  );
}

export function PipelineTableSkeleton() {
  return (
    <div className="panel" style={{ padding: '1rem' }}>
      <div className="skeleton-group">
        {Array.from({ length: 5 }, (_, i) => (
          <div
            key={i}
            className="skeleton skeleton--row"
            style={{ animationDelay: `${i * 0.08}s` }}
            aria-hidden="true"
          />
        ))}
      </div>
    </div>
  );
}
