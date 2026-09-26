import { CheckCircle2, CircleDashed, ShieldQuestion } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

/** Verification state always ships with an icon and a label, never colour alone. */
export function VerificationBadge({ value, className }: { value: string; className?: string }) {
  if (value === 'pending') {
    return <Badge variant="outline" className={cn('h-6 gap-1.5 border-pending/60 px-2 text-sm text-pending', className)}><CircleDashed aria-hidden />pending</Badge>;
  }
  if (value === 'verified') {
    return <Badge variant="outline" className={cn('h-6 gap-1.5 border-positive/50 px-2 text-sm text-positive', className)}><CheckCircle2 aria-hidden />verified</Badge>;
  }
  if (!value) return null;
  return <Badge variant="outline" className={cn('h-6 gap-1.5 px-2 text-sm text-muted-foreground', className)}><ShieldQuestion aria-hidden />{value}</Badge>;
}

/** Note type, coloured the same way as the graph nodes (entity amber, concept green, thesis blue, source grey). */
const kindStyle: Record<string, string> = {
  entity: 'bg-primary/15 text-primary',
  concept: 'bg-chart-2/15 text-chart-2',
  thesis: 'bg-thesis/15 text-thesis',
  source: 'bg-muted text-muted-foreground',
  schema: 'bg-muted text-muted-foreground',
};

export function KindBadge({ label, kind, className }: { label: string; kind?: string; className?: string }) {
  return (
    <Badge variant="secondary" className={cn('h-6 rounded-md px-2 text-sm font-medium', kind && kindStyle[kind], className)}>
      {label}
    </Badge>
  );
}
