# Auth Fix Summary

## What Was Broken

- The frontend treated `/auth/refresh` like a refresh-token endpoint, but the backend only accepted the current bearer access token.
- When an API call got `401`, the frontend called `refreshToken()`.
- `refreshToken()` itself used the same generic request wrapper.
- If `/auth/refresh` returned `401`, the wrapper tried to refresh again, causing the repeated `401` loop in the console.
- The app also only stored one token in localStorage, so there was no real silent re-auth flow once the access token expired.

## What I Fixed

- Added a real refresh-token flow in the backend.
- Login and Google auth now return both `access_token` and `refresh_token`.
- `/auth/refresh` now accepts a real `refresh_token` in the request body.
- Access tokens and refresh tokens are validated separately.
- The frontend now stores `miryn_token` and `miryn_refresh_token` separately.
- The frontend refresh logic no longer calls itself recursively.
- Protected app pages now check auth before rendering and redirect cleanly to `/login` when the session is gone.

## Result

- No more infinite `401` refresh loop.
- Expired access tokens can be renewed correctly.
- Signup/login still writes users to the database and returns valid tokens.
