-- Add workflow_status and source columns to bills table
-- Safe to run multiple times (IF NOT EXISTS guards)

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'bills' AND column_name = 'workflow_status'
  ) THEN
    ALTER TABLE bills ADD COLUMN workflow_status text DEFAULT 'input_edited';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'bills' AND column_name = 'source'
  ) THEN
    ALTER TABLE bills ADD COLUMN source text DEFAULT 'manual';
  END IF;
END $$;
