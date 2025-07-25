import { NextResponse } from 'next/server';

interface HealthCheckResponse {
  status: 'ok' | 'error' | 'maintenance';
  timestamp: string;
  version: string;
  uptime: number;
  environment: string;
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  services: {
    database: 'ok' | 'error';
    cache: 'ok' | 'error';
  };
}

export async function GET() {
  try {
    const uptime = process.uptime();
    const memUsage = process.memoryUsage();
    
    // Simulate service health checks
    const isDatabaseHealthy = Math.random() > 0.1; // 90% chance of being healthy
    const isCacheHealthy = Math.random() > 0.05; // 95% chance of being healthy
    
    const overallStatus = isDatabaseHealthy && isCacheHealthy ? 'ok' : 'error';
    
    const healthData: HealthCheckResponse = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      uptime: Math.floor(uptime),
      environment: process.env.NODE_ENV || 'development',
      memory: {
        used: Math.floor(memUsage.heapUsed / 1024 / 1024),
        total: Math.floor(memUsage.heapTotal / 1024 / 1024),
        percentage: Math.floor((memUsage.heapUsed / memUsage.heapTotal) * 100)
      },
      services: {
        database: isDatabaseHealthy ? 'ok' : 'error',
        cache: isCacheHealthy ? 'ok' : 'error'
      }
    };

    return NextResponse.json(healthData, {
      status: overallStatus === 'ok' ? 200 : 503,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Health check failed:', error);
    
    const errorResponse: HealthCheckResponse = {
      status: 'error',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      uptime: 0,
      environment: process.env.NODE_ENV || 'development',
      memory: {
        used: 0,
        total: 0,
        percentage: 0
      },
      services: {
        database: 'error',
        cache: 'error'
      }
    };

    return NextResponse.json(errorResponse, { status: 500 });
  }
}
