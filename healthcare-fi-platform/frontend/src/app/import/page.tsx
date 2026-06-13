'use client';

import { useState } from 'react';
import { UploadCloud, FileType, CheckCircle2, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { dataImportAPI } from '@/lib/api/client';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export default function ImportCenterPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus('idle');
      setMessage('');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setProgress(20);
    
    try {
      // Simulate progress for large files
      const interval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const res = await dataImportAPI.uploadFile(file);
      
      clearInterval(interval);
      setProgress(100);
      setStatus('success');
      setMessage(res.data.message || 'File successfully imported.');
    } catch (err: any) {
      setProgress(0);
      setStatus('error');
      setMessage(err.response?.data?.detail || 'An error occurred during upload.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Data Import Center</h2>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card className="col-span-2">
            <CardHeader>
              <CardTitle>Historical Data Upload</CardTitle>
              <CardDescription>
                Upload your financial data in Excel (.xlsx) or CSV format.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div 
                className="border-2 border-dashed rounded-lg p-12 text-center hover:bg-muted/50 transition-colors cursor-pointer"
                onClick={() => document.getElementById('file-upload')?.click()}
              >
                <input 
                  type="file" 
                  id="file-upload" 
                  className="hidden" 
                  accept=".csv, .xlsx, .xls"
                  onChange={handleFileChange}
                />
                
                {file ? (
                  <div className="flex flex-col items-center gap-2">
                    <FileType className="h-10 w-10 text-primary" />
                    <span className="font-medium">{file.name}</span>
                    <span className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <UploadCloud className="h-10 w-10 text-muted-foreground" />
                    <span className="font-medium">Click to select a file</span>
                    <span className="text-xs text-muted-foreground">CSV, Excel files supported</span>
                  </div>
                )}
              </div>

              {uploading && (
                <div className="mt-6 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Uploading and processing...</span>
                    <span>{progress}%</span>
                  </div>
                  <Progress value={progress} />
                </div>
              )}

              {status === 'success' && (
                <Alert className="mt-6 border-green-500 bg-green-500/10">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <AlertTitle className="text-green-600">Success</AlertTitle>
                  <AlertDescription className="text-green-600">
                    {message}
                  </AlertDescription>
                </Alert>
              )}

              {status === 'error' && (
                <Alert variant="destructive" className="mt-6">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{message}</AlertDescription>
                </Alert>
              )}
            </CardContent>
            <CardFooter>
              <Button 
                onClick={handleUpload} 
                disabled={!file || uploading} 
                className="w-full"
              >
                {uploading ? 'Processing...' : 'Upload & Import'}
              </Button>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Format Requirements</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm space-y-4">
                <p>Ensure your file has the following required columns (case-insensitive):</p>
                <ul className="list-disc pl-4 space-y-2 text-muted-foreground">
                  <li><strong className="text-foreground">branch_id</strong>: Numeric ID of the branch</li>
                  <li><strong className="text-foreground">department_id</strong>: Numeric ID of the department</li>
                  <li><strong className="text-foreground">type</strong>: "revenue" or "expense"</li>
                  <li><strong className="text-foreground">amount</strong>: Numeric value</li>
                  <li><strong className="text-foreground">date</strong>: Date of transaction (e.g. YYYY-MM-DD)</li>
                  <li><strong className="text-foreground">category</strong>: (Optional) Expense category</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
