import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import IncidentsPage from './pages/IncidentsPage';
import CreateIncidentPage from './pages/CreateIncidentPage';
import IncidentDetailsPage from './pages/IncidentDetailsPage';
import AIAnalysisPage from './pages/AIAnalysisPage';
import AlertsPage from './pages/AlertsPage';
import ReportsPage from './pages/ReportsPage';
import UserManagementPage from './pages/UserManagementPage';
import AuditLogsPage from './pages/AuditLogsPage';
import SettingsPage from './pages/SettingsPage';
import HomePage from './pages/HomePage';

function ProtectedRoute({ children }) {
  const { token, isInitializing } = useAuth();
  if (isInitializing) return null;
  return token ? children : <Navigate to="/login" replace />;
}

function AppRoutes() {
  const { token, isInitializing } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={token ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/register" element={token ? <Navigate to="/" replace /> : <RegisterPage />} />

      <Route
        path="/"
        element={
          isInitializing ? null : token ? (
            <Layout>
              <DashboardPage />
            </Layout>
          ) : <HomePage />
        }
      />
      <Route
        path="/incidents"
        element={
          <ProtectedRoute>
            <Layout>
              <IncidentsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/incidents/:incidentId"
        element={
          <ProtectedRoute>
            <Layout>
              <IncidentDetailsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/create-incident"
        element={
          <ProtectedRoute>
            <Layout>
              <CreateIncidentPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-analysis"
        element={
          <ProtectedRoute>
            <Layout>
              <AIAnalysisPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/alerts"
        element={
          <ProtectedRoute>
            <Layout>
              <AlertsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <Layout>
              <ReportsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/users"
        element={
          <ProtectedRoute>
            <Layout>
              <UserManagementPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/audit"
        element={
          <ProtectedRoute>
            <Layout>
              <AuditLogsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Layout>
              <SettingsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
