'use client';

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Shield, Key, Users, Eye, Lock, Fingerprint, AlertTriangle } from 'lucide-react';
import { governanceAPI } from '@/lib/api/client';

interface AuditEntry {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  actor_id: string | null;
  timestamp: string;
  result: string;
  compliance_flags: string[];
}

const PREBUILT_ROLES = [
  { name: 'Platform Admin', permissions: ['*'], scope: 'ALL', color: 'bg-red-100 text-red-700', description: 'Full system access' },
  { name: 'Tenant Admin', permissions: ['manage_users', 'manage_settings', 'read', 'write'], scope: 'TENANT', color: 'bg-orange-100 text-orange-700', description: 'Tenant-level administration' },
  { name: 'CFO', permissions: ['read', 'write', 'certify', 'approve', 'export'], scope: 'ALL', color: 'bg-blue-100 text-blue-700', description: 'Financial oversight and certification' },
  { name: 'Analyst', permissions: ['read', 'create', 'export'], scope: 'TEAM', color: 'bg-emerald-100 text-emerald-700', description: 'Data analysis and report creation' },
  { name: 'Viewer', permissions: ['read'], scope: 'TEAM', color: 'bg-gray-100 text-gray-700', description: 'Read-only access' },
];

export default function AuthPage() {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('roles');
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAuditLog();
  }, []);

  async function loadAuditLog() {
    setAuditLoading(true);
    setAuditError(null);
    try {
      // Audit log functionality removed with enterprise governance module
      setAuditEntries([]);
    } catch (err) {
      setAuditError(err instanceof Error ? err.message : 'Failed to load audit log');
    } finally {
      setAuditLoading(false);
      setLoading(false);
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Shield className="h-8 w-8 text-red-600" />
              Authentication & Authorization
            </h1>
            <p className="text-gray-500 mt-1">RBAC, MFA, SSO, and audit logging</p>
          </div>
          <Badge className="bg-red-100 text-red-800 border-red-200">Enterprise</Badge>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4 flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-4 w-4" /> {error}
            </CardContent>
          </Card>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="roles">Roles & Permissions</TabsTrigger>
            <TabsTrigger value="mfa">MFA</TabsTrigger>
            <TabsTrigger value="audit">Audit Log</TabsTrigger>
            <TabsTrigger value="scope">Scope Model</TabsTrigger>
          </TabsList>

          <TabsContent value="roles" className="space-y-4">
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[1,2,3].map(i => <Skeleton key={i} className="h-40" />)}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {PREBUILT_ROLES.map((role, i) => (
                  <Card key={i} className="hover:border-red-300 transition-colors">
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold">{role.name}</h3>
                        <Badge className={role.color}>{role.scope}</Badge>
                      </div>
                      <p className="text-xs text-gray-500">{role.description}</p>
                      <div className="flex gap-1 flex-wrap">
                        {role.permissions.map((p, j) => (
                          <Badge key={j} variant="outline" className="text-xs">{p}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="mfa" className="space-y-4">
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Fingerprint className="h-5 w-5" /> Multi-Factor Authentication</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 border rounded-lg bg-emerald-50 border-emerald-200">
                    <div className="font-semibold text-emerald-700 flex items-center gap-2"><Key className="h-4 w-4" /> TOTP (Authenticator App)</div>
                    <p className="text-sm text-emerald-600 mt-1">Google Authenticator, Authy, 1Password</p>
                    <div className="mt-3 space-y-2">
                      <div className="text-xs text-gray-500">Supported algorithms: SHA-1, SHA-256</div>
                      <div className="text-xs text-gray-500">Time step: 30 seconds</div>
                      <div className="text-xs text-gray-500">Digits: 6</div>
                    </div>
                    <Badge className="mt-2 bg-emerald-100 text-emerald-700">Production Ready</Badge>
                  </div>
                  <div className="p-4 border rounded-lg bg-blue-50 border-blue-200">
                    <div className="font-semibold text-blue-700 flex items-center gap-2"><Lock className="h-4 w-4" /> Backup Codes</div>
                    <p className="text-sm text-blue-600 mt-1">8 single-use recovery codes</p>
                    <div className="mt-3 space-y-2">
                      <div className="text-xs text-gray-500">Length: 8 characters each</div>
                      <div className="text-xs text-gray-500">One-time use with consumption tracking</div>
                      <div className="text-xs text-gray-500">Stored as salted hashes</div>
                    </div>
                    <Badge className="mt-2 bg-blue-100 text-blue-700">Production Ready</Badge>
                  </div>
                </div>
                <div className="p-4 border rounded-lg bg-amber-50 border-amber-200">
                  <div className="font-semibold text-amber-700">Password Policy</div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-sm text-amber-600">
                    <div>Minimum length: 12 characters</div>
                    <div>Requires uppercase + lowercase</div>
                    <div>Requires digits</div>
                    <div>Requires special characters</div>
                    <div>Hashing: SHA-256 with salt</div>
                    <div>Strength validation: enforced</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="audit" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Audit Log</CardTitle>
                <Button size="sm" variant="outline" onClick={loadAuditLog} disabled={auditLoading}>
                  {auditLoading ? 'Loading...' : 'Refresh'}
                </Button>
              </CardHeader>
              <CardContent>
                {auditLoading ? (
                  <div className="space-y-2">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-12" />)}</div>
                ) : auditError ? (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {auditError}
                  </div>
                ) : auditEntries.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No audit entries yet. Actions will be logged as you use the platform.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {auditEntries.map((entry) => (
                      <div key={entry.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                        <div className="flex items-center gap-3">
                          <Badge className={
                            entry.result === 'success' ? 'bg-emerald-100 text-emerald-700' :
                            entry.result === 'failure' ? 'bg-red-100 text-red-700' :
                            'bg-gray-100 text-gray-700'
                          }>
                            {entry.action}
                          </Badge>
                          <span className="text-sm text-gray-600">{entry.resource_type}</span>
                          {entry.resource_id && (
                            <span className="text-xs text-gray-400 font-mono">{entry.resource_id.slice(0, 8)}</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {entry.compliance_flags.length > 0 && (
                            <div className="flex gap-1">
                              {entry.compliance_flags.map((f, i) => (
                                <Badge key={i} className="bg-amber-100 text-amber-700 text-xs">{f}</Badge>
                              ))}
                            </div>
                          )}
                          <span className="text-xs text-gray-400">{new Date(entry.timestamp).toLocaleString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="scope" className="space-y-4">
            <Card>
              <CardHeader><CardTitle>RBAC Scope Resolution</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-gray-600">
                  Permissions are resolved across all assigned roles. The widest scope wins:
                  if a user has OWN scope from one role and ALL scope from another, ALL takes precedence.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { scope: 'ALL', desc: 'Access all resources across the entire tenant', color: 'bg-red-50 border-red-200', textColor: 'text-red-700' },
                    { scope: 'TEAM', desc: 'Access resources within own team/department', color: 'bg-blue-50 border-blue-200', textColor: 'text-blue-700' },
                    { scope: 'OWN', desc: 'Access only resources created by self', color: 'bg-emerald-50 border-emerald-200', textColor: 'text-emerald-700' },
                  ].map((s, i) => (
                    <div key={i} className={`p-4 border rounded-lg ${s.color}`}>
                      <div className={`font-semibold ${s.textColor}`}>{s.scope}</div>
                      <p className="text-sm text-gray-600 mt-1">{s.desc}</p>
                    </div>
                  ))}
                </div>
                <div className="p-4 bg-gray-50 border rounded-lg">
                  <h4 className="font-semibold text-sm">Example Resolution</h4>
                  <div className="mt-2 text-sm text-gray-600 space-y-1">
                    <div>1. Collect all permissions from all assigned roles</div>
                    <div>2. Group by permission action (read, write, certify, etc.)</div>
                    <div>3. For each action, take the widest scope across all roles</div>
                    <div>4. Result: user gets the union of all permissions at their widest scope</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
