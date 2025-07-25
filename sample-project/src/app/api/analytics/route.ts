// Analytics API route for user engagement metrics
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

// Validation schema for analytics query
const AnalyticsQuerySchema = z.object({
  userId: z.string().uuid().optional(),
  startDate: z.string().datetime().optional(),
  endDate: z.string().datetime().optional(),
  metric: z.enum(['pageviews', 'sessions', 'engagement', 'all']).default('all'),
})

interface AnalyticsData {
  userId?: string
  metric: string
  value: number
  date: string
}

// Mock analytics data
const mockAnalytics: AnalyticsData[] = [
  { userId: '550e8400-e29b-41d4-a716-446655440000', metric: 'pageviews', value: 245, date: '2025-01-20T00:00:00Z' },
  { userId: '550e8400-e29b-41d4-a716-446655440000', metric: 'sessions', value: 45, date: '2025-01-20T00:00:00Z' },
  { userId: '550e8400-e29b-41d4-a716-446655440000', metric: 'engagement', value: 85, date: '2025-01-20T00:00:00Z' },
  { userId: '550e8400-e29b-41d4-a716-446655440001', metric: 'pageviews', value: 189, date: '2025-01-20T00:00:00Z' },
  { userId: '550e8400-e29b-41d4-a716-446655440001', metric: 'sessions', value: 32, date: '2025-01-20T00:00:00Z' },
  { userId: '550e8400-e29b-41d4-a716-446655440001', metric: 'engagement', value: 72, date: '2025-01-20T00:00:00Z' },
]

/**
 * GET /api/analytics - Retrieve user analytics data
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const params = AnalyticsQuerySchema.parse({
      userId: searchParams.get('userId'),
      startDate: searchParams.get('startDate'),
      endDate: searchParams.get('endDate') || new Date().toISOString(),
      metric: searchParams.get('metric'),
    })

    let filteredData = mockAnalytics

    // Filter by user ID if provided
    if (params.userId) {
      filteredData = filteredData.filter(item => item.userId === params.userId)
    }

    // Filter by metric if not 'all'
    if (params.metric !== 'all') {
      filteredData = filteredData.filter(item => item.metric === params.metric)
    }

    // Calculate summary statistics
    const summary = {
      totalPageviews: filteredData.filter(d => d.metric === 'pageviews').reduce((sum, d) => sum + d.value, 0),
      totalSessions: filteredData.filter(d => d.metric === 'sessions').reduce((sum, d) => sum + d.value, 0),
      avgEngagement: Math.round(
        filteredData.filter(d => d.metric === 'engagement').reduce((sum, d) => sum + d.value, 0) /
        Math.max(filteredData.filter(d => d.metric === 'engagement').length, 1)
      ),
      uniqueUsers: new Set(filteredData.map(d => d.userId)).size,
    }

    return NextResponse.json({
      success: true,
      data: filteredData,
      summary,
      query: params
    })

  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: 'Invalid query parameters', details: error.errors },
        { status: 400 }
      )
    }

    console.error('Error fetching analytics:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}

/**
 * POST /api/analytics - Record new analytics event
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const EventSchema = z.object({
      userId: z.string().uuid(),
      metric: z.enum(['pageview', 'session_start', 'engagement']),
      value: z.number().min(0).optional().default(1),
      metadata: z.object({}).passthrough().optional(),
    })

    const validatedData = EventSchema.parse(body)

    // Create new analytics entry
    const newEntry: AnalyticsData = {
      userId: validatedData.userId,
      metric: validatedData.metric,
      value: validatedData.value,
      date: new Date().toISOString()
    }

    mockAnalytics.push(newEntry)

    return NextResponse.json(
      { success: true, message: 'Analytics event recorded', data: newEntry },
      { status: 201 }
    )

  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: error.errors },
        { status: 400 }
      )
    }

    console.error('Error recording analytics:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
