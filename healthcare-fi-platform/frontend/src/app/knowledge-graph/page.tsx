"use client";

import { KnowledgeGraphExplorer } from "@/components/knowledge-graph/knowledge-graph-explorer";
import { DashboardLayout } from "@/components/layout/dashboard-layout";

export default function GraphPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <KnowledgeGraphExplorer />
      </div>
    </DashboardLayout>
  );
}
