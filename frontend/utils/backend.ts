export async function fetchBackendInfo(metadata: {
    headers: [string, string][] | Record<string, string> | Headers;
    method: string
}) {
    const res = await fetch(`${process.env.BACKEND_URL}/api/info`, metadata);
    if (!res.ok) {
        throw new Error('Failed to fetch data');
    }
    const data = await res.json();
    return data.backend
}