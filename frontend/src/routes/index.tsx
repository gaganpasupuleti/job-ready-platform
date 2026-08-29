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

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
