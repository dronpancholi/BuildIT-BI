'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { authAPI, workspaceAPI } from '@/lib/api/client';
import {
  Settings,
  User,
  Bell,
  Shield,
  Palette,
  Save,
  Check,
  AlertTriangle,
} from 'lucide-react';

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

interface NotificationConfig {
  channels: {
    email: { enabled: boolean; address: string };
    in_app: { enabled: boolean; sound: boolean };
  };
  preferences: {
    briefing_notifications: { enabled: boolean; frequency: string };
    alert_notifications: { enabled: boolean; frequency: string };
    assignment_notifications: { enabled: boolean; frequency: string };
  };
  quiet_hours: { enabled: boolean; start: string; end: string };
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Profile state
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');

  // Notification state
  const [notifications, setNotifications] = useState<NotificationConfig | null>(null);
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [inAppEnabled, setInAppEnabled] = useState(true);
  const [briefingEnabled, setBriefingEnabled] = useState(true);
  const [alertEnabled, setAlertEnabled] = useState(true);

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [profileRes, notifRes] = await Promise.allSettled([
        authAPI.getMe(),
        workspaceAPI.getNotifications(),
      ]);

      if (profileRes.status === 'fulfilled') {
        const p = profileRes.value.data;
        setProfile(p);
        setFullName(p.full_name || '');
        setEmail(p.email || '');
      }

      if (notifRes.status === 'fulfilled') {
        const n = notifRes.value.data;
        setNotifications(n);
        setEmailEnabled(n.channels?.email?.enabled ?? true);
        setInAppEnabled(n.channels?.in_app?.enabled ?? true);
        setBriefingEnabled(n.preferences?.briefing_notifications?.enabled ?? true);
        setAlertEnabled(n.preferences?.alert_notifications?.enabled ?? true);
      }
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveProfile() {
    setSaving(true);
    setMessage(null);
    try {
      await authAPI.updateMe({ full_name: fullName, email });
      setMessage({ type: 'success', text: 'Profile updated successfully' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to update profile' });
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveNotifications() {
    setSaving(true);
    setMessage(null);
    try {
      await workspaceAPI.updateNotifications({
        channel: 'email',
        channel_enabled: emailEnabled,
      });
      await workspaceAPI.updateNotifications({
        channel: 'in_app',
        channel_enabled: inAppEnabled,
      });
      setMessage({ type: 'success', text: 'Notification preferences saved' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to save notifications' });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex-1 space-y-6 p-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-[400px]" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Settings className="h-8 w-8 text-primary" />
            Settings
          </h1>
          <p className="text-muted-foreground">
            Manage your account and platform preferences
          </p>
        </div>

        {message && (
          <div className={`flex items-center gap-2 p-4 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {message.type === 'success' ? <Check className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            {message.text}
            <Button variant="ghost" size="sm" className="ml-auto" onClick={() => setMessage(null)}>×</Button>
          </div>
        )}

        <Separator />

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList>
            <TabsTrigger value="profile" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="notifications" className="flex items-center gap-2">
              <Bell className="h-4 w-4" />
              Notifications
            </TabsTrigger>
            <TabsTrigger value="security" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Security
            </TabsTrigger>
            <TabsTrigger value="appearance" className="flex items-center gap-2">
              <Palette className="h-4 w-4" />
              Appearance
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>Update your personal information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="fullName">Full Name</Label>
                    <Input id="fullName" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="John Doe" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="john.doe@hospital.com" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Input id="role" value={profile?.role || 'CFO'} disabled />
                </div>
                <Button onClick={handleSaveProfile} disabled={saving}>
                  {saving ? 'Saving...' : 'Save Changes'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>Configure how you receive alerts and updates</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div>
                    <p className="font-medium">Email Notifications</p>
                    <p className="text-sm text-muted-foreground">Receive alerts via email</p>
                  </div>
                  <input type="checkbox" className="h-4 w-4" checked={emailEnabled} onChange={e => setEmailEnabled(e.target.checked)} />
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div>
                    <p className="font-medium">In-App Notifications</p>
                    <p className="text-sm text-muted-foreground">Show notifications in the app</p>
                  </div>
                  <input type="checkbox" className="h-4 w-4" checked={inAppEnabled} onChange={e => setInAppEnabled(e.target.checked)} />
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div>
                    <p className="font-medium">Briefing Notifications</p>
                    <p className="text-sm text-muted-foreground">Receive daily briefing alerts</p>
                  </div>
                  <input type="checkbox" className="h-4 w-4" checked={briefingEnabled} onChange={e => setBriefingEnabled(e.target.checked)} />
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div>
                    <p className="font-medium">Critical Alerts</p>
                    <p className="text-sm text-muted-foreground">Immediate notification for critical issues</p>
                  </div>
                  <input type="checkbox" className="h-4 w-4" checked={alertEnabled} onChange={e => setAlertEnabled(e.target.checked)} />
                </div>
                <Button onClick={handleSaveNotifications} disabled={saving}>
                  {saving ? 'Saving...' : 'Save Preferences'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Security Settings</CardTitle>
                <CardDescription>Manage your account security</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="currentPassword">Current Password</Label>
                  <Input id="currentPassword" type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="newPassword">New Password</Label>
                  <Input id="newPassword" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <Input id="confirmPassword" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} />
                </div>
                <Button disabled>
                  Update Password (Coming Soon)
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="appearance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Appearance Settings</CardTitle>
                <CardDescription>Customize the look and feel</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Theme</Label>
                  <div className="flex gap-2">
                    <Button variant="outline" className="flex-1">Light</Button>
                    <Button variant="default" className="flex-1">Dark</Button>
                    <Button variant="outline" className="flex-1">System</Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Accent Color</Label>
                  <div className="flex gap-2">
                    <div className="h-8 w-8 rounded-full bg-healthcare-blue cursor-pointer ring-2 ring-offset-2 ring-primary" />
                    <div className="h-8 w-8 rounded-full bg-healthcare-teal cursor-pointer" />
                    <div className="h-8 w-8 rounded-full bg-healthcare-green cursor-pointer" />
                    <div className="h-8 w-8 rounded-full bg-healthcare-amber cursor-pointer" />
                  </div>
                </div>
                <Button disabled>
                  Save Appearance (Coming Soon)
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
