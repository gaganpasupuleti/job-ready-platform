import { Route, Routes } from 'react-router-dom'

import { AdminRoute, GuestRoute, ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { PlaceholderPage } from '@/components/common/PlaceholderPage'
import { AppLayout } from '@/layouts/AppLayout'
import { AdminCodingProblemFormPage } from '@/pages/admin/AdminCodingProblemFormPage'
import { AdminCodingProblemsPage } from '@/pages/admin/AdminCodingProblemsPage'
import { AdminQuestionFormPage } from '@/pages/admin/AdminQuestionFormPage'
import { AdminQuestionsPage } from '@/pages/admin/AdminQuestionsPage'
import { AdminSqlProblemFormPage } from '@/pages/admin/AdminSqlProblemFormPage'
import { AdminSqlProblemsPage } from '@/pages/admin/AdminSqlProblemsPage'
import { AdminTaxonomyPage } from '@/pages/admin/AdminTaxonomyPage'
import { AdminContentBatchPage } from '@/pages/admin/AdminContentBatchPage'
import { AdminContentPage } from '@/pages/admin/AdminContentPage'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { AptitudePage } from '@/pages/practice/AptitudePage'
import { BookmarksPage } from '@/pages/bookmarks/BookmarksPage'
import { SubmissionDetailPage } from '@/pages/submissions/SubmissionDetailPage'
import { SubmissionsPage } from '@/pages/submissions/SubmissionsPage'
import { CodingPage } from '@/pages/practice/CodingPage'
import { DsaPage } from '@/pages/practice/DsaPage'
import { DsaProblemPage } from '@/pages/practice/DsaProblemPage'
import { McqPage } from '@/pages/practice/McqPage'
import { PracticeResultsPage } from '@/pages/practice/PracticeResultsPage'
import { PracticeSessionPage } from '@/pages/practice/PracticeSessionPage'
import { SqlPage } from '@/pages/practice/SqlPage'
import { SqlProblemPage } from '@/pages/practice/SqlProblemPage'
import { SqlSubmissionDetailPage } from '@/pages/sql/SqlSubmissionDetailPage'
import { SqlSubmissionsPage } from '@/pages/sql/SqlSubmissionsPage'
import { InterviewHubPage } from '@/pages/interviews/InterviewHubPage'
import { InterviewQuestionsPage } from '@/pages/interviews/InterviewQuestionsPage'
import { InterviewPacksPage } from '@/pages/interviews/InterviewPacksPage'
import { InterviewPackDetailPage } from '@/pages/interviews/InterviewPackDetailPage'
import { InterviewSessionNewPage } from '@/pages/interviews/InterviewSessionNewPage'
import { InterviewSessionPage } from '@/pages/interviews/InterviewSessionPage'
import { InterviewResultsPage } from '@/pages/interviews/InterviewResultsPage'
import { InterviewHistoryPage } from '@/pages/interviews/InterviewHistoryPage'
import { InterviewReviewPage } from '@/pages/interviews/InterviewReviewPage'
import { InterviewProgressPage } from '@/pages/interviews/InterviewProgressPage'
import { CompanyPrepPage } from '@/pages/interviews/CompanyPrepPage'
import { CompanyPrepDetailPage } from '@/pages/interviews/CompanyPrepDetailPage'
import { AdminInterviewPacksPage } from '@/pages/admin/AdminInterviewPacksPage'
import { AdminJobsPage } from '@/pages/admin/AdminJobsPage'
import { AdminReadinessPage } from '@/pages/admin/AdminReadinessPage'
import { JobsApplicationsPage } from '@/pages/jobs/JobsApplicationsPage'
import { JobApplicationDetailPage } from '@/pages/jobs/JobApplicationDetailPage'
import { JobDetailPage } from '@/pages/jobs/JobDetailPage'
import { JobsHubPage } from '@/pages/jobs/JobsHubPage'
import { JobsRecommendedPage } from '@/pages/jobs/JobsRecommendedPage'
import { JobsSavedPage } from '@/pages/jobs/JobsSavedPage'
import { ReadinessPage } from '@/pages/readiness/ReadinessPage'
import { ReadinessSkillsPage } from '@/pages/readiness/ReadinessSkillsPage'
import { MistakesPage } from '@/pages/mistakes/MistakesPage'
import { PracticeHubPage } from '@/pages/practice/PracticeHubPage'
import { PracticePathPage } from '@/pages/practice/PracticePathPage'
import { ProjectsPage } from '@/pages/practice/ProjectsPage'
import { ProjectDetailPage } from '@/pages/practice/ProjectDetailPage'
import { ProjectTaskPage } from '@/pages/practice/ProjectTaskPage'
import { CourseListPage } from '@/pages/learn/CourseListPage'
import { CourseDetailPage } from '@/pages/learn/CourseDetailPage'
import { LessonWorkspacePage } from '@/pages/learn/LessonWorkspacePage'
import { AdminPracticePathsPage } from '@/pages/admin/AdminPracticePathsPage'
import { AdminCoursesPage } from '@/pages/admin/AdminCoursesPage'
import { AdminProjectsPage } from '@/pages/admin/AdminProjectsPage'
import { AdminAiPage } from '@/pages/admin/AdminAiPage'
import { AdminPromptsPage } from '@/pages/admin/AdminPromptsPage'
import { AdminPromptFormPage } from '@/pages/admin/AdminPromptFormPage'
import { AiHomePage } from '@/pages/ai/AiHomePage'
import { AiTrackPage } from '@/pages/ai/AiTrackPage'
import { AiProgressPage } from '@/pages/ai/AiProgressPage'
import { PromptChallengeListPage } from '@/pages/ai/PromptChallengeListPage'
import { PromptChallengeWorkspacePage } from '@/pages/ai/PromptChallengeWorkspacePage'
import { PromptSubmissionsPage } from '@/pages/ai/PromptSubmissionsPage'
import { PromptSubmissionDetailPage } from '@/pages/ai/PromptSubmissionDetailPage'
import { InfraHomePage } from '@/pages/infra/InfraHomePage'
import { InfraProgressPage } from '@/pages/infra/InfraProgressPage'
import { InfraTrackPage } from '@/pages/infra/InfraTrackPage'
import { ScenarioWorkspacePage } from '@/pages/infra/ScenarioWorkspacePage'
import { AdminInfraPage } from '@/pages/admin/AdminInfraPage'
import { AdminScenariosPage } from '@/pages/admin/AdminScenariosPage'
import { AdminScenarioFormPage } from '@/pages/admin/AdminScenarioFormPage'
import { moduleRoutes } from '@/routes/moduleRoutes'

const placeholderRoutes = moduleRoutes.filter(
  (route) =>
    ![
      'practice/aptitude',
      'practice/mcq',
      'practice/dsa',
      'practice/coding',
      'practice/sql',
      'bookmarks',
      'interviews',
      'company-prep',
      'ai',
      'ai/genai',
      'ai/prompt-engineering',
      'ai/agents',
      'cloud',
      'devops',
      'cybersecurity',
      'jobs',
      'jobs/recommended',
      'jobs/saved',
      'jobs/applications',
    ].includes(route.path),
)

export function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <GuestRoute>
            <LoginPage />
          </GuestRoute>
        }
      />
      <Route
        path="/register"
        element={
          <GuestRoute>
            <RegisterPage />
          </GuestRoute>
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="practice" element={<PracticeHubPage />} />
        <Route path="practice/paths/:slug" element={<PracticePathPage />} />
        <Route path="practice/projects" element={<ProjectsPage />} />
        <Route path="practice/projects/:slug" element={<ProjectDetailPage />} />
        <Route path="projects/:slug/tasks/:taskId" element={<ProjectTaskPage />} />
        <Route path="projects/:slug" element={<ProjectDetailPage />} />
        <Route path="learn" element={<CourseListPage />} />
        <Route path="learn/courses/:slug" element={<CourseDetailPage />} />
        <Route
          path="learn/courses/:courseSlug/:moduleSlug/:lessonSlug"
          element={<LessonWorkspacePage />}
        />
        <Route path="practice/aptitude" element={<AptitudePage />} />
        <Route path="practice/mcq" element={<McqPage />} />
        <Route path="practice/dsa" element={<DsaPage />} />
        <Route path="practice/dsa/:problemId" element={<DsaProblemPage />} />
        <Route path="practice/coding" element={<CodingPage />} />
        <Route path="practice/sql" element={<SqlPage />} />
        <Route path="practice/sql/:slug" element={<SqlProblemPage />} />
        <Route path="submissions" element={<SubmissionsPage />} />
        <Route path="submissions/:submissionId" element={<SubmissionDetailPage />} />
        <Route path="sql/submissions" element={<SqlSubmissionsPage />} />
        <Route path="sql/submissions/:submissionId" element={<SqlSubmissionDetailPage />} />
        <Route path="bookmarks" element={<BookmarksPage />} />
        <Route path="interviews" element={<InterviewHubPage />} />
        <Route path="interviews/questions" element={<InterviewQuestionsPage />} />
        <Route path="interviews/packs" element={<InterviewPacksPage />} />
        <Route path="interviews/packs/:slug" element={<InterviewPackDetailPage />} />
        <Route path="interviews/session/new" element={<InterviewSessionNewPage />} />
        <Route path="interviews/sessions/:sessionId" element={<InterviewSessionPage />} />
        <Route path="interviews/sessions/:sessionId/results" element={<InterviewResultsPage />} />
        <Route path="interviews/history" element={<InterviewHistoryPage />} />
        <Route path="interviews/review" element={<InterviewReviewPage />} />
        <Route path="interviews/progress" element={<InterviewProgressPage />} />
        <Route path="company-prep" element={<CompanyPrepPage />} />
        <Route path="company-prep/:slug" element={<CompanyPrepDetailPage />} />
        <Route path="jobs" element={<JobsHubPage />} />
        <Route path="jobs/recommended" element={<JobsRecommendedPage />} />
        <Route path="jobs/saved" element={<JobsSavedPage />} />
        <Route path="jobs/applications" element={<JobsApplicationsPage />} />
        <Route path="jobs/applications/:applicationId" element={<JobApplicationDetailPage />} />
        <Route path="jobs/:jobId" element={<JobDetailPage />} />
        <Route path="ai" element={<AiHomePage />} />
        <Route path="ai/genai" element={<AiTrackPage track="genai" />} />
        <Route path="ai/rag" element={<AiTrackPage track="rag" />} />
        <Route path="ai/prompt-engineering" element={<AiTrackPage track="prompt-engineering" />} />
        <Route path="ai/prompt-engineering/challenges" element={<PromptChallengeListPage />} />
        <Route path="ai/prompt-engineering/challenges/:slug" element={<PromptChallengeWorkspacePage />} />
        <Route path="ai/prompt-engineering/submissions" element={<PromptSubmissionsPage />} />
        <Route path="ai/prompt-engineering/submissions/:id" element={<PromptSubmissionDetailPage />} />
        <Route path="ai/agents" element={<AiTrackPage track="agents" />} />
        <Route path="ai/mcp" element={<AiTrackPage track="mcp" />} />
        <Route path="ai/tool-calling" element={<AiTrackPage track="tool-calling" />} />
        <Route path="ai/evaluation" element={<AiTrackPage track="evaluation" />} />
        <Route path="ai/security" element={<AiTrackPage track="security" />} />
        <Route path="ai/system-design" element={<AiTrackPage track="system-design" />} />
        <Route path="ai/progress" element={<AiProgressPage />} />
        <Route path="cloud" element={<InfraHomePage domain="cloud" />} />
        <Route path="cloud/fundamentals" element={<InfraTrackPage track="cloud-fundamentals" />} />
        <Route path="cloud/aws" element={<InfraTrackPage track="cloud-aws" />} />
        <Route path="cloud/azure" element={<InfraTrackPage track="cloud-azure" />} />
        <Route path="cloud/gcp" element={<InfraTrackPage track="cloud-gcp" />} />
        <Route path="cloud/architecture" element={<InfraTrackPage track="cloud-architecture" />} />
        <Route path="cloud/security" element={<InfraTrackPage track="cloud-security" />} />
        <Route path="cloud/progress" element={<InfraProgressPage domain="cloud" />} />
        <Route path="devops" element={<InfraHomePage domain="devops" />} />
        <Route path="devops/linux" element={<InfraTrackPage track="devops-linux" />} />
        <Route path="devops/git" element={<InfraTrackPage track="devops-git" />} />
        <Route path="devops/docker" element={<InfraTrackPage track="devops-docker" />} />
        <Route path="devops/kubernetes" element={<InfraTrackPage track="devops-kubernetes" />} />
        <Route path="devops/cicd" element={<InfraTrackPage track="devops-cicd" />} />
        <Route path="devops/terraform" element={<InfraTrackPage track="devops-terraform" />} />
        <Route path="devops/observability" element={<InfraTrackPage track="devops-observability" />} />
        <Route path="devops/sre" element={<InfraTrackPage track="devops-sre" />} />
        <Route path="devops/progress" element={<InfraProgressPage domain="devops" />} />
        <Route path="cybersecurity" element={<InfraHomePage domain="cybersecurity" />} />
        <Route path="cybersecurity/fundamentals" element={<InfraTrackPage track="cyber-fundamentals" />} />
        <Route path="cybersecurity/network-security" element={<InfraTrackPage track="cyber-network" />} />
        <Route path="cybersecurity/iam" element={<InfraTrackPage track="cyber-iam" />} />
        <Route path="cybersecurity/web-security" element={<InfraTrackPage track="cyber-web" />} />
        <Route path="cybersecurity/owasp" element={<InfraTrackPage track="cyber-owasp" />} />
        <Route path="cybersecurity/api-security" element={<InfraTrackPage track="cyber-api" />} />
        <Route path="cybersecurity/cloud-security" element={<InfraTrackPage track="cyber-cloud" />} />
        <Route path="cybersecurity/soc" element={<InfraTrackPage track="cyber-soc" />} />
        <Route path="cybersecurity/siem" element={<InfraTrackPage track="cyber-siem" />} />
        <Route path="cybersecurity/incident-response" element={<InfraTrackPage track="cyber-ir" />} />
        <Route path="cybersecurity/secure-coding" element={<InfraTrackPage track="cyber-coding" />} />
        <Route path="cybersecurity/progress" element={<InfraProgressPage domain="cybersecurity" />} />
        <Route path="scenarios/:slug" element={<ScenarioWorkspacePage />} />
        <Route path="practice/sessions/:sessionId" element={<PracticeSessionPage />} />
        <Route path="practice/sessions/:sessionId/results" element={<PracticeResultsPage />} />

        <Route path="readiness" element={<ReadinessPage />} />
        <Route path="readiness/skills" element={<ReadinessSkillsPage />} />
        <Route path="mistakes" element={<MistakesPage />} />

        {placeholderRoutes.map((module) => (
          <Route
            key={module.path}
            path={module.path}
            element={
              <PlaceholderPage
                title={module.title}
                description={module.description}
                icon={module.icon}
              />
            }
          />
        ))}

        <Route
          path="admin/questions"
          element={
            <AdminRoute>
              <AdminQuestionsPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/questions/new"
          element={
            <AdminRoute>
              <AdminQuestionFormPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/questions/:questionId/edit"
          element={
            <AdminRoute>
              <AdminQuestionFormPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/taxonomy"
          element={
            <AdminRoute>
              <AdminTaxonomyPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/coding"
          element={
            <AdminRoute>
              <AdminCodingProblemsPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/coding/new"
          element={
            <AdminRoute>
              <AdminCodingProblemFormPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/coding/:problemId"
          element={
            <AdminRoute>
              <AdminCodingProblemFormPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/sql"
          element={
            <AdminRoute>
              <AdminSqlProblemsPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/sql/new"
          element={
            <AdminRoute>
              <AdminSqlProblemFormPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/sql/:problemId/edit"
          element={
            <AdminRoute>
              <AdminSqlProblemFormPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/content"
          element={
            <AdminRoute>
              <AdminContentPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/content/batches/:batchId"
          element={
            <AdminRoute>
              <AdminContentBatchPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/practice-paths"
          element={
            <AdminRoute>
              <AdminPracticePathsPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/courses"
          element={
            <AdminRoute>
              <AdminCoursesPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/projects"
          element={
            <AdminRoute>
              <AdminProjectsPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/projects/new"
          element={
            <AdminRoute>
              <AdminProjectsPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/projects/:id/edit"
          element={
            <AdminRoute>
              <AdminProjectsPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/ai"
          element={
            <AdminRoute>
              <AdminAiPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/ai/prompts"
          element={
            <AdminRoute>
              <AdminPromptsPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/ai/prompts/new"
          element={
            <AdminRoute>
              <AdminPromptFormPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/ai/prompts/:id/edit"
          element={
            <AdminRoute>
              <AdminPromptFormPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/ai/taxonomy"
          element={
            <AdminRoute>
              <AdminTaxonomyPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/cloud"
          element={
            <AdminRoute>
              <AdminInfraPage domain="cloud" />
            </AdminRoute>
          }
        />
        <Route
          path="admin/devops"
          element={
            <AdminRoute>
              <AdminInfraPage domain="devops" />
            </AdminRoute>
          }
        />
        <Route
          path="admin/cybersecurity"
          element={
            <AdminRoute>
              <AdminInfraPage domain="cybersecurity" />
            </AdminRoute>
          }
        />
        <Route
          path="admin/scenarios"
          element={
            <AdminRoute>
              <AdminScenariosPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/scenarios/new"
          element={
            <AdminRoute>
              <AdminScenarioFormPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/scenarios/:id/edit"
          element={
            <AdminRoute>
              <AdminScenarioFormPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/interviews"
          element={
            <AdminRoute>
              <AdminInterviewPacksPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/interviews/packs"
          element={
            <AdminRoute>
              <AdminInterviewPacksPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/jobs"
          element={
            <AdminRoute>
              <AdminJobsPage />
            </AdminRoute>
          }
        />
        <Route
          path="admin/readiness"
          element={
            <AdminRoute>
              <AdminReadinessPage />
            </AdminRoute>
          }
        />

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
