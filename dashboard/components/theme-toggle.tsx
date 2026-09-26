'use client';

import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { setTheme, useTheme } from '@/components/use-theme';

export function ThemeToggle({ className }: { className?: string }) {
  const theme = useTheme();
  const next = theme === 'dark' ? 'light' : 'dark';
  return (
    <Button
      variant="outline"
      size="icon"
      className={className}
      onClick={() => setTheme(next)}
      aria-label={next === 'light' ? 'สลับเป็นโหมดสว่าง' : 'สลับเป็นโหมดมืด'}
      title={next === 'light' ? 'โหมดสว่าง' : 'โหมดมืด'}
    >
      <Sun className="hidden size-4 dark:block" aria-hidden />
      <Moon className="size-4 dark:hidden" aria-hidden />
    </Button>
  );
}
