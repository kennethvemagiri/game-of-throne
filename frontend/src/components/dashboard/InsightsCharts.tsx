import { useMemo } from 'react';
import type { Application } from '../../api/client';

interface InsightsChartsProps {
  applications: Application[];
}

interface DayBucket {
  date: Date;
  label: string;
  count: number;
}

interface StatusDayBucket {
  date: Date;
  label: string;
  interview: number;
  assessment: number;
  recruiter: number;
  acknowledged: number;
  rejected: number;
}

function getDayRange(apps: Application[]): Date[] {
  if (!apps.length) return [];
  const dates = apps
    .filter((a) => a.receivedAt)
    .map((a) => new Date(a.receivedAt!));
  if (!dates.length) return [];

  const min = new Date(Math.min(...dates.map((d) => d.getTime())));
  const max = new Date(Math.max(...dates.map((d) => d.getTime())));
  min.setHours(0, 0, 0, 0);
  max.setHours(0, 0, 0, 0);

  const padBefore = new Date(min);
  padBefore.setDate(padBefore.getDate() - 2);
  const padAfter = new Date(max);
  padAfter.setDate(padAfter.getDate() + 2);

  const result: Date[] = [];
  const cur = new Date(padBefore);
  while (cur <= padAfter) {
    result.push(new Date(cur));
    cur.setDate(cur.getDate() + 1);
  }
  return result;
}

function formatLabel(d: Date): string {
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function toKey(d: Date): string {
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
}

function buildActivityData(apps: Application[]): DayBucket[] {
  const days = getDayRange(apps);
  const countMap = new Map<string, number>();
  for (const app of apps) {
    if (!app.receivedAt) continue;
    const d = new Date(app.receivedAt);
    d.setHours(0, 0, 0, 0);
    const key = toKey(d);
    countMap.set(key, (countMap.get(key) ?? 0) + 1);
  }
  return days.map((d) => ({
    date: d,
    label: formatLabel(d),
    count: countMap.get(toKey(d)) ?? 0,
  }));
}

function buildStatusData(apps: Application[]): StatusDayBucket[] {
  const days = getDayRange(apps);
  const map = new Map<string, StatusDayBucket>();
  for (const d of days) {
    map.set(toKey(d), {
      date: d,
      label: formatLabel(d),
      interview: 0,
      assessment: 0,
      recruiter: 0,
      acknowledged: 0,
      rejected: 0,
    });
  }
  for (const app of apps) {
    if (!app.receivedAt) continue;
    const d = new Date(app.receivedAt);
    d.setHours(0, 0, 0, 0);
    const bucket = map.get(toKey(d));
    if (!bucket) continue;
    if (app.status === 'interview') bucket.interview++;
    else if (app.status === 'assessment') bucket.assessment++;
    else if (app.status === 'recruiter_inbound') bucket.recruiter++;
    else if (app.status === 'acknowledged') bucket.acknowledged++;
    else if (app.status === 'rejected') bucket.rejected++;
  }
  return days.map((d) => map.get(toKey(d))!);
}

function buildCumulativeData(apps: Application[]): DayBucket[] {
  const days = getDayRange(apps);
  const countMap = new Map<string, number>();
  for (const app of apps) {
    if (!app.receivedAt) continue;
    const d = new Date(app.receivedAt);
    d.setHours(0, 0, 0, 0);
    const key = toKey(d);
    countMap.set(key, (countMap.get(key) ?? 0) + 1);
  }
  let running = 0;
  return days.map((d) => {
    running += countMap.get(toKey(d)) ?? 0;
    return { date: d, label: formatLabel(d), count: running };
  });
}

const CHART_W = 780;
const CHART_H = 110;
const PAD_L = 32;
const PAD_R = 12;
const PAD_T = 10;
const PAD_B = 22;
const PLOT_W = CHART_W - PAD_L - PAD_R;
const PLOT_H = CHART_H - PAD_T - PAD_B;

function buildSmoothPath(
  values: number[],
  maxVal: number,
): { line: string; area: string } {
  if (!values.length) return { line: '', area: '' };
  const n = values.length;
  const scaleX = (i: number) => PAD_L + (i / Math.max(n - 1, 1)) * PLOT_W;
  const scaleY = (v: number) =>
    PAD_T + PLOT_H - (v / Math.max(maxVal, 1)) * PLOT_H;

  const points = values.map((v, i) => ({ x: scaleX(i), y: scaleY(v) }));

  let path = `M${points[0].x},${points[0].y}`;
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const cur = points[i];
    const cpx = (prev.x + cur.x) / 2;
    path += ` C${cpx},${prev.y} ${cpx},${cur.y} ${cur.x},${cur.y}`;
  }

  const baseline = PAD_T + PLOT_H;
  const area =
    path +
    ` L${points[points.length - 1].x},${baseline} L${points[0].x},${baseline} Z`;

  return { line: path, area };
}

function yAxisTicks(max: number): number[] {
  if (max <= 0) return [0];
  const step = max <= 4 ? 1 : Math.ceil(max / 4);
  const ticks: number[] = [];
  for (let v = 0; v <= max; v += step) ticks.push(v);
  if (ticks[ticks.length - 1] < max) ticks.push(max);
  return ticks;
}

interface AreaChartProps {
  title: string;
  legend: string;
  color: string;
  gradientId: string;
  values: number[];
  labels: string[];
}

function AreaChart({ title, legend, color, gradientId, values, labels }: AreaChartProps) {
  const maxVal = Math.max(...values, 1);
  const { line, area } = buildSmoothPath(values, maxVal);
  const ticks = yAxisTicks(maxVal);
  const n = labels.length;

  const labelStep = Math.max(1, Math.ceil(n / 7));
  const xLabels = labels
    .map((l, i) => ({ label: l, x: PAD_L + (i / Math.max(n - 1, 1)) * PLOT_W }))
    .filter((_, i) => i % labelStep === 0 || i === n - 1);

  return (
    <div className="insight-chart panel fade-in">
      <svg
        viewBox={`0 0 ${CHART_W} ${CHART_H}`}
        preserveAspectRatio="xMidYMid meet"
        className="insight-chart__svg"
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={0.03} />
          </linearGradient>
        </defs>

        {ticks.map((v) => {
          const y = PAD_T + PLOT_H - (v / Math.max(maxVal, 1)) * PLOT_H;
          return (
            <g key={v}>
              <line
                x1={PAD_L}
                x2={PAD_L + PLOT_W}
                y1={y}
                y2={y}
                stroke="#e5e7eb"
                strokeWidth={0.8}
              />
              <text
                x={PAD_L - 5}
                y={y + 3}
                textAnchor="end"
                fontSize={9}
                fill="#9ca3af"
              >
                {v}
              </text>
            </g>
          );
        })}

        <path d={area} fill={`url(#${gradientId})`} />
        <path
          d={line}
          fill="none"
          stroke={color}
          strokeWidth={2.2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {xLabels.map(({ label, x }) => (
          <text
            key={label + x}
            x={x}
            y={CHART_H - 4}
            textAnchor="middle"
            fontSize={9}
            fill="#9ca3af"
          >
            {label}
          </text>
        ))}
      </svg>

      <div className="insight-chart__footer">
        <span className="insight-chart__title">{title}</span>
        <span className="insight-chart__legend">
          <span className="insight-chart__dot" style={{ background: color }} />
          {legend}
        </span>
      </div>
    </div>
  );
}

export function InsightsCharts({ applications }: InsightsChartsProps) {
  const activity = useMemo(() => buildActivityData(applications), [applications]);
  const statusData = useMemo(() => buildStatusData(applications), [applications]);
  const cumulative = useMemo(() => buildCumulativeData(applications), [applications]);

  if (!applications.length) {
    return (
      <div className="empty-state">
        <svg className="empty-state__icon" width="40" height="40" viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6,30 14,18 22,24 34,10" />
          <polyline points="28,10 34,10 34,16" />
        </svg>
        <p>No data to display yet.</p>
      </div>
    );
  }

  return (
    <div className="insight-charts-stack">
      <AreaChart
        title="Pipeline Activity"
        legend="Applications received"
        color="#f59e0b"
        gradientId="grad-activity"
        values={activity.map((d) => d.count)}
        labels={activity.map((d) => d.label)}
      />

      <AreaChart
        title="Status Breakdown"
        legend="Positive responses"
        color="#6366f1"
        gradientId="grad-status"
        values={statusData.map(
          (d) => d.interview + d.assessment + d.recruiter + d.acknowledged,
        )}
        labels={statusData.map((d) => d.label)}
      />

      <AreaChart
        title="Cumulative Applications"
        legend="Total over time"
        color="#ec4899"
        gradientId="grad-cumulative"
        values={cumulative.map((d) => d.count)}
        labels={cumulative.map((d) => d.label)}
      />
    </div>
  );
}
