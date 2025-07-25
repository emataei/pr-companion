import { UserProfile } from '@/components/UserProfile';

/**
 * Props for the ProfileDemo component
 */
interface ProfileDemoProps {
  readonly userId?: string;
  readonly mode?: 'edit' | 'create';
}

/**
 * Demo component showcasing the UserProfile functionality
 * @param userId - Optional user ID for editing existing users
 * @param mode - Whether to edit or create a user
 */
export function ProfileDemo({ userId, mode = 'create' }: ProfileDemoProps) {
  const handleSave = async (formData: FormData) => {
    const userData = {
      name: formData.get('name') as string,
      email: formData.get('email') as string,
    };

    try {
      const url = userId ? `/api/users/${userId}` : '/api/users';
      const method = userId ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        throw new Error(`Failed to ${mode} user`);
      }

      const result = await response.json();
      console.log(`User ${mode}d successfully:`, result);
    } catch (error) {
      console.error(`Error ${mode}ing user:`, error);
      throw error;
    }
  };

  const title = mode === 'edit' ? 'Edit User Profile' : 'Create New User';
  const variant = mode === 'edit' ? 'primary' : 'secondary';

  return (
    <div className="profile-demo">
      <UserProfile
        title={title}
        onSave={handleSave}
        variant={variant}
        userId={userId}
      />
    </div>
  );
}
