'use client';

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  FileText,
  FileSpreadsheet,
  Download,
  Plus,
  Loader2,
  CheckCircle2,
} from 'lucide-react';
import { exportsAPI } from '@/lib/api/client';

export default function ExportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const [newExport, setNewExport] = useState({
    name: 'Q3 Board Pack',
    format: 'pdf',
  });

  const fetchExports = async () => {
    try {
      const res = await exportsAPI.getJobs();
      setReports(res.data.reports || []);
    } catch (err) {
      console.error('Failed to load exports', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExports();
  }, []);

  const handleCreate = async () => {
    if (!newExport.name) return;
    setCreating(true);
    try {
      await exportsAPI.createJob(newExport);
      await fetchExports();
      setNewExport({ name: '', format: 'pdf' });
    } catch (err) {
      console.error('Failed to create export', err);
    } finally {
      setCreating(false);
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format?.toLowerCase()) {
      case 'pdf': return <FileText className="h-4 w-4 text-red-500" />;
      case 'excel': return <FileSpreadsheet className="h-4 w-4 text-green-600" />;
      default: return <FileText className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Board Pack Exports</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {/* Create Export Card */}
          <Card className="col-span-1">
            <CardHeader>
              <CardTitle>Generate New Export</CardTitle>
              <CardDescription>Select the format and run a new report.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Report Name</Label>
                <Input 
                  value={newExport.name}
                  onChange={(e) => setNewExport({ ...newExport, name: e.target.value })}
                  placeholder="e.g. Monthly Financials" 
                />
              </div>
              <div className="space-y-2">
                <Label>Format</Label>
                <Select 
                  value={newExport.format} 
                  onValueChange={(val) => setNewExport({ ...newExport, format: val || '' })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pdf">PDF Document</SelectItem>
                    <SelectItem value="excel">Excel Workbook</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button 
                onClick={handleCreate} 
                disabled={creating || !newExport.name} 
                className="w-full mt-4"
              >
                {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                Generate Report
              </Button>
            </CardContent>
          </Card>

          {/* Export History */}
          <Card className="col-span-2">
            <CardHeader>
              <CardTitle>Recent Exports</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center p-4 text-muted-foreground">Loading history...</div>
              ) : reports.length === 0 ? (
                <div className="text-center p-8 border border-dashed rounded-lg text-muted-foreground">
                  No export history found. Generate your first report.
                </div>
              ) : (
                <div className="space-y-3">
                  {reports.map((report) => (
                    <div key={report.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                      <div className="flex items-center gap-4">
                        {getFormatIcon(report.format)}
                        <div>
                          <p className="font-medium text-sm">{report.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(report.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="flex items-center text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> Ready
                        </span>
                        <Button variant="ghost" size="icon">
                          <Download className="h-4 w-4 text-muted-foreground" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
