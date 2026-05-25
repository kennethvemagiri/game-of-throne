import { useMemo, useState } from 'react';
import type { Application } from '../../api/client';
import { getMonthDays, isSameDay } from '../../lib/dates';
import { STATUS_COLORS } from '../../lib/statuses';

interface CalendarWidgetProps {
  applications: Application[];
  compact?: boolean;
}

const WEEKDAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

export function CalendarWidget({ applications, compact = false }: CalendarWidgetProps) {
  const today = new Date();
  const [viewDate, setViewDate] = useState(
    () => new Date(today.getFullYear(), today.getMonth(), 1),
  );

  const eventsByDay = useMemo(() => {
    const map = new Map<string, { status: string }[]>();
    for (const app of applications) {
      if (!app.receivedAt) continue;
      const d = new Date(app.receivedAt);
      const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
      const list = map.get(key) ?? [];
      list.push({ status: app.status });
      map.set(key, list);
    }
    return map;
  }, [applications]);

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const days = getMonthDays(year, month);
  const monthLabel = viewDate.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });

  const shiftMonth = (delta: number) => {
    setViewDate(new Date(year, month + delta, 1));
  };

  return (
    <div className={`widget panel calendar-widget${compact ? ' calendar-widget--compact' : ''}`}>
      <div className="calendar-widget__head">
        <h3>{compact ? 'Calendar' : monthLabel}</h3>
        {!compact && (
          <div className="calendar-widget__nav">
            <button type="button" onClick={() => shiftMonth(-1)} aria-label="Previous month">
              ‹
            </button>
            <button type="button" onClick={() => shiftMonth(1)} aria-label="Next month">
              ›
            </button>
          </div>
        )}
      </div>
      {compact && <p className="calendar-widget__month">{monthLabel}</p>}
      <div className="calendar-grid">
        {WEEKDAYS.map((d) => (
          <span key={d} className="calendar-grid__weekday">
            {d}
          </span>
        ))}
        {days.map((day) => {
          const inMonth = day.getMonth() === month;
          const key = `${day.getFullYear()}-${day.getMonth()}-${day.getDate()}`;
          const events = eventsByDay.get(key) ?? [];
          const isToday = isSameDay(day, today);

          return (
            <div
              key={day.toISOString()}
              className={`calendar-grid__day${inMonth ? '' : ' is-muted'}${isToday ? ' is-today' : ''}`}
            >
              <span>{day.getDate()}</span>
              {events.length > 0 && (
                <span className="calendar-grid__dots">
                  {events.slice(0, 3).map((e, i) => (
                    <span
                      key={`${key}-${i}`}
                      className="calendar-grid__dot"
                      style={{ background: STATUS_COLORS[e.status] || '#94a3b8' }}
                    />
                  ))}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
