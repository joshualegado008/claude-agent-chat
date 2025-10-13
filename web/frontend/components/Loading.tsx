/**
 * Loading spinner component
 */

export function Loading({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div className="flex items-center justify-center">
      <div
        className={`animate-spin rounded-full border-4 border-gray-300 border-t-blue-600 ${sizeClasses[size]}`}
      />
    </div>
  );
}

export function LoadingScreen({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen space-y-4">
      <Loading size="lg" />
      {message && <p className="text-gray-600 dark:text-gray-400">{message}</p>}
    </div>
  );
}
