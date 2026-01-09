import React from 'react';
import { cx } from '@/lib/utils';

interface SectionContainerProps {
  children: React.ReactNode;
  className?: string;
  as?: 'section' | 'div';
}

export function SectionContainer({
  children,
  className,
  as: Component = 'section'
}: SectionContainerProps) {
  return (
    <Component className={cx('mx-auto max-w-7xl px-4 sm:px-6 lg:px-10', className)}>
      {children}
    </Component>
  );
}
