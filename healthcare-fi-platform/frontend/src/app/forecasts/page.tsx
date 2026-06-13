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
  BarChart3,
  TrendingUp,
  Calendar,
  RefreshCw,
  Download,
  Loader2,
} from 'lucide-react';
import { forecastsAPI } from '@/lib/api/client';
import { ForecastResult } from '@/lib/types';
import { formatCurrency, formatPercentage, getConfidenceColor } from '@/lib/utils/format';

export default function ForecastsPage() {
  const [metricType, setMetricType] = useState('revenue');
  const [periodsAhead, setPeriodsAhead] = useState(12);
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerateForecast = async () => {
    setLoading(true);
    try {
      const response = await forecastsAPI.createForecast({
        metric_type: metricType,
        periods_ahead: periodsAhead,
      });
      setForecast(response.data);
    } catch (error) {
      console.error('Failed to generate forecast:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <BarChart3 className="h-8 w-8 text-primary" />
              Forecasting Platform
            </h1>
            <p className="text-muted-foreground">
              AI-powered financial forecasting with confidence intervals
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        <Separator />

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Forecast Configuration */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Forecast Configuration</CardTitle>
                <CardDescription>Configure your forecast parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="metric">Metric Type</Label>
                  <select
                    id="metric"
                    className="w-full p-2 border rounded-md bg-background"
                    value={metricType}
                    onChange={(e) => setMetricType(e.target.value)}
                  >
                    <option value="revenue">Revenue</option>
                    <option value="expenses">Expenses</option>
                    <option value="profit">Net Profit</option>
                    <option value="occupancy">Occupancy Rate</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="periods">Forecast Periods (Months)</Label>
                  <Input
                    id="periods"
                    type="number"
                    min="1"
                    max="36"
                    value={periodsAhead}
                    onChange={(e) => setPeriodsAhead(Number(e.target.value))}
                  />
                </div>

                <Button 
                  className="w-full" 
                  onClick={handleGenerateForecast}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <BarChart3 className="h-4 w-4 mr-2" />
                      Generate Forecast
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Forecast Info */}
            <Card>
              <CardHeader>
                <CardTitle>How It Works</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p>
                  Our forecasting engine uses advanced statistical methods including:
                </p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Linear Regression</li>
                  <li>Moving Averages</li>
                  <li>Seasonal Decomposition</li>
                  <li>Trend Analysis</li>
                </ul>
                <p>
                  Forecasts include confidence intervals to help you understand the range of possible outcomes.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Forecast Results */}
          <div className="lg:col-span-2 space-y-6">
            {forecast ? (
              <>
                {/* Forecast Summary */}
                <div className="grid gap-4 md:grid-cols-3">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-sm font-medium text-muted-foreground">Predicted Value</p>
                        <p className="text-3xl font-bold text-primary">
                          {formatCurrency(forecast.predicted_value, true)}
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-sm font-medium text-muted-foreground">Confidence Score</p>
                        <p className={`text-3xl font-bold ${getConfidenceColor(forecast.confidence_score)}`}>
                          {formatPercentage(forecast.confidence_score * 100, 0)}
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-sm font-medium text-muted-foreground">Methodology</p>
                        <p className="text-lg font-medium capitalize">
                          {forecast.methodology.replace('_', ' ')}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Confidence Interval */}
                <Card>
                  <CardHeader>
                    <CardTitle>Confidence Interval</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Lower Bound</span>
                        <span className="font-medium">{formatCurrency(forecast.confidence_lower, true)}</span>
                      </div>
                      <div className="relative h-4 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="absolute h-full bg-primary/20"
                          style={{
                            left: '20%',
                            width: '60%',
                          }}
                        />
                        <div 
                          className="absolute h-full bg-primary"
                          style={{
                            left: '45%',
                            width: '10%',
                          }}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Upper Bound</span>
                        <span className="font-medium">{formatCurrency(forecast.confidence_upper, true)}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Historical Data */}
                <Card>
                  <CardHeader>
                    <CardTitle>Historical Data & Forecast</CardTitle>
                    <CardDescription>
                      Showing {forecast.historical_data.length} periods of historical data
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px] flex items-center justify-center bg-muted/50 rounded-lg">
                      <div className="text-center">
                        <TrendingUp className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                        <p className="text-muted-foreground">
                          Historical trend and forecast visualization
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          ECharts line chart with confidence bands
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Forecast Decomposition */}
                <Card>
                  <CardHeader>
                    <CardTitle>Forecast Decomposition</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="p-4 rounded-lg bg-muted/50 text-center">
                        <p className="text-sm font-medium text-muted-foreground">Trend</p>
                        <p className="text-lg font-medium mt-1">Increasing</p>
                        <p className="text-xs text-muted-foreground">+2.3% monthly</p>
                      </div>
                      <div className="p-4 rounded-lg bg-muted/50 text-center">
                        <p className="text-sm font-medium text-muted-foreground">Seasonality</p>
                        <p className="text-lg font-medium mt-1">Moderate</p>
                        <p className="text-xs text-muted-foreground">Q4 peak pattern</p>
                      </div>
                      <div className="p-4 rounded-lg bg-muted/50 text-center">
                        <p className="text-sm font-medium text-muted-foreground">Noise</p>
                        <p className="text-lg font-medium mt-1">Low</p>
                        <p className="text-xs text-muted-foreground">High signal-to-noise</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="h-[600px] flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium">No Forecast Generated</h3>
                  <p className="text-muted-foreground mt-1">
                    Configure parameters and generate a forecast to see results
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
