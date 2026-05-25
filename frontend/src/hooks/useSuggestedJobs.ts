import { useCallback, useEffect, useState } from 'react';
import {
  fetchSuggestedJobs,
  markSuggestedJobViewed,
  rejectSuggestedJob,
  type SuggestedJob,
} from '../api/client';

export function useSuggestedJobs() {
  const [jobs, setJobs] = useState<SuggestedJob[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchSuggestedJobs('pending');
      setJobs(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const reject = async (id: string) => {
    await rejectSuggestedJob(id);
    await refresh();
  };

  const openJob = async (job: SuggestedJob) => {
    window.open(job.url, '_blank', 'noopener,noreferrer');
    await markSuggestedJobViewed(job.id);
    await refresh();
  };

  return { jobs, loading, refresh, reject, openJob };
}
