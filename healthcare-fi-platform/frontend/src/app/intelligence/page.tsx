"use client";

import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { IntelligenceFeed } from "@/components/intelligence/intelligence-feed";
import { AnomalyCenter } from "@/components/intelligence/anomaly-center";
import { OpportunityCenter } from "@/components/intelligence/opportunity-center";
import { RecommendationCenter } from "@/components/intelligence/recommendation-center";
import { BriefingLibrary } from "@/components/intelligence/briefing-library";
import { IntelligenceGraphExplorer } from "@/components/intelligence/graph-explorer";
import { Activity, AlertTriangle, DollarSign, CheckCircle2, BookOpen, GitBranch } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";

export default function IntelligencePage() {
  const [activeTab, setActiveTab] = useState("feed");

  return (
    <DashboardLayout>
      <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Intelligence Center</h1>
          <p className="text-muted-foreground">
            AI-powered insights, anomalies, opportunities, and recommendations
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => v && setActiveTab(v)}>
        <TabsList>
          <TabsTrigger value="feed">
            <Activity className="size-4 mr-1.5" />
            Feed
          </TabsTrigger>
          <TabsTrigger value="anomalies">
            <AlertTriangle className="size-4 mr-1.5" />
            Anomalies
          </TabsTrigger>
          <TabsTrigger value="opportunities">
            <DollarSign className="size-4 mr-1.5" />
            Opportunities
          </TabsTrigger>
          <TabsTrigger value="recommendations">
            <CheckCircle2 className="size-4 mr-1.5" />
            Recommendations
          </TabsTrigger>
          <TabsTrigger value="briefings">
            <BookOpen className="size-4 mr-1.5" />
            Briefings
          </TabsTrigger>
          <TabsTrigger value="graph">
            <GitBranch className="size-4 mr-1.5" />
            Graph
          </TabsTrigger>
        </TabsList>

        <TabsContent value="feed">
          <IntelligenceFeed />
        </TabsContent>
        <TabsContent value="anomalies">
          <AnomalyCenter />
        </TabsContent>
        <TabsContent value="opportunities">
          <OpportunityCenter />
        </TabsContent>
        <TabsContent value="recommendations">
          <RecommendationCenter />
        </TabsContent>
        <TabsContent value="briefings">
          <BriefingLibrary />
        </TabsContent>
        <TabsContent value="graph">
          <IntelligenceGraphExplorer />
        </TabsContent>
      </Tabs>
      </div>
    </DashboardLayout>
  );
}
