/**
 * Loading spinner component
 */

import Image from 'next/image';

export function Loading({
  size = 'md',
  useLogo = false
}: {
  size?: 'sm' | 'md' | 'lg';
  useLogo?: boolean;
}) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  const logoSizes = {
    sm: 16,
    md: 32,
    lg: 48,
  };

  if (useLogo) {
    return (
      <div className="flex items-center justify-center">
        <Image
          src="/images/claude-chorus-icon-256.png"
          alt="Loading..."
          width={logoSizes[size]}
          height={logoSizes[size]}
          className="animate-pulse"
        />
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center">
      <div
        className={`animate-spin rounded-full border-4 border-slate-700 border-t-chorus-primary ${sizeClasses[size]}`}
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
