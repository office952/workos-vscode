import { Route, Routes } from "react-router-dom";
import { EmployeeMobileV2Layout } from "@/components/workos/employee-mobile-v2/EmployeeMobileV2Shell";
import EmployeeMobileV2Home from "@/components/workos/employee-mobile-v2/EmployeeMobileV2Home";
import EmployeeMobileV2TasksPage from "@/components/workos/employee-mobile-v2/EmployeeMobileV2TasksPage";
import EmployeeMobileV2TaskDetailPage from "@/components/workos/employee-mobile-v2/EmployeeMobileV2TaskDetailPage";
import EmployeeMobileV2PipelinePage from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PipelinePage";
import EmployeeMobileV2DocumentsPage from "@/components/workos/employee-mobile-v2/EmployeeMobileV2DocumentsPage";
import EmployeeMobileV2BlockersPage from "@/components/workos/employee-mobile-v2/EmployeeMobileV2BlockersPage";
import EmployeeMobileV2UpcomingPage from "@/components/workos/employee-mobile-v2/EmployeeMobileV2UpcomingPage";
import EmployeeMobileV2PersonalPage from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PersonalPage";

export default function EmployeeMobileV2App() {
  return (
    <Routes>
      <Route element={<EmployeeMobileV2Layout />}>
        <Route index element={<EmployeeMobileV2Home />} />
        <Route path="tasks" element={<EmployeeMobileV2TasksPage />} />
        <Route path="tasks/:taskId" element={<EmployeeMobileV2TaskDetailPage />} />
        <Route path="pipeline" element={<EmployeeMobileV2PipelinePage />} />
        <Route path="documents" element={<EmployeeMobileV2DocumentsPage />} />
        <Route path="blockers" element={<EmployeeMobileV2BlockersPage />} />
        <Route path="upcoming" element={<EmployeeMobileV2UpcomingPage />} />
        <Route path="personal/*" element={<EmployeeMobileV2PersonalPage />} />
      </Route>
    </Routes>
  );
}
