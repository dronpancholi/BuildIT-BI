'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api/client';
import {
  LayoutDashboard,
  TrendingUp,
  Brain,
  BarChart3,
  AlertTriangle,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User,
  GitMerge,
  Network,
  BarChart,
  LayoutGrid,
  Database,
  Download,
  MessageSquare,
  Shield,
  Palette,
  Code,
  DollarSign,
  Zap,
  Target,
  BookOpen,
  Layers,
  Activity,
  Command,
  Bot,
  Building2,
  FileText,
  BedDouble,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Separator } from '@/components/ui/separator';

interface NavItem {
  name: string;
  href: string;
  icon: any;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const navigation: NavSection[] = [
  {
    label: 'Command',
    items: [
      { name: 'Command Center', href: '/dashboard', icon: LayoutDashboard },
      { name: 'Executive Center', href: '/executive-center', icon: Command },
      { name: 'AI CFO Core', href: '/ai-cfo', icon: Zap },
      { name: 'AI CFO Copilot', href: '/copilot', icon: Bot },
      { name: 'Workspace', href: '/workspace', icon: LayoutDashboard },
    ],
  },
  {
    label: 'Financial Performance',
    items: [
      { name: 'Revenue Intelligence', href: '/revenue', icon: TrendingUp },
      { name: 'Departments', href: '/departments', icon: Building2 },
      { name: 'Claims & Denials', href: '/claims', icon: FileText },
      { name: 'Occupancy', href: '/occupancy', icon: BedDouble },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { name: 'Intelligence Hub', href: '/intelligence', icon: Activity },
      { name: 'AI Insights', href: '/insights', icon: Brain },
      { name: 'Decisions', href: '/decisions', icon: GitMerge },
      { name: 'Forecasting', href: '/forecasting', icon: BarChart3 },
      { name: 'Strategic Planning', href: '/strategic', icon: Target },
      { name: 'Alert Center', href: '/alerts', icon: AlertTriangle },
    ],
  },
  {
    label: 'Data & Analytics',
    items: [
      { name: 'Analytics', href: '/analytics', icon: BarChart },
      { name: 'Dashboards', href: '/dashboards', icon: LayoutGrid },
      { name: 'Query Engine', href: '/analytics/query', icon: Database },
      { name: 'Exports', href: '/exports', icon: Download },
      { name: 'Visualization', href: '/visualization', icon: Palette },
    ],
  },
  {
    label: 'Platform',
    items: [
      { name: 'Metric Studio', href: '/metric-studio', icon: BarChart3 },
      { name: 'Semantic Layer', href: '/semantic', icon: Layers },
      { name: 'Formula Editor', href: '/formulas', icon: Code },
      { name: 'Knowledge Graph', href: '/knowledge-graph', icon: Network },
      { name: 'Governance', href: '/governance', icon: Shield },
      { name: 'Collaboration', href: '/collaboration', icon: MessageSquare },
      { name: 'Learning Engine', href: '/learning', icon: BookOpen },
      { name: 'Settings', href: '/settings', icon: Settings },
    ],
  },
];

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          const response = await api.get('/auth/me');
          setUser(response.data);
        }
      } catch (error) {
        console.error('Failed to fetch user:', error);
      }
    };

    fetchUser();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col border-r bg-card transition-all duration-300',
          collapsed ? 'w-[68px]' : 'w-[260px]'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-4">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
                <span className="text-xs font-bold text-white">BI</span>
              </div>
              <span className="text-lg font-semibold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">BuildIT BI</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(!collapsed)}
            className="h-8 w-8"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>

        <Separator />

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-2 space-y-4">
          {navigation.map((section) => (
            <div key={section.label}>
              {!collapsed && (
                <div className="px-3 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {section.label}
                </div>
              )}
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-primary/10 text-primary'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      )}
                      title={collapsed ? item.name : undefined}
                    >
                      <item.icon className="h-5 w-5 flex-shrink-0" />
                      {!collapsed && <span>{item.name}</span>}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <Separator />

        {/* User Menu */}
        <div className="p-2">
          <DropdownMenu>
            <DropdownMenuTrigger className="w-full">
              <Button variant="ghost" className={cn('w-full justify-start gap-3', collapsed && 'justify-center')}>
                <Avatar className="h-8 w-8">
                  <AvatarImage src="" alt={user?.full_name || 'User'} />
                  <AvatarFallback>
                    {user?.full_name
                      ?.split(' ')
                      .map((n: string) => n[0])
                      .join('') || 'U'}
                  </AvatarFallback>
                </Avatar>
                {!collapsed && (
                  <div className="flex flex-col items-start text-left">
                    <span className="text-sm font-medium">{user?.full_name || 'User'}</span>
                    <span className="text-xs text-muted-foreground capitalize">{user?.role || 'viewer'}</span>
                  </div>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
