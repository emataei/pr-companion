# GitHub Copilot Instructions

DO NOT ADD EMOJIS TO MARKDOWN FILES OR CODE COMMENTS.

## AI Assistant Guidelines for Code Generation

When generating code, please follow these patterns and conventions to maintain consistency and quality across the project.

---

## 🚀 Next.js/TypeScript Project Patterns

### Component Generation
When creating React components:
- Use TypeScript interfaces for props
- Implement proper error boundaries
- Include accessibility attributes
- Use semantic HTML elements
- Apply consistent naming conventions

```typescript
// Preferred component structure
interface ComponentProps {
  title: string;
  onAction: (data: FormData) => void;
  variant?: 'primary' | 'secondary';
}

export function MyComponent({ title, onAction, variant = 'primary' }: ComponentProps) {
  return (
    <div className={`component component--${variant}`}>
      <h2>{title}</h2>
      {/* Implementation */}
    </div>
  );
}
```

### API Route Generation
When creating API routes:
- Include proper TypeScript types
- Implement comprehensive error handling
- Use Zod or similar for validation
- Return consistent response formats

```typescript
// Preferred API route structure
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

const requestSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const data = requestSchema.parse(body);
    
    // Process data
    const result = await processData(data);
    
    return NextResponse.json({ success: true, data: result });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: error.errors },
        { status: 400 }
      );
    }
    
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### Function Generation
When creating utility functions:
- Keep functions focused and small
- Use descriptive names
- Include proper TypeScript typing
- Add JSDoc comments for complex logic

```typescript
/**
 * Formats a date string for display in the UI
 * @param date - ISO date string or Date object
 * @param format - Display format preference
 * @returns Formatted date string
 */
function formatDisplayDate(
  date: string | Date, 
  format: 'short' | 'long' = 'short'
): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  return format === 'short' 
    ? dateObj.toLocaleDateString()
    : dateObj.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
}
```

---

## Code Generation Preferences

### Error Handling
Always include proper error handling:
- Use try/catch blocks for async operations
- Provide meaningful error messages
- Include fallback behaviors
- Log errors appropriately

### Performance Considerations
When generating code:
- Prefer `const` over `let` when possible
- Use early returns to reduce nesting
- Implement proper memoization for expensive operations
- Consider lazy loading for large components

### Type Safety
- Avoid `any` types
- Use proper generic constraints
- Implement discriminated unions for complex state
- Prefer interfaces over types for object shapes

---

## � Development Workflow Support

### Test Generation
When creating tests, include:
- Unit tests for business logic
- Integration tests for API routes
- Component testing for UI elements
- Mock implementations for external dependencies

### Documentation Generation
For complex functions or components:
- Add JSDoc comments with parameter descriptions
- Include usage examples
- Document any side effects or assumptions
- Explain complex business logic

### File Organization
Follow these patterns:
- Group related functionality together
- Use index files for clean imports
- Separate concerns (UI, logic, data)
- Keep configuration files at appropriate levels

---

## � Tooling Integration

### ESLint/Prettier Compliance
Generated code should:
- Follow configured ESLint rules
- Use consistent formatting
- Include proper imports/exports
- Maintain consistent naming conventions

### Package Management
When suggesting dependencies:
- Prefer established, well-maintained packages
- Consider bundle size impact
- Check for TypeScript support
- Evaluate security and license considerations

---

## AI Assistance Focus Areas

### Code Completion
Prioritize helping with:
- Boilerplate reduction
- Type inference and completion
- Pattern recognition and replication
- Refactoring suggestions

### Code Explanation
When explaining code:
- Focus on business logic and intent
- Explain complex algorithms or patterns
- Highlight potential edge cases
- Suggest improvements or alternatives

### Debugging Assistance
Help identify:
- Common TypeScript errors
- React/Next.js specific issues
- Performance bottlenecks
- Security considerations

This project uses automated code quality analysis. Focus on helping developers write clean, maintainable code that follows established patterns rather than optimizing for specific metrics.