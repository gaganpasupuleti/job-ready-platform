import { Navigate, Route, Routes } from 'react-router-dom'

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
import { InterviewsPage } from '@/pages/interviews/InterviewsPage'
import { PracticeHubPage } from '@/pages/practice/PracticeHubPage'
import { PracticePathPage } from '@/pages/practice/PracticePathPage'
import { ProjectsPage } from '@/pages/practice/ProjectsPage'
import { ProjectDetailPage } from '@/pages/practice/ProjectDetailPage'
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
      'ai',
      'ai/ml',
      'ai/genai',
      'ai/prompt-engineering',
      'ai/agents',
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
        <Route path="interviews" element={<InterviewsPage />} />
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
        <Route path="practice/sessions/:sessionId" element={<PracticeSessionPage />} />
        <Route path="practice/sessions/:sessionId/results" element={<PracticeResultsPage />} />

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

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
