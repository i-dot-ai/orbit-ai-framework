export async function fetchAPIInfo() {
    const res = await fetch(`/api/info`);
    if (!res.ok) {
        throw new Error('Failed to fetch data');
    }
    const data = await res.json();
    return data.backend
}