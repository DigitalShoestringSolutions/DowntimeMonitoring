import { useMutation, useQuery, useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import APIBackend from './RestAPI'

class APIException extends Error {
    constructor(message, code = code, payload = undefined, name = "PayloadError") {
        super(message);
        this.name = name;
        this.payload = payload
        this.code = code
    }
}

function get_url(config) {
    return (config.api.host ? config.api.host : window.location.hostname) + (config.api.port ? ":" + config.api.port : "")
}

export function useConfig() {
    return useQuery(
        {
            queryKey: ['config'],
            queryFn: async () => APIBackend.api_get('http://' + document.location.host + '/config/config.json'),
            select: (data) => (data.payload)
        }
    )
}


export function useMachineList(config) {
    return useQuery(
        {
            queryKey: ['machine_list'],
            queryFn: async () => APIBackend.api_get('http://' + get_url(config) + '/machines'),
            select: (data) => (data.payload)
        }
    )
}

export function useMachineReasons(config, machine_id) {
    return useQuery(
        {
            queryKey: ['reasons', { id: machine_id }],
            queryFn: async () => APIBackend.api_get('http://' + get_url(config) + '/reasons/' + machine_id),
            select: (data) => (data.payload)
        }
    )
}

export function useMachineStatus(config, machine_id) {
    return useQuery(
        {
            queryKey: ['status', { id: machine_id }],
            queryFn: async () => APIBackend.api_get('http://' + get_url(config) + '/state/' + machine_id).then(({ payload }) => payload[0]),
        }
    )
}

export function useEventList(config, machine_id, page, page_length, from = undefined, to = undefined) {
    const searchParams = new URLSearchParams();

    searchParams.append("page-length", page_length)
    searchParams.append("page", page)
    if (from)
        searchParams.append("from", from)
    if (to)
        searchParams.append("to", to)
    return useQuery(
        {
            queryKey: ['events', { id: machine_id, from: from, to: to }, { page: page }],
            queryFn: async () => APIBackend.api_get('http://' + get_url(config) + '/events/by-state/' + machine_id + "?" + searchParams.toString()).then(({ payload }) => payload),
        }
    )
}

export function useMachineStoppages(config, machine_id, page, page_length, duration_filter) {
    const searchParams = new URLSearchParams();

    searchParams.append("page-length", page_length)
    searchParams.append("page", page)
    searchParams.append("running", false)
    if (duration_filter) {
        searchParams.append("duration", duration_filter)
    }

    return useQuery(
        {
            queryKey: ['stoppages', { id: machine_id, page: page, duration_filter: duration_filter }],
            queryFn: async () => APIBackend.api_get('http://' + get_url(config) + '/state/history/' + machine_id + "?" + searchParams.toString()).then(({ payload }) => payload),
        }
    )
}

export function useSetReason(config, machine_id) {
    return useMutation(
        {
            mutationFn: async ({ record_id, reason }) => {
                let url = "http://" + get_url(config) + "/state/set_reason/" + record_id
                return APIBackend.api_put(url, { reason: reason }).then(({ status, payload }) => {
                    if (status == 200)
                        return payload
                    else
                        throw new APIException("API ERROR", status, payload)
                })
            },
            onSuccess: (result, mutation_data) => {
                // if (result.status === 200)
                //     queryClient.invalidateQueries({ queryKey: ['order_list'] })
            }
        }
    )
}

export function useModifyEvent() {
    let { data: config } = useConfig()
    const queryClient = useQueryClient()
    return useMutation(
        {
            mutationFn: async ({ event_id, timestamp }) => {
                let url = "http://" + get_url(config) + "/events/update/" + event_id
                return APIBackend.api_put(url, { timestamp: timestamp }).then(({ status, payload }) => {
                    if (status == 200)
                        return payload
                    else
                        throw new APIException("API ERROR", status, payload)
                })
            },
            onSuccess: (result, mutation_data) => {
                queryClient.invalidateQueries({ queryKey: ['events'], refetchType: 'active' })
            }
        }
    )
}

export function useDeleteEvent() {
    let { data: config } = useConfig()
    const queryClient = useQueryClient()
    return useMutation(
        {
            mutationFn: async ({ event_id }) => {
                let url = "http://" + get_url(config) + "/events/delete/" + event_id
                return APIBackend.api_delete(url).then(({ status, payload }) => {
                    if (status == 200)
                        return payload
                    else
                        throw new APIException("API ERROR", status, payload)
                })
            },
            onSuccess: (result, mutation_data) => {
                queryClient.invalidateQueries({ queryKey: ['events'], refetchType: 'active' })
            }
        }
    )
}