import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

const userSettingsSchema = z.object({
  theme: z.enum(['light', 'dark', 'auto']),
  notifications: z.object({
    email: z.boolean(),
    push: z.boolean(),
    sms: z.boolean(),
  }),
  privacy: z.object({
    publicProfile: z.boolean(),
    shareAnalytics: z.boolean(),
  }),
  language: z.string().min(2).max(5),
});

type UserSettings = z.infer<typeof userSettingsSchema>;

// In-memory storage for demo purposes
const userSettingsStore = new Map<string, UserSettings>();

export async function GET(
  request: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const { userId } = params;
    
    if (!userId) {
      return NextResponse.json(
        { success: false, error: 'User ID is required' },
        { status: 400 }
      );
    }

    const settings = userSettingsStore.get(userId) || {
      theme: 'auto' as const,
      notifications: {
        email: true,
        push: true,
        sms: false,
      },
      privacy: {
        publicProfile: false,
        shareAnalytics: true,
      },
      language: 'en-US',
    };

    return NextResponse.json({
      success: true,
      data: settings,
    });
  } catch (error) {
    console.error('Error fetching user settings:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function PUT(
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

    const validatedSettings = userSettingsSchema.parse(body);
    
    // Store the settings
    userSettingsStore.set(userId, validatedSettings);

    // Log the update for audit purposes
    console.log(`User ${userId} updated settings:`, {
      timestamp: new Date().toISOString(),
      changes: Object.keys(validatedSettings),
      userAgent: request.headers.get('user-agent') || 'unknown',
    });

    return NextResponse.json({
      success: true,
      data: validatedSettings,
      message: 'Settings updated successfully',
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Invalid settings data', 
          details: error.errors 
        },
        { status: 400 }
      );
    }

    console.error('Error updating user settings:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const { userId } = params;
    
    if (!userId) {
      return NextResponse.json(
        { success: false, error: 'User ID is required' },
        { status: 400 }
      );
    }

    const existed = userSettingsStore.delete(userId);
    
    if (!existed) {
      return NextResponse.json(
        { success: false, error: 'User settings not found' },
        { status: 404 }
      );
    }

    console.log(`User ${userId} settings deleted at ${new Date().toISOString()}`);

    return NextResponse.json({
      success: true,
      message: 'Settings deleted successfully',
    });
  } catch (error) {
    console.error('Error deleting user settings:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
