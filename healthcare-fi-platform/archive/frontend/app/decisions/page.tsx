"use client";

import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DecisionCenter } from "@/components/decision/decision-center";
import { OutcomeCenter } from "@/components/outcome/outcome-center";
import { FeatureCatalog } from "@/components/outcome/feature-catalog";
import { ModelRegistry } from "@/components/outcome/model-registry";
import { DashboardLayout } from "@/components/layout/dashboard-layout";

export default function DecisionsPage() {
  const [activeTab, setActiveTab] = useState("decisions");

  return (
    <DashboardLayout>
      <div className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Decision Intelligence</h1>
        <p className="text-muted-foreground">
          Propose, review, and track decisions with outcome measurement and model governance
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="decisions">Decisions</TabsTrigger>
          <TabsTrigger value="outcomes">Outcomes</TabsTrigger>
          <TabsTrigger value="features">Feature Catalog</TabsTrigger>
          <TabsTrigger value="models">Model Registry</TabsTrigger>
        </TabsList>

        <TabsContent value="decisions"><DecisionCenter /></TabsContent>
        <TabsContent value="outcomes"><OutcomeCenter /></TabsContent>
        <TabsContent value="features"><FeatureCatalog /></TabsContent>
        <TabsContent value="models"><ModelRegistry /></TabsContent>
      </Tabs>
      </div>
    </DashboardLayout>
  );
}
