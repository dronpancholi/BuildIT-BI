'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Bell,
  Filter,
  RefreshCw,
  Eye,
  EyeOff,
} from 'lucide-react';
import { alertsAPI } from '@/lib/api/client';
import { Alert, AlertStats } from '@/lib/types';
import { formatDateTime, getSeverityColor } from '@/lib/utils/format';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [filter, setFilter] = useState<'all' | 'unread' | 'critical'>('all');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [alertsRes, statsRes] = await Promise.all([
        alertsAPI.listAlerts({ limit: 50 }),
        alertsAPI.getStats(),
      ]);
      setAlerts(alertsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id: number) => {
    try {
      await alertsAPI.markAsRead(id);
      setAlerts(alerts.map(alert => 
        alert.id === id ? { ...alert, is_read: true } : alert
      ));
      if (stats) {
        setStats({ ...stats, unread: stats.unread - 1 });
      }
    } catch (error) {
      console.error('Failed to mark alert as read:', error);
    }
  };

  const handleResolve = async (id: number) => {
    try {
      await alertsAPI.resolveAlert(id);
      setAlerts(alerts.map(alert => 
        alert.id === id ? { ...alert, is_resolved: true, is_read: true } : alert
      ));
      if (stats) {
        setStats({ ...stats, critical: stats.critical - 1 });
      }
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'unread') return !alert.is_read;
    if (filter === 'critical') return alert.severity === 'critical' && !alert.is_resolved;
    return true;
  });

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Bell className="h-8 w-8 text-primary" />
              Alert Center
            </h1>
            <p className="text-muted-foreground">
              Monitor and manage financial alerts and anomalies
            </p>
          </div>
          <Button onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <Separator />

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Alerts</p>
                  <p className="text-3xl font-bold">{stats?.total || 0}</p>
                </div>
                <div className="h-12 w-12 rounded-lg bg-muted flex items-center justify-center">
                  <Bell className="h-6 w-6 text-muted-foreground" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Unread</p>
                  <p className="text-3xl font-bold text-healthcare-blue">{stats?.unread || 0}</p>
                </div>
                <div className="h-12 w-12 rounded-lg bg-healthcare-blue/10 flex items-center justify-center">
                  <EyeOff className="h-6 w-6 text-healthcare-blue" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Critical</p>
                  <p className="text-3xl font-bold text-healthcare-red">{stats?.critical || 0}</p>
                </div>
                <div className="h-12 w-12 rounded-lg bg-healthcare-red/10 flex items-center justify-center">
                  <AlertTriangle className="h-6 w-6 text-healthcare-red" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filter Buttons */}
        <div className="flex gap-2">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            onClick={() => setFilter('all')}
          >
            All Alerts
          </Button>
          <Button
            variant={filter === 'unread' ? 'default' : 'outline'}
            onClick={() => setFilter('unread')}
          >
            Unread ({stats?.unread || 0})
          </Button>
          <Button
            variant={filter === 'critical' ? 'default' : 'outline'}
            onClick={() => setFilter('critical')}
          >
            Critical ({stats?.critical || 0})
          </Button>
        </div>

        {/* Alerts List */}
        <Card>
          <CardHeader>
            <CardTitle>Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : filteredAlerts.length > 0 ? (
              <div className="space-y-4">
                {filteredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)} ${
                      alert.is_read ? 'opacity-60' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium">{alert.title}</h3>
                          {!alert.is_read && (
                            <Badge variant="secondary" className="h-5 px-1.5">New</Badge>
                          )}
                          {alert.is_resolved && (
                            <Badge variant="outline" className="h-5 px-1.5">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Resolved
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm mt-1">{alert.message}</p>
                        {alert.recommendation && (
                          <p className="text-sm mt-2 opacity-80">
                            <strong>Recommendation:</strong> {alert.recommendation}
                          </p>
                        )}
                        <div className="flex items-center gap-4 mt-3 text-xs opacity-70">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDateTime(alert.created_at)}
                          </span>
                          <span className="capitalize">{alert.category.replace('_', ' ')}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        {!alert.is_read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleMarkAsRead(alert.id)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        )}
                        {!alert.is_resolved && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleResolve(alert.id)}
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle className="h-12 w-12 text-healthcare-green mx-auto mb-4" />
                <h3 className="text-lg font-medium">All Clear</h3>
                <p className="text-muted-foreground">
                  No alerts match your current filter
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
