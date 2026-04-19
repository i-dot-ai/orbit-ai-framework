import { NextRequest, NextResponse } from 'next/server'
import { type UserAuthorisationResult } from "@i-dot-ai-npm/utilities"
import { parseAuthToken } from './utils/auth';

// Define paths that should be public (no authorisation required)
const PUBLIC_PATHS = [
  '/unauthorised',
  '/generic-error',
]

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Check if the requested path is public
  if (PUBLIC_PATHS.some(path => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  try {
    let authResult: UserAuthorisationResult | null = null;

    if (process.env.ENVIRONMENT !== "local") {
      const token = req.headers.get("x-amzn-oidc-data"); // use "x-amzn-oidc-accesstoken" for keycloak

      if (!token) {
        console.error(`No auth token found in headers when accessing ${pathname}`);
        return redirectToUnauthorised(req);
      }

      authResult = await parseAuthToken(token);
    } else {
      authResult = {
        email: "test@i.ai.gov.uk",
        isAuthorised: true,
        authReason: "LOCAL_TESTING"
      }
    }

    if (authResult?.isAuthorised !== true) {
      console.error(`User is not authorised to access ${pathname}`);
      return redirectToUnauthorised(req);
    }

    console.info(
      `User ${authResult.email} authorisation result: ${authResult.isAuthorised}`
    );

    return NextResponse.next();
  } catch (error) {
    console.error("Error authorising token:", error)
    return redirectToGenericError(req)
  }
}

function redirectToUnauthorised(req: NextRequest) {
  const url = req.nextUrl.clone();
  url.pathname = "/unauthorised";
  return NextResponse.redirect(url);
}

function redirectToGenericError(req: NextRequest) {
  const url = req.nextUrl.clone();
  url.pathname = "/generic-error";
  return NextResponse.redirect(url);
}

// Configure which paths this middleware should run on
export const config = {
  matcher: [
    // Match all paths except those starting with excluded paths
    // You can customize this as needed
    "/((?!unauthorised|generic-error|_next/static|_next/image|favicon.ico|api/health).*)",
  ],
};
