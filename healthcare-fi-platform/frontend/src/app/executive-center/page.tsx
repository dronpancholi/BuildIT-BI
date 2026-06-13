'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  executiveAPI,
  assistantAPI,
} from '@/lib/api/client';
import {
  TrendingUp,
  AlertTriangle,
  Activity,
  DollarSign,
  Users,
  Send,
  BedDouble,
  FileText
} from 'lucide-react';

export default function ExecutiveCenterPage() {
  const [loading, setLoading] = useState(true);
  
  // Data State
  const [financials, setFinancials] = useState<any>(null);
  const [operations, setOperations] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [forecasts, setForecasts] = useState<any[]>([]);

  // AI Chat State
  const [chatHistory, setChatHistory] = useState<{role: string, content: string}[]>([]);
  const [query, setQuery] = useState('');
  const [asking, setAsking] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [kpiRes, alertRes] = await Promise.all([
          executiveAPI.getKPIs(),
          executiveAPI.getAlerts()
        ]);
        
        // Mocking structure until backend is fully hooked up
        setFinancials(kpiRes.data.financials || {
          revenue: 12500000,
          expenses: 8400000,
          profit: 4100000,
          cash: 2100000
        });
        
        setOperations(kpiRes.data.operations || {
          occupancy: 82.5,
          patients: 12450,
          claims_denial_rate: 4.2
        });

        setAlerts(alertRes.data.alerts || [
          { id: 1, title: 'Unusual Supply Cost Spike in Cardiology', severity: 'critical' },
          { id: 2, title: 'Occupancy approaching 90% capacity', severity: 'warning' },
          { id: 3, title: 'Cash flow dip projected for next week', severity: 'warning' }
        ]);
        
        setForecasts([
          { period: 'Next 30 Days', metric: 'Revenue', value: 13100000, trend: 'up' },
          { period: 'Next 30 Days', metric: 'Expenses', value: 8600000, trend: 'up' }
        ]);

      } catch (err) {
        console.error('Failed to load executive data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleAskAI = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage = { role: 'user', content: query };
    setChatHistory(prev => [...prev, userMessage]);
    setQuery('');
    setAsking(true);

    try {
      const res = await assistantAPI.askQuestion(userMessage.content);
      setChatHistory(prev => [...prev, { role: 'ai', content: res.data.answer }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'ai', content: 'Sorry, I encountered an error analyzing the data.' }]);
    } finally {
      setAsking(false);
    }
  };

  const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val || 0);

  if (loading) {
    return <DashboardLayout><div className="p-8 text-center text-muted-foreground">Loading Executive Workspace...</div></DashboardLayout>;
  }

  return (
    <DashboardLayout>
      <div className="flex-1 flex flex-col h-screen overflow-hidden p-6 space-y-6 bg-slate-50 dark:bg-slate-900">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold tracking-tight">Executive Workspace</h1>
        </div>

        <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
          
          {/* Main Content Area (Metrics) */}
          <div className="col-span-8 space-y-6 overflow-y-auto pr-2">
            
            {/* Financial Health */}
            <section>
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2"><DollarSign className="h-5 w-5 text-green-600"/> Financial Health</h2>
              <div className="grid grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Revenue</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold">{formatCurrency(financials?.revenue)}</div></CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Expenses</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold">{formatCurrency(financials?.expenses)}</div></CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Net Profit</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold text-green-600">{formatCurrency(financials?.profit)}</div></CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Cash Position</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold">{formatCurrency(financials?.cash)}</div></CardContent>
                </Card>
              </div>
            </section>

            {/* Operations */}
            <section>
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2"><Activity className="h-5 w-5 text-blue-600"/> Operations</h2>
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground flex items-center gap-2"><BedDouble className="h-4 w-4"/> Occupancy</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold">{(operations?.occupancy || 0).toFixed(1)}%</div></CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground flex items-center gap-2"><Users className="h-4 w-4"/> Patient Volume</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold">{(operations?.patients || 0).toLocaleString()}</div></CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground flex items-center gap-2"><FileText className="h-4 w-4"/> Denial Rate</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold">{(operations?.claims_denial_rate || 0).toFixed(1)}%</div></CardContent>
                </Card>
              </div>
            </section>

            {/* Forecasts & Alerts Row */}
            <div className="grid grid-cols-2 gap-6">
              <Card>
                <CardHeader><CardTitle className="text-lg flex items-center gap-2"><TrendingUp className="h-5 w-5"/> Forecasts (Next 30 Days)</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  {forecasts.map((f, i) => (
                    <div key={i} className="flex justify-between items-center p-3 bg-muted rounded-lg">
                      <span className="font-medium">{f.metric}</span>
                      <span className="font-bold">{formatCurrency(f.value)}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle className="text-lg flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-amber-500"/> Top Alerts</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {alerts.map((a, i) => (
                    <div key={i} className="flex items-start gap-3 p-2 border-b last:border-0">
                      <AlertTriangle className={`h-4 w-4 mt-0.5 ${a.severity === 'critical' ? 'text-red-500' : 'text-amber-500'}`} />
                      <span className="text-sm">{a.title}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
            
          </div>

          {/* Right Side: Executive Assistant */}
          <Card className="col-span-4 flex flex-col h-full border-primary/20 shadow-lg">
            <CardHeader className="bg-primary/5 border-b pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                Executive Assistant
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0 flex flex-col overflow-hidden">
              <ScrollArea className="flex-1 p-4">
                {chatHistory.length === 0 ? (
                  <div className="text-center text-muted-foreground text-sm mt-10">
                    <p>I am connected to the Financial Data Warehouse.</p>
                    <p className="mt-2">Ask me anything about revenue, expenses, or operations.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {chatHistory.map((msg, i) => (
                      <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] rounded-lg p-3 text-sm ${
                          msg.role === 'user' 
                            ? 'bg-primary text-primary-foreground' 
                            : 'bg-muted'
                        }`}>
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    {asking && (
                      <div className="flex justify-start">
                        <div className="max-w-[85%] rounded-lg p-3 text-sm bg-muted animate-pulse">
                          Analyzing warehouse data...
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </ScrollArea>
              
              <div className="p-4 border-t bg-background">
                <form onSubmit={handleAskAI} className="flex gap-2">
                  <Input 
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="E.g., Why did revenue decline?"
                    disabled={asking}
                    className="flex-1"
                  />
                  <Button type="submit" size="icon" disabled={asking || !query.trim()}>
                    <Send className="h-4 w-4" />
                  </Button>
                </form>
              </div>
            </CardContent>
          </Card>

        </div>
      </div>
    </DashboardLayout>
  );
}
