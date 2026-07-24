import { cn } from "@/lib/utils";

// Enhanced Skeleton with shimmer animation
export function Skeleton({ className, ...props }) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-md bg-gray-200 dark:bg-gray-800",
        "before:absolute before:inset-0 before:-translate-x-full",
        "before:animate-[shimmer_1.5s_infinite]",
        "before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent",
        className
      )}
      {...props}
    />
  );
}

// News Card Skeleton - Matches NewsCardHorizontal layout
export function NewsCardSkeleton() {
  return (
    <div className="flex gap-3 p-3 border-b border-gray-100 dark:border-gray-800 animate-pulse">
      {/* Image Skeleton */}
      <div className="relative w-[110px] h-[75px] flex-shrink-0">
        <Skeleton className="w-full h-full rounded-lg" />
      </div>
      
      {/* Content Skeleton */}
      <div className="flex-1 flex flex-col justify-center gap-2">
        {/* Badge + Time */}
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-16 rounded" />
          <Skeleton className="h-3 w-12 rounded" />
        </div>
        
        {/* Title - 2 lines */}
        <Skeleton className="h-4 w-full rounded" />
        <Skeleton className="h-4 w-3/4 rounded" />
        
        {/* Optional probability bar */}
        <Skeleton className="h-2 w-32 rounded-full mt-1" />
      </div>
    </div>
  );
}

// Multiple skeletons for loading state
export function NewsListSkeleton({ count = 6 }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm overflow-hidden">
      {[...Array(count)].map((_, i) => (
        <NewsCardSkeleton key={i} />
      ))}
    </div>
  );
}

// Trending Widget Skeleton
export function TrendingWidgetSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm overflow-hidden">
      <div className="p-3 border-b border-gray-100 dark:border-gray-800">
        <Skeleton className="h-5 w-24 rounded" />
      </div>
      <div className="p-3">
        <Skeleton className="h-4 w-16 mb-3 rounded" />
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center justify-between py-2">
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-5 rounded-full" />
              <Skeleton className="h-4 w-24 rounded" />
            </div>
            <Skeleton className="h-4 w-12 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default Skeleton;
