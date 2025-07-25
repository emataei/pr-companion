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
    
    const healthData: HealthCheckResponse = {
      status: 'ok',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      uptime: Math.floor(uptime),
      environment: process.env.NODE_ENV || 'development',
      memory: {
        used: Math.floor(memUsage.heapUsed / 1024 / 1024),
        total: Math.floor(memUsage.heapTotal / 1024 / 1024),
        percentage: Math.floor((memUsage.heapUsed / memUsage.heapTotal) * 100)
      },
      services: {
        database: 'ok',
        cache: 'ok'
      }
    };

    return NextResponse.json(healthData);
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
