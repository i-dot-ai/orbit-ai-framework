import { NextApiRequest, NextApiResponse } from 'next'
import { fetchBackendInfo } from '@/utils/backend'
import {filterHeaderForAWSValues} from "@/utils/header";

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
): Promise<void> {
    const { method, headers } = req
    switch (method) {
        case 'GET':
            try {
                const metadata = {
                    method: 'GET',
                    headers: {
                        ...filterHeaderForAWSValues(headers), // Filter out cookies not needed for backend requests
                    } as HeadersInit,
                }
                console.log("Headers:", headers)
                const backend = await fetchBackendInfo(metadata)
                return res.status(200).send({ backend: backend })
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