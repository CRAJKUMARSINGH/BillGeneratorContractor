## Packages
react-dropzone | Beautiful drag and drop file uploads
framer-motion | Smooth transitions and animations for a premium feel
clsx | Utility for constructing className strings conditionally
tailwind-merge | Utility to merge tailwind classes safely

## Notes
- File upload uses `multipart/form-data` with a `file` field POSTed to `/api/bills/process`
- Wouter handles routing, using TanStack Query for state and cache
- Print functionality heavily relies on dynamic `@page` rules injected into the DOM based on the active view
