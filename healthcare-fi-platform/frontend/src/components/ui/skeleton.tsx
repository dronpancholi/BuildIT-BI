"use client";

import { cn } from "@/lib/utils";

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="skeleton"
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className
      )}
      {...props}
    />
  );
}

function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-xl bg-card p-4 ring-1 ring-foreground/10",
        className
      )}
    >
      <div className="flex items-center gap-3">
        <Skeleton className="size-10 shrink-0 rounded-lg" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
        <Skeleton className="h-5 w-16 shrink-0 rounded-full" />
      </div>
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-5/6" />
      <div className="flex items-center justify-between pt-2">
        <div className="flex gap-2">
          <Skeleton className="h-5 w-14 rounded-full" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-16 rounded-lg" />
          <Skeleton className="h-8 w-20 rounded-lg" />
        </div>
      </div>
    </div>
  );
}

function SkeletonStatCard() {
  return (
    <div className="flex flex-col gap-2 rounded-xl bg-card p-4 ring-1 ring-foreground/10">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-7 w-16" />
      <Skeleton className="h-3 w-24" />
    </div>
  );
}

function SkeletonTableRow() {
  return (
    <div className="flex items-center gap-4 border-b border-border px-4 py-3">
      <Skeleton className="h-5 w-16 rounded-full" />
      <Skeleton className="h-5 w-20" />
      <Skeleton className="h-4 flex-1" />
      <Skeleton className="h-4 w-12" />
      <Skeleton className="h-4 w-20" />
      <Skeleton className="h-4 w-16" />
      <Skeleton className="h-5 w-14 rounded-full" />
      <Skeleton className="h-8 w-16 rounded-lg" />
    </div>
  );
}

function SkeletonBriefingCard() {
  return (
    <div className="flex flex-col gap-3 rounded-xl bg-card p-4 ring-1 ring-foreground/10">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-24 rounded-full" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <Skeleton className="h-4 w-4/5" />
      <Skeleton className="h-3 w-3/5" />
      <div className="space-y-1.5">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-4/5" />
      </div>
      <Skeleton className="h-3 w-1/3" />
    </div>
  );
}

export { Skeleton, SkeletonCard, SkeletonStatCard, SkeletonTableRow, SkeletonBriefingCard };
