import { HeroSection } from './HeroSection';
import { ProblemStatement } from './ProblemStatement';
import { SolutionOverview } from './SolutionOverview';
import { FeaturesGrid } from './FeaturesGrid';
import { WhoItsFor } from './WhoItsFor';
import { HowItWorks } from './HowItWorks';
import { ComparisonTable } from './ComparisonTable';
import { TechnicalFeatures } from './TechnicalFeatures';
import { CallToAction } from './CallToAction';

export function HomePage() {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <ProblemStatement />
      <SolutionOverview />
      <FeaturesGrid />
      <WhoItsFor />
      <HowItWorks />
      <ComparisonTable />
      <TechnicalFeatures />
      <CallToAction />
    </div>
  );
}
