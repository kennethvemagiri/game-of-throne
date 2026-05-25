import { createContext, useContext, type ReactNode } from 'react';
import { useApplications } from '../hooks/useApplications';
import { useSuggestedJobs } from '../hooks/useSuggestedJobs';

type AppData = ReturnType<typeof useApplications> & {
  suggested: ReturnType<typeof useSuggestedJobs>;
};

const AppDataContext = createContext<AppData | null>(null);

export function AppDataProvider({ children }: { children: ReactNode }) {
  const applications = useApplications();
  const suggested = useSuggestedJobs();

  return (
    <AppDataContext.Provider value={{ ...applications, suggested }}>
      {children}
    </AppDataContext.Provider>
  );
}

export function useAppData() {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error('useAppData must be used within AppDataProvider');
  return ctx;
}
