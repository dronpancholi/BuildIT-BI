'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { authAPI } from '@/lib/api/client';
import { Loader2, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';

interface PasswordRequirement {
  label: string;
  test: (p: string) => boolean;
}

const PASSWORD_RULES: PasswordRequirement[] = [
  { label: 'At least 8 characters', test: (p) => p.length >= 8 },
  { label: 'One uppercase letter', test: (p) => /[A-Z]/.test(p) },
  { label: 'One lowercase letter', test: (p) => /[a-z]/.test(p) },
  { label: 'One digit', test: (p) => /\d/.test(p) },
];

function PasswordStrengthMeter({ password }: { password: string }) {
  if (!password) return null;
  const passed = PASSWORD_RULES.filter((r) => r.test(password)).length;
  const pct = Math.round((passed / PASSWORD_RULES.length) * 100);
  const color =
    pct < 50 ? 'bg-red-500' : pct < 75 ? 'bg-yellow-500' : pct < 100 ? 'bg-orange-500' : 'bg-emerald-500';
  return (
    <div className="space-y-2">
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-300 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {PASSWORD_RULES.map((rule) => {
          const ok = rule.test(password);
          return (
            <div key={rule.label} className="flex items-center gap-1 text-xs">
              {ok ? (
                <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" />
              ) : (
                <XCircle className="h-3 w-3 text-muted-foreground/50 shrink-0" />
              )}
              <span className={ok ? 'text-emerald-600' : 'text-muted-foreground'}>{rule.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const ROLES = [
  { value: 'ceo', label: 'Chief Executive Officer' },
  { value: 'cfo', label: 'Chief Financial Officer' },
  { value: 'finance_manager', label: 'Finance Manager' },
  { value: 'department_head', label: 'Department Head' },
  { value: 'analyst', label: 'Analyst' },
  { value: 'viewer', label: 'Viewer (Read Only)' },
];

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm_password: '', role: 'viewer' });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const isFormValid = useCallback(() => {
    if (!form.full_name.trim()) return false;
    if (!form.email.includes('@')) return false;
    if (PASSWORD_RULES.some((r) => !r.test(form.password))) return false;
    if (form.password !== form.confirm_password) return false;
    return true;
  }, [form]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (form.password !== form.confirm_password) {
      setError('Passwords do not match');
      return;
    }
    if (PASSWORD_RULES.some((r) => !r.test(form.password))) {
      setError('Please meet all password requirements');
      return;
    }

    setLoading(true);
    try {
      await authAPI.register({
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        role: form.role,
      });
      // Auto-login after successful registration
      const loginRes = await authAPI.login(form.email, form.password);
      localStorage.setItem('access_token', loginRes.data.access_token);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
              <span className="text-xl font-bold text-primary-foreground">HFI</span>
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">Create Account</CardTitle>
          <CardDescription>Join the Healthcare Financial Intelligence Platform</CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-5">
            {error && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Full Name */}
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                type="text"
                placeholder="Dr. Jane Smith"
                value={form.full_name}
                onChange={set('full_name')}
                required
                disabled={loading}
                autoComplete="name"
              />
            </div>

            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="email">Work Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="jane.smith@hospital.org"
                value={form.email}
                onChange={set('email')}
                required
                disabled={loading}
                autoComplete="email"
              />
            </div>

            {/* Role */}
            <div className="space-y-2">
              <Label htmlFor="role">Your Role</Label>
              <select
                id="role"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={form.role}
                onChange={set('role')}
                disabled={loading}
              >
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Create a strong password"
                value={form.password}
                onChange={set('password')}
                required
                disabled={loading}
                autoComplete="new-password"
              />
              <PasswordStrengthMeter password={form.password} />
            </div>

            {/* Confirm Password */}
            <div className="space-y-2">
              <Label htmlFor="confirm_password">Confirm Password</Label>
              <Input
                id="confirm_password"
                type="password"
                placeholder="Repeat your password"
                value={form.confirm_password}
                onChange={set('confirm_password')}
                required
                disabled={loading}
                autoComplete="new-password"
              />
              {form.confirm_password && form.password !== form.confirm_password && (
                <p className="text-xs text-destructive">Passwords do not match</p>
              )}
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={loading || !isFormValid()}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                'Create Account'
              )}
            </Button>

            <div className="relative w-full">
              <Separator />
              <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-2 text-xs text-muted-foreground">
                Already have an account?
              </span>
            </div>

            <Link href="/login" className="w-full">
              <Button variant="outline" className="w-full" type="button">
                Sign In
              </Button>
            </Link>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}