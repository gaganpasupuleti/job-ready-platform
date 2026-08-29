/**
 * TEMP — development only. Never enabled in production builds.
 * Dev auto-login credentials (matches backend seed).
 */
export const DEV_AUTO_LOGIN =
  import.meta.env.DEV && import.meta.env.VITE_ENABLE_DEV_LOGIN !== 'false'
    ? ({
        email: 'admin@jobready.dev',
        password: 'Admin123!',
      } as const)
    : null
