import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@shared/routes";

// ============================================
// REST HOOKS
// ============================================

export function useJobs() {
  return useQuery({
    queryKey: [api.jobs.list.path],
    queryFn: async () => {
      const res = await fetch(api.jobs.list.path, { credentials: "include" });
      if (!res.ok) throw new Error('Failed to fetch jobs');
      return api.jobs.list.responses[200].parse(await res.json());
    },
  });
}

export function useJob(id: number | null) {
  return useQuery({
    queryKey: [api.jobs.get.path, id],
    queryFn: async () => {
      if (!id) return null;
      const url = api.jobs.get.path.replace(":id", id.toString());
      const res = await fetch(url, { credentials: "include" });
      if (res.status === 404) throw new Error('Job not found');
      if (!res.ok) throw new Error('Failed to fetch job details');
      return api.jobs.get.responses[200].parse(await res.json());
    },
    enabled: !!id,
  });
}

export function useProcessJob() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await fetch(api.jobs.process.path, {
        method: api.jobs.process.method,
        body: formData, // No Content-Type header; browser sets it automatically with the correct boundary
        credentials: "include",
      });

      if (!res.ok) {
        let errorMsg = "Failed to process job due to an unexpected error.";
        try {
          const errData = await res.json();
          if (errData.message) errorMsg = errData.message;
        } catch (e) {
          console.error("Could not parse error response", e);
        }
        throw new Error(errorMsg);
      }
      
      return api.jobs.process.responses[200].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.jobs.list.path] });
    },
  });
}
