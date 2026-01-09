export const siteConfig = {
  name: "SPIN AI Coaching",
  url: "https://salescoach.ai",
  description:
    "AI-powered SPIN selling assessments, coaching feedback, and LangSmith benchmarking for revenue teams.",
  baseLinks: {
    home: "/",
    overview: "/overview",
    representatives: "/representatives",
    settings: {
      general: "/settings/general",
      integrations: "/settings/integrations",
      promptTemplates: "/settings/prompt-templates",
      evaluations: "/settings/evaluations",
    },
  },
}

export type siteConfig = typeof siteConfig
