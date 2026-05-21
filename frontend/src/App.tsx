import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { useAuth } from "./auth";
import { CaseDetailPage } from "./pages/CaseDetail";
import { DriverDashboardPage } from "./pages/DriverDashboard";
import { LoginPage } from "./pages/Login";
import { ManagerDashboardPage } from "./pages/ManagerDashboard";
import { ReviewerDashboardPage } from "./pages/ReviewerDashboard";
import { UploadCasePage } from "./pages/UploadCase";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="loading-screen">Loading…</div>;
  }
  if (!user) return <LoginPage />;

  const role = user.role;

  return (
    <AppShell>
      <Routes>
        {role === "driver" && (
          <>
            <Route path="/" element={<DriverDashboardPage driverId={user.driver_id ?? ""} />} />
            <Route path="/cases/:caseId" element={<CaseDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </>
        )}

        {role === "reviewer" && (
          <>
            <Route path="/" element={<ReviewerDashboardPage />} />
            <Route path="/upload" element={<UploadCasePage />} />
            <Route path="/cases/:caseId" element={<CaseDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </>
        )}

        {role === "manager" && (
          <>
            <Route path="/" element={<ManagerDashboardPage />} />
            <Route path="/queue" element={<ReviewerDashboardPage />} />
            <Route path="/upload" element={<UploadCasePage />} />
            <Route path="/cases/:caseId" element={<CaseDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </>
        )}
      </Routes>
    </AppShell>
  );
}
