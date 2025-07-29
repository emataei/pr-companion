interface UserCardProps {
  readonly name: string;
  readonly email: string;
  readonly role: string;
}

export function UserCard({ name, email, role }: UserCardProps) {
  return (
    <div style={{ 
      border: '1px solid #ddd', 
      borderRadius: '8px', 
      padding: '1rem', 
      margin: '1rem 0',
      backgroundColor: '#f9f9f9'
    }}>
      <h3>{name}</h3>
      <p>{email}</p>
      <span style={{ 
        backgroundColor: '#007acc', 
        color: 'white', 
        padding: '0.25rem 0.5rem', 
        borderRadius: '4px', 
        fontSize: '0.875rem' 
      }}>
        {role}
      </span>
    </div>
  );
}
