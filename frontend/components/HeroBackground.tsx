import React from 'react';
import { StarField } from './StarField';

interface HeroBackgroundProps {
  children: React.ReactNode;
  /** Show dot indicators at bottom (e.g. for landing; default false for auth pages) */
  showDots?: boolean;
  /** Optional extra class for the content wrapper */
  className?: string;
}

/** Full-viewport starry background for landing and auth pages. Uses StarField (cosmic theme). */
export const HeroBackground: React.FC<HeroBackgroundProps> = ({
  children,
  showDots = false,
  className = '',
}) => {
  return (
    <div className={`relative min-h-[100dvh] flex items-center justify-center overflow-hidden ${className}`}>
      <StarField />
      <div className="absolute inset-0 bg-gradient-to-b from-[hsl(230,35%,4%)]/30 via-transparent to-[hsl(230,35%,4%)]/50 z-[1]" />

      <div className="relative z-10 w-full flex items-center justify-center p-4 py-8">
        {children}
      </div>

      {showDots && (
        <div className="absolute bottom-6 left-0 right-0 z-10 flex justify-center gap-2">
          <span className="h-2 w-2 rounded-full bg-white/50" aria-hidden />
          <span className="h-2 w-2 rounded-full bg-white/30" aria-hidden />
          <span className="h-2 w-2 rounded-full bg-white/30" aria-hidden />
        </div>
      )}
    </div>
  );
};
