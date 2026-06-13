"use client";

import { LearningDashboard } from "@/components/learning/learning-dashboard";
import { DashboardLayout } from "@/components/layout/dashboard-layout";

export default function LearningPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <LearningDashboard />
      </div>
    </DashboardLayout>
  );
}
