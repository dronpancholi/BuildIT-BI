'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  GitBranch,
  DollarSign,
  Users,
  Building,
  Activity,
  TrendingUp,
  Calculator,
  Save,
  Play,
  CheckCircle,
} from 'lucide-react';
import { scenariosAPI } from '@/lib/api/client';
import { ScenarioResult } from '@/lib/types';
import { formatCurrency, formatPercentage } from '@/lib/utils/format';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

const SCENARIO_TYPES = [
  {
    id: 'pricing_change',
    name: 'Pricing Change',
    description: 'Simulate the impact of changing service prices',
    icon: DollarSign,
  },
  {
    id: 'department_expansion',
    name: 'Department Expansion',
    description: 'Model the financial impact of expanding a department',
    icon: Building,
  },
  {
    id: 'staffing_change',
    name: 'Staffing Change',
    description: 'Analyze the impact of adding or reducing staff',
    icon: Users,
  },
  {
    id: 'capacity_expansion',
    name: 'Capacity Expansion',
    description: 'Simulate adding beds or treatment capacity',
    icon: Activity,
  },
];

export default function ScenariosPage() {
  const [selectedScenario, setSelectedScenario] = useState<string>('pricing_change');
  const [parameters, setParameters] = useState<Record<string, number>>({});
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [scenarioName, setScenarioName] = useState('');
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleRunSimulation = async () => {
    setLoading(true);
    try {
      const response = await scenariosAPI.runSimulation({
        scenario_type: selectedScenario,
        parameters,
        periods: 12,
      });
      setResult(response.data);
    } catch (error) {
      console.error('Simulation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveScenario = async () => {
    if (!scenarioName.trim()) return;
    
    try {
      await scenariosAPI.saveScenario({
        name: scenarioName,
        description: `Scenario: ${SCENARIO_TYPES.find(s => s.id === selectedScenario)?.name}`,
        parameters,
      });
      setScenarioName('');
      setSuccessMsg('Scenario saved successfully!');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (error) {
      console.error('Failed to save scenario:', error);
    }
  };

  const renderParameterForm = () => {
    switch (selectedScenario) {
      case 'pricing_change':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current_revenue">Current Annual Revenue ($)</Label>
              <Input
                id="current_revenue"
                type="number"
                placeholder="10000000"
                onChange={(e) => setParameters({ ...parameters, current_revenue: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="price_change">Price Change (%)</Label>
              <Input
                id="price_change"
                type="number"
                placeholder="10"
                onChange={(e) => setParameters({ ...parameters, price_change_percent: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="volume_impact">Volume Impact (%)</Label>
              <Input
                id="volume_impact"
                type="number"
                placeholder="-5"
                onChange={(e) => setParameters({ ...parameters, volume_impact_percent: Number(e.target.value) })}
              />
            </div>
          </div>
        );

      case 'department_expansion':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="investment">Initial Investment ($)</Label>
              <Input
                id="investment"
                type="number"
                placeholder="2000000"
                onChange={(e) => setParameters({ ...parameters, investment: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="monthly_revenue">Expected Monthly Revenue ($)</Label>
              <Input
                id="monthly_revenue"
                type="number"
                placeholder="500000"
                onChange={(e) => setParameters({ ...parameters, monthly_revenue: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="monthly_expenses">Expected Monthly Expenses ($)</Label>
              <Input
                id="monthly_expenses"
                type="number"
                placeholder="300000"
                onChange={(e) => setParameters({ ...parameters, monthly_expenses: Number(e.target.value) })}
              />
            </div>
          </div>
        );

      case 'staffing_change':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new_hires">Number of New Hires</Label>
              <Input
                id="new_hires"
                type="number"
                placeholder="5"
                onChange={(e) => setParameters({ ...parameters, new_hires: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="average_salary">Average Annual Salary ($)</Label>
              <Input
                id="average_salary"
                type="number"
                placeholder="80000"
                onChange={(e) => setParameters({ ...parameters, average_salary: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="productivity">Expected Productivity Improvement (%)</Label>
              <Input
                id="productivity"
                type="number"
                placeholder="15"
                onChange={(e) => setParameters({ ...parameters, productivity_improvement_percent: Number(e.target.value) })}
              />
            </div>
          </div>
        );

      case 'capacity_expansion':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="additional_beds">Additional Beds</Label>
              <Input
                id="additional_beds"
                type="number"
                placeholder="20"
                onChange={(e) => setParameters({ ...parameters, additional_beds: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bed_cost">Cost per Bed ($)</Label>
              <Input
                id="bed_cost"
                type="number"
                placeholder="150000"
                onChange={(e) => setParameters({ ...parameters, bed_cost: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="daily_revenue">Daily Revenue per Bed ($)</Label>
              <Input
                id="daily_revenue"
                type="number"
                placeholder="1500"
                onChange={(e) => setParameters({ ...parameters, daily_revenue_per_bed: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="daily_cost">Daily Cost per Bed ($)</Label>
              <Input
                id="daily_cost"
                type="number"
                placeholder="800"
                onChange={(e) => setParameters({ ...parameters, daily_cost_per_bed: Number(e.target.value) })}
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <GitBranch className="h-8 w-8 text-primary" />
              Scenario Lab
            </h1>
            <p className="text-muted-foreground">
              Model financial scenarios and simulate business decisions
            </p>
          </div>
        </div>

        <Separator />

        {successMsg && (
          <Alert className="border-healthcare-green/30 bg-healthcare-green/10 text-healthcare-green">
            <CheckCircle className="h-4 w-4 text-healthcare-green" />
            <AlertTitle className="text-healthcare-green font-semibold">Success</AlertTitle>
            <AlertDescription className="text-healthcare-green/90">
              {successMsg}
            </AlertDescription>
          </Alert>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Scenario Selection & Parameters */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Select Scenario Type</CardTitle>
                <CardDescription>Choose a scenario to simulate</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {SCENARIO_TYPES.map((scenario) => (
                  <Button
                    key={scenario.id}
                    variant={selectedScenario === scenario.id ? 'default' : 'outline'}
                    className="w-full justify-start"
                    onClick={() => setSelectedScenario(scenario.id)}
                  >
                    <scenario.icon className="h-4 w-4 mr-2" />
                    {scenario.name}
                  </Button>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Parameters</CardTitle>
                <CardDescription>
                  {SCENARIO_TYPES.find(s => s.id === selectedScenario)?.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {renderParameterForm()}
              </CardContent>
            </Card>

            <div className="flex gap-2">
              <Button 
                className="flex-1" 
                onClick={handleRunSimulation}
                disabled={loading}
              >
                <Play className="h-4 w-4 mr-2" />
                {loading ? 'Running...' : 'Run Simulation'}
              </Button>
            </div>
          </div>

          {/* Results */}
          <div className="lg:col-span-2 space-y-6">
            {result ? (
              <>
                {/* Summary Cards */}
                <div className="grid gap-4 md:grid-cols-2">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Total Impact</p>
                          <p className={`text-3xl font-bold ${result.results.total_impact >= 0 ? 'text-healthcare-green' : 'text-healthcare-red'}`}>
                            {formatCurrency(result.results.total_impact || 0)}
                          </p>
                        </div>
                        <TrendingUp className="h-8 w-8 text-primary" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">ROI</p>
                          <p className="text-3xl font-bold text-primary">
                            {formatPercentage(result.results.roi_percent || 0)}
                          </p>
                        </div>
                        <Calculator className="h-8 w-8 text-primary" />
                      </div>
                    </CardContent>
                  </Card>

                  {result.results.payback_period && (
                    <Card>
                      <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-muted-foreground">Payback Period</p>
                            <p className="text-3xl font-bold text-healthcare-blue">
                              {result.results.payback_period} months
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {result.results.annual_revenue && (
                    <Card>
                      <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-muted-foreground">Annual Revenue</p>
                            <p className="text-3xl font-bold text-healthcare-green">
                              {formatCurrency(result.results.annual_revenue, true)}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>

                {/* Monthly Simulations */}
                <Card>
                  <CardHeader>
                    <CardTitle>Monthly Simulation Results</CardTitle>
                    <CardDescription>12-month projection based on your scenario</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-3 px-2">Period</th>
                            <th className="text-right py-3 px-2">Revenue</th>
                            <th className="text-right py-3 px-2">Expenses</th>
                            <th className="text-right py-3 px-2">Profit</th>
                            <th className="text-right py-3 px-2">Cumulative</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.results.monthly_simulations?.map((sim) => (
                            <tr key={sim.period} className="border-b border-border/50">
                              <td className="py-3 px-2 font-medium">Month {sim.period}</td>
                              <td className="text-right py-3 px-2">
                                {formatCurrency(sim.revenue || 0)}
                              </td>
                              <td className="text-right py-3 px-2">
                                {formatCurrency(sim.expenses || 0)}
                              </td>
                              <td className={`text-right py-3 px-2 ${(sim.profit || 0) >= 0 ? 'text-healthcare-green' : 'text-healthcare-red'}`}>
                                {formatCurrency(sim.profit || 0)}
                              </td>
                              <td className="text-right py-3 px-2">
                                {formatCurrency(sim.cumulative_roi || 0)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>

                {/* Save Scenario */}
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-4">
                      <Input
                        placeholder="Enter scenario name..."
                        value={scenarioName}
                        onChange={(e) => setScenarioName(e.target.value)}
                      />
                      <Button onClick={handleSaveScenario} disabled={!scenarioName.trim()}>
                        <Save className="h-4 w-4 mr-2" />
                        Save Scenario
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="h-[400px] flex items-center justify-center">
                <div className="text-center">
                  <GitBranch className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium">No Simulation Results</h3>
                  <p className="text-muted-foreground mt-1">
                    Configure parameters and run a simulation to see results
                  </p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
