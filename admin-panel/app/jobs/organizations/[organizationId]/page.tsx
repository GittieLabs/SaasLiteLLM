'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function RedirectToAnalytics() {
  const params = useParams();
  const router = useRouter();
  const organizationId = params.organizationId as string;

  useEffect(() => {
    // Redirect to the consolidated analytics page
    router.replace(`/organizations/${organizationId}/analytics`);
  }, [organizationId, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <p className="text-muted-foreground">Redirecting to analytics...</p>
      </div>
    </div>
  );
}
