import { useCallback, useEffect, useState } from 'react';

import { fetchGmailStatus, triggerGmailSync } from '../../api/client';
import { useAppData } from '../../context/AppDataContext';
import { STATUS_LABELS, METRIC_KEYS } from '../../lib/statuses';
import { BottomNav } from './BottomNav';
import { CalendarWidget } from '../dashboard/CalendarWidget';
import { InsightsCharts } from '../dashboard/InsightsCharts';
import { MetricCards } from '../dashboard/MetricCards';
import { PipelineTable } from '../dashboard/PipelineTable';
import { ReviewWidget } from '../dashboard/ReviewWidget';
import { SuggestedJobsWidget } from '../dashboard/SuggestedJobsWidget';
import { MetricCardsSkeleton, PipelineTableSkeleton, Skeleton } from '../ui/Skeleton';

type Section = 'overview' | 'applications' | 'suggested' | 'insights';

const SECTIONS: { key: Section; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'applications', label: 'Applications' },
  { key: 'suggested', label: 'Suggested Jobs' },
  { key: 'insights', label: 'Insights' },
];

function useGmailSync(onSyncComplete: () => void) {
  const [authenticated, setAuthenticated] = useState(false);
  const [lastFetch, setLastFetch] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const checkStatus = useCallback(async () => {
    try {
      const status = await fetchGmailStatus();
      setAuthenticated(status.authenticated);
      setLastFetch(status.lastFetch);
    } catch {
      /* status endpoint may not exist yet */
    }
  }, []);

  useEffect(() => {
    void checkStatus();
  }, [checkStatus]);

  const sync = async () => {
    setSyncing(true);
    try {
      await triggerGmailSync();
      await checkStatus();
      onSyncComplete();
    } finally {
      setSyncing(false);
    }
  };

  return { authenticated, lastFetch, syncing, sync };
}

function formatTimeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function Dashboard() {
  const { applications, stats, assignStatus, archiveApp, suggested, refresh, loading, error } =
    useAppData();
  const gmail = useGmailSync(refresh);
  const [activeSection, setActiveSection] = useState<Section>('overview');
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [appStatusFilter, setAppStatusFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().slice(0, 10));

  const pipelineFilter =
    activeFilter && activeFilter !== 'needs_review' ? activeFilter : statusFilter;

  const pending = stats.needsReview;

  return (
    <div className="dashboard">
      {/* ── Header ── */}
      <header className="dash-header">
        <div className="dash-header__brand">
          <img src="/logo.png" alt="" className="dash-header__logo" aria-hidden="true" />
          <div>
            <h1 className="dash-header__title">Game of Throne</h1>
            <p className="dash-header__sub">
              Automated job pipeline, synced from{' '}
              <a
                href="https://kennethvemagiri.com"
                target="_blank"
                rel="noopener noreferrer"
                className="dash-header__link"
              >
                @kennethvemagiri
              </a>{' '}
              email inbox
            </p>
          </div>
        </div>

        <div className="dash-header__sync">
          {gmail.authenticated ? (
            <>
              <button
                type="button"
                className="btn btn--sync"
                onClick={gmail.sync}
                disabled={gmail.syncing}
              >
                {gmail.syncing ? (
                  <>
                    <span className="sync-spinner" aria-hidden="true" />
                    Syncing…
                  </>
                ) : (
                  'Sync'
                )}
              </button>
              {gmail.lastFetch && (
                <span className="sync-status">{formatTimeAgo(gmail.lastFetch)}</span>
              )}
            </>
          ) : (
            <a href="/auth/google/login" className="btn btn--sync">
              Connect Gmail
            </a>
          )}
        </div>

        <span className={`header__badge${pending === 0 ? ' is-empty' : ''}`}>
          {pending === 1 ? '1 pending review' : `${pending} pending reviews`}
        </span>
      </header>

      {/* ── Tab bar (desktop only via CSS) ── */}
      <nav className="tab-bar" aria-label="Main navigation">
        {SECTIONS.map((s) => (
          <button
            key={s.key}
            type="button"
            className={`tab-bar__tab${activeSection === s.key ? ' is-active' : ''}`}
            onClick={() => setActiveSection(s.key)}
            aria-selected={activeSection === s.key}
            role="tab"
          >
            {s.label}
          </button>
        ))}
      </nav>

      {/* ── Error banner ── */}
      {error && (
        <div className="dash-content" style={{ paddingBottom: 0 }}>
          <div className="error-banner">
            <span>Failed to load data. Please try again.</span>
            <button type="button" onClick={refresh}>
              Retry
            </button>
          </div>
        </div>
      )}

      {/* ── Content: all sections always rendered ── */}
      <main className="dash-content">
        <div className="dash-grid">
        {/* ─── OVERVIEW ─── */}
        <section
          id="overview"
          className={`dash-section${activeSection === 'overview' ? ' is-active' : ''}`}
        >
          <div className="section">
            {loading ? (
              <MetricCardsSkeleton />
            ) : (
              <MetricCards
                counts={stats.counts}
                activeFilter={activeFilter}
                onFilter={(key) => {
                  setActiveFilter(key);
                  if (key && key !== 'needs_review') setStatusFilter(key);
                  else setStatusFilter('');
                }}
              />
            )}
          </div>

          <div className="overview-grid">
            <section className="section overview-grid__main">
              {loading ? (
                <div className="widget panel review-widget">
                  <Skeleton variant="text" width="8rem" height="1.25rem" />
                  <div className="skeleton-group" style={{ marginTop: '1rem' }}>
                    <Skeleton variant="row" count={3} />
                  </div>
                </div>
              ) : (
                <ReviewWidget applications={applications} onAssign={assignStatus} />
              )}
            </section>

            <aside className="section overview-grid__aside">
              <div className="section-header">
                <h2 className="section-title">Pipeline</h2>
                <div className="filter-group">
                  <div className="filter-control filter-control--date">
                    <label>
                      <span className="filter-label">From</span>
                      <input
                        type="date"
                        value={dateFrom}
                        onChange={(e) => setDateFrom(e.target.value)}
                        aria-label="Filter from date"
                      />
                    </label>
                    <label>
                      <span className="filter-label">To</span>
                      <input
                        type="date"
                        value={dateTo}
                        onChange={(e) => setDateTo(e.target.value)}
                        aria-label="Filter to date"
                      />
                    </label>
                  </div>
                  <label className="filter-control">
                    <select
                      value={statusFilter}
                      onChange={(e) => {
                        setStatusFilter(e.target.value);
                        setActiveFilter(e.target.value || null);
                      }}
                      aria-label="Filter by status"
                    >
                      <option value="">All statuses</option>
                      {Object.entries(STATUS_LABELS)
                        .filter(([k]) => k !== 'needs_review')
                        .map(([key, label]) => (
                          <option key={key} value={key}>
                            {label}
                          </option>
                        ))}
                    </select>
                  </label>
                </div>
              </div>
              {loading ? (
                <PipelineTableSkeleton />
              ) : (
                <div className="panel pipeline-aside-panel">
                  <PipelineTable
                    applications={applications}
                    statusFilter={pipelineFilter}
                    dateFrom={dateFrom}
                    dateTo={dateTo}
                    onArchive={archiveApp}
                    variant="cards"
                  />
                </div>
              )}
            </aside>
          </div>
        </section>

        {/* ─── APPLICATIONS ─── */}
        <section
          id="applications"
          className={`dash-section${activeSection === 'applications' ? ' is-active' : ''}`}
        >
          <div className="section-header">
            <h2 className="section-title">Applications</h2>
            <label className="filter-control">
              <select
                value={appStatusFilter}
                onChange={(e) => setAppStatusFilter(e.target.value)}
                aria-label="Filter by status"
              >
                <option value="">All statuses</option>
                {Object.entries(STATUS_LABELS)
                  .filter(([k]) => k !== 'needs_review')
                  .map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
              </select>
            </label>
          </div>
          {loading ? (
            <PipelineTableSkeleton />
          ) : (
            <div className="panel">
              <PipelineTable
                applications={applications}
                statusFilter={appStatusFilter}
                onArchive={archiveApp}
              />
            </div>
          )}
        </section>

        {/* ─── SUGGESTED JOBS ─── */}
        <section
          id="suggested"
          className={`dash-section${activeSection === 'suggested' ? ' is-active' : ''}`}
        >
          <h2 className="section-title">Suggested jobs</h2>
          <p className="page-lead">
            Jobs surfaced by automation (e.g. Indeed). Reject what does not fit, or open the listing
            to apply.
          </p>
          <SuggestedJobsWidget
            jobs={suggested.jobs}
            onReject={suggested.reject}
            onOpen={suggested.openJob}
          />
        </section>

        {/* ─── INSIGHTS ─── */}
        <section
          id="insights"
          className={`dash-section${activeSection === 'insights' ? ' is-active' : ''}`}
        >
          <h2 className="section-title">Insights</h2>
          <div className="insights-grid">
            <InsightsCharts applications={applications} />
            <div className="insights-grid__aside">
              <div className="stats-grid panel">
                <div className="stats-summary">
                  <div>
                    <span className="stats-summary__label">Total applications</span>
                    <strong className="stats-summary__value">{stats.total}</strong>
                  </div>
                  <div>
                    <span className="stats-summary__label">Needs review</span>
                    <strong className="stats-summary__value">{stats.needsReview}</strong>
                  </div>
                </div>
                <ul className="stats-bars">
                  {METRIC_KEYS.map((key) => {
                    const count = stats.counts[key] ?? 0;
                    const max = Math.max(
                      ...METRIC_KEYS.map((k) => stats.counts[k] ?? 0),
                      1,
                    );
                    const pct = Math.round((count / max) * 100);
                    return (
                      <li key={key} className={`stats-bar stats-bar--${key}`}>
                        <div className="stats-bar__label">
                          <span>{STATUS_LABELS[key]}</span>
                          <span>{count}</span>
                        </div>
                        <div className="stats-bar__track">
                          <div className="stats-bar__fill" style={{ width: `${pct}%` }} />
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
              <CalendarWidget applications={applications} compact />
            </div>
          </div>
        </section>
        </div>
      </main>

      {/* ── Bottom nav (mobile only via CSS) ── */}
      <BottomNav activeSection={activeSection} onNavigate={(s) => setActiveSection(s as Section)} />
    </div>
  );
}
