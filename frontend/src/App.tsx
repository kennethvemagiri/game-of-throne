import { AppDataProvider } from './context/AppDataContext';
import { Dashboard } from './components/layout/Dashboard';

export default function App() {
  return (
    <AppDataProvider>
      <Dashboard />
    </AppDataProvider>
  );
}
