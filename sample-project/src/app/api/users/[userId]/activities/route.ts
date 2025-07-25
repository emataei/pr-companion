import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

const activitySchema = z.object({
  type: z.enum(['login', 'logout', 'profile_update', 'settings_change', 'api_call']),
  timestamp: z.string().datetime(),
  metadata: z.object({
    userAgent: z.string().optional(),
    ipAddress: z.string().optional(),
    duration: z.number().optional(),
  }).optional(),
});

type UserActivity = z.infer<typeof activitySchema>;

// In-memory storage for demo purposes
const userActivitiesStore = new Map<string, UserActivity[]>();

export async function GET(
  request: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const { userId } = params;
    const { searchParams } = new URL(request.url);
    
    if (!userId) {
      return NextResponse.json(
        { success: false, error: 'User ID is required' },
        { status: 400 }
      );
    }

    // Get query parameters for filtering
    const activityType = searchParams.get('type');
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');

    let activities = userActivitiesStore.get(userId) || [];

    // Filter by activity type if provided
    if (activityType) {
      activities = activities.filter(activity => activity.type === activityType);
    }

    // Apply pagination
    const paginatedActivities = activities.slice(offset, offset + limit);

    return NextResponse.json({
      success: true,
      data: {
        activities: paginatedActivities,
        total: activities.length,
        limit,
        offset,
      },
    });
  } catch (error) {
    console.error('Error fetching user activities:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const { userId } = params;
    const body = await request.json();

    if (!userId) {
      return NextResponse.json(
        { success: false, error: 'User ID is required' },
        { status: 400 }
      );
    }

    const validatedActivity = activitySchema.parse(body);
    
    // Get existing activities or create new array
    const existingActivities = userActivitiesStore.get(userId) || [];
    
    // Add new activity at the beginning (most recent first)
    existingActivities.unshift(validatedActivity);
    
    // Keep only last 1000 activities per user
    if (existingActivities.length > 1000) {
      existingActivities.splice(1000);
    }
    
    userActivitiesStore.set(userId, existingActivities);

    // Log the activity for audit purposes
    console.log(`User ${userId} activity logged:`, {
      type: validatedActivity.type,
      timestamp: validatedActivity.timestamp,
    });

    return NextResponse.json({
      success: true,
      data: validatedActivity,
      message: 'Activity logged successfully',
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Invalid activity data', 
          details: error.errors 
        },
        { status: 400 }
      );
    }

    console.error('Error logging user activity:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
