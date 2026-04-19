import { NextApiRequest, NextApiResponse } from 'next'
import { filterHeaderForAWSValues } from '@/utils/header'

/// This is the handler for the /api/item/[uuid] route.
/// Currently the backend doesn't support this route, this is an example of passing auth to the backend.
/// Adapt this handler to your needs.

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
): Promise<void> {
    const {
        query: { uuid },
        method,
        headers
    } = req
    switch (method) {
        case 'GET':
            try {
                const data = {
                    method: 'GET',
                    headers: {
                        ...filterHeaderForAWSValues(headers), // Filter out cookies not needed for backend requests
                    } as HeadersInit,
                }
                const response = await fetch(process.env.BACKEND_URL + '/api/item/' + uuid, data);
                if (!response.ok) {
                    console.error(await response.text())
                    console.error(await response.json())
                    throw new Error('Failed to read items by attribute');
                }
                res.status(200).send(await response.json())
            } catch (error) {
                let message
                console.log(error)
                if (error instanceof Error) message = error.message
                res.status(500).send({ error: message })
            }
            break
        default:
            res.setHeader('Allow', ['GET'])
            res.status(405).end(`Method ${method} Not Allowed`)
            break
    }
}
