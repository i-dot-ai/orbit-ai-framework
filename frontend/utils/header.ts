import { IncomingHttpHeaders } from "http";

/// Filter to limit headers to only amazon headers for auth

export function filterHeaderForAWSValues(headers: IncomingHttpHeaders) {
    return Object.fromEntries(
        Object.entries(headers).filter(([key, value]) => key.startsWith('x-amzn'))
    );
}
