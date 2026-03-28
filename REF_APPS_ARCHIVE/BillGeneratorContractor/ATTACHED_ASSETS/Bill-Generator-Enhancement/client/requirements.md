## Packages
framer-motion | Page transitions and sleek animated interactions
date-fns | Beautiful date formatting for the recent jobs list
clsx | Class name merging for UI components
tailwind-merge | Efficient Tailwind class conflict resolution

## Notes
Tailwind Config - extend fontFamily:
fontFamily: {
  sans: ["var(--font-sans)"],
  display: ["var(--font-display)"],
  mono: ["var(--font-mono)"],
}
API Assumption: /api/jobs/process expects multipart/form-data with 'image' and 'qtyFile' fields.
