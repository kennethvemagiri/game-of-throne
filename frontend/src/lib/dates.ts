export function formatDate(iso?: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateLong(iso?: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function getMonthDays(year: number, month: number): Date[] {
  const first = new Date(year, month, 1);
  const startPad = first.getDay();
  const days: Date[] = [];

  for (let i = 0; i < startPad; i += 1) {
    days.push(new Date(year, month, i - startPad + 1));
  }

  const last = new Date(year, month + 1, 0).getDate();
  for (let d = 1; d <= last; d += 1) {
    days.push(new Date(year, month, d));
  }

  return days;
}

export function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}
