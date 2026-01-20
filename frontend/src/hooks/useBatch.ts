import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { batchApi, BatchJobList, BatchJobWithFiles, BatchResultsSummary, BatchJobCreated } from '@/lib/api'

export function useBatchJobs(page = 1, pageSize = 20) {
  return useQuery<BatchJobList>({
    queryKey: ['batch', 'jobs', page, pageSize],
    queryFn: () => batchApi.list(page, pageSize),
    refetchInterval: 5000, // Poll every 5 seconds to check progress
  })
}

export function useBatchJob(jobId: string | undefined) {
  return useQuery<BatchJobWithFiles>({
    queryKey: ['batch', 'job', jobId],
    queryFn: () => batchApi.get(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Stop polling when job is complete
      const data = query.state.data
      if (data?.status === 'completed' || data?.status === 'failed' || data?.status === 'cancelled') {
        return false
      }
      return 2000 // Poll every 2 seconds while processing
    },
  })
}

export function useBatchResults(jobId: string | undefined) {
  return useQuery<BatchResultsSummary>({
    queryKey: ['batch', 'results', jobId],
    queryFn: () => batchApi.getResults(jobId!),
    enabled: !!jobId,
  })
}

export function useCreateBatch() {
  const queryClient = useQueryClient()

  return useMutation<BatchJobCreated, Error, { files: File[]; name?: string; clientId?: string }>({
    mutationFn: ({ files, name, clientId }) => batchApi.create(files, name, clientId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batch', 'jobs'] })
    },
  })
}

export function useCancelBatch() {
  const queryClient = useQueryClient()

  return useMutation<void, Error, string>({
    mutationFn: (jobId) => batchApi.cancel(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batch'] })
    },
  })
}

export function useDeleteBatch() {
  const queryClient = useQueryClient()

  return useMutation<void, Error, string>({
    mutationFn: (jobId) => batchApi.delete(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batch', 'jobs'] })
    },
  })
}
