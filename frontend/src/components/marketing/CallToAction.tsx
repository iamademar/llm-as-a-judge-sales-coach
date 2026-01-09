import Link from 'next/link';
import { Button } from '@/components/Button';
import { SectionContainer } from './ui/SectionContainer';

export function CallToAction() {
  return (
    <section className="py-24 bg-indigo-600 dark:bg-indigo-700">
      <SectionContainer>
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            Start Coaching With Data<br />
            Not Gut Feel
          </h2>

          <p className="text-lg sm:text-xl text-indigo-100 mb-10">
            Transform transcripts into measurable revenue skill improvement
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              variant="secondary"
              asChild
              className="text-base px-8 py-3 bg-white hover:bg-gray-50 text-indigo-600 border-0"
            >
              <Link href="/register">Create Your Workspace</Link>
            </Button>
            <Button
              variant="ghost"
              asChild
              className="text-base px-8 py-3 text-white hover:bg-indigo-500 dark:hover:bg-indigo-600 border-white/20"
            >
              <Link href="/login">Sign In</Link>
            </Button>
          </div>

          <p className="mt-8 text-sm text-indigo-200">
            Already have an account?{' '}
            <Link href="/login" className="underline hover:text-white">
              Sign in here
            </Link>
          </p>
        </div>
      </SectionContainer>
    </section>
  );
}
