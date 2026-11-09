const IST_TIME_ZONE = 'Asia/Kolkata';

function parseUtcTimestamp(value) {
  if (!value) return null;
  const timestamp = String(value);
  const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(timestamp);
  const date = new Date(hasTimezone ? timestamp : `${timestamp}Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDateTimeIST(value) {
  const date = parseUtcTimestamp(value);
  if (!date) return '—';

  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: IST_TIME_ZONE,
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).formatToParts(date);
  const part = (type) => parts.find((item) => item.type === type)?.value || '';
  return `${part('day')} ${part('month')} ${part('year')}, ${part('hour')}:${part('minute')} ${part('dayPeriod').toUpperCase()} IST`;
}

export function formatDateIST(value) {
  const date = parseUtcTimestamp(value);
  if (!date) return '—';
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: IST_TIME_ZONE,
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date);
}
