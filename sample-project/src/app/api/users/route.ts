// Enhanced API route with proper security and validation
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

// Input validation schemas
const UserQuerySchema = z.object({
  id: z.string().uuid().optional(),
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(10),
})

const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  phone: z.string().optional(),
  location: z.string().max(200).optional(),
  bio: z.string().max(500).optional(),
})

const UpdateUserSchema = CreateUserSchema.partial()

// User interface
interface User {
  id: string
  name: string
  email: string
  phone?: string
  location?: string
  bio?: string
  createdAt: string
}

// Mock database for demonstration
const mockUsers: User[] = [
  { 
    id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'John Doe', 
    email: 'john@example.com',
    phone: '+1-555-0123',
    location: 'San Francisco, CA',
    bio: 'Full-stack developer with a passion for clean code.',
    createdAt: new Date().toISOString()
  },
  { 
    id: '550e8400-e29b-41d4-a716-446655440001',
    name: 'Jane Smith', 
    email: 'jane@example.com',
    location: 'New York, NY',
    bio: 'UX designer and frontend developer.',
    createdAt: new Date().toISOString()
  }
]

/**
 * GET /api/users - Retrieve users with optional filtering and pagination
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const params = UserQuerySchema.parse({
      id: searchParams.get('id'),
      page: searchParams.get('page'),
      limit: searchParams.get('limit'),
    })

    // If specific ID requested, return single user
    if (params.id) {
      const user = mockUsers.find(u => u.id === params.id)
      if (!user) {
        return NextResponse.json(
          { success: false, error: 'User not found' },
          { status: 404 }
        )
      }
      return NextResponse.json({ success: true, data: user })
    }

    // Paginate results
    const startIndex = (params.page - 1) * params.limit
    const endIndex = startIndex + params.limit
    const paginatedUsers = mockUsers.slice(startIndex, endIndex)

    return NextResponse.json({
      success: true,
      data: paginatedUsers,
      pagination: {
        page: params.page,
        limit: params.limit,
        total: mockUsers.length,
        pages: Math.ceil(mockUsers.length / params.limit)
      }
    })

  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: 'Invalid query parameters', details: error.errors },
        { status: 400 }
      )
    }

    console.error('Error fetching users:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}

/**
 * POST /api/users - Create a new user with proper validation
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const validatedData = CreateUserSchema.parse(body)

    // Check for duplicate email
    const existingUser = mockUsers.find(u => u.email === validatedData.email)
    if (existingUser) {
      return NextResponse.json(
        { success: false, error: 'User with this email already exists' },
        { status: 409 }
      )
    }

    // Create new user
    const newUser = {
      id: crypto.randomUUID(),
      ...validatedData,
      createdAt: new Date().toISOString()
    }

    mockUsers.push(newUser)

    return NextResponse.json(
      { success: true, message: 'User created successfully', data: newUser },
      { status: 201 }
    )

  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: error.errors },
        { status: 400 }
      )
    }

    console.error('Error creating user:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
