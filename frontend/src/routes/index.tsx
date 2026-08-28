import { Navigate, Route, Routes } from 'react-router-dom'

import { AdminRoute, GuestRoute, ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { PlaceholderPage } from '@/components/common/PlaceholderPage'
import { AppLayout } from '@/layouts/AppLayout'
import { AdminQuestionFormPage } from '@/pages/admin/AdminQuestionFormPage'
import { AdminQuestionsPage } from '@/pages/admin/AdminQuestionsPage'
import { AdminTaxonomyPage } from '@/pages/admin/AdminTaxonomyPage'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { AptitudePage } from '@/pages/practice/AptitudePage'
import { McqPage } from '@/pages/practice/McqPage'
import { PracticeResultsPage } from '@/pages/practice/PracticeResultsPage'
import { PracticeSessionPage } from '@/pages/practice/PracticeSessionPage'
import { moduleRoutes } from '@/routes/moduleRoutes'

const placeholderRoutes = moduleRoutes.filter(
  (route) => !['practice/aptitude', 'practice/mcq'].includes(route.path),
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
          path="admin/taxonomy"
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
