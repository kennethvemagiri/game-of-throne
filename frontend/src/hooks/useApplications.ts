import { useCallback, useEffect, useState } from 'react';
import {
  archiveApplication,
  fetchApplications,
  fetchStats,
  reviewApplication,
  type Application,
  type Stats,
} from '../api/client';

export function useApplications() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [stats, setStats] = useState<Stats>({ counts: {}, needsReview: 0, total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const [apps, nextStats] = await Promise.all([fetchApplications(), fetchStats()]);
      setApplications(apps);
      setStats(nextStats);
      setError(null);
    } catch {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const assignStatus = async (id: string, status: string) => {
    await reviewApplication(id, status);
    await refresh();
  };

  const archiveApp = async (id: string) => {
    await archiveApplication(id);
    await refresh();
  };

  return { applications, stats, loading, error, refresh, assignStatus, archiveApp };
}
