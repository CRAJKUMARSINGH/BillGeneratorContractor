/*
  # Create Bills Schema for Contractor Bill Generator

  1. New Tables
    - `bills`
      - `id` (uuid, primary key) - Unique bill identifier
      - `user_id` (uuid) - Reference to authenticated user
      - `voucher_number` (text) - Cash book voucher number
      - `bill_date` (date) - Date of bill
      - `contractor_name` (text) - Name of contractor/supplier
      - `work_name` (text) - Description of work
      - `serial_number` (text) - Serial number of current bill
      - `previous_bill_number` (text) - Previous bill reference
      - `previous_bill_date` (date) - Date of previous bill
      - `work_order_reference` (text) - Work order/agreement reference
      - `agreement_number` (text) - Agreement number
      - `commencement_date` (date) - Work commencement date
      - `scheduled_start_date` (date) - Scheduled start date
      - `scheduled_completion_date` (date) - Scheduled completion date
      - `actual_completion_date` (date) - Actual completion date
      - `measurement_date` (date) - Measurement date
      - `tender_premium_percentage` (numeric) - Tender premium percentage
      - `last_bill_deduction` (numeric) - Amount deducted from last bill
      - `status` (text) - Bill status (draft, preview, finalized)
      - `created_at` (timestamptz) - Creation timestamp
      - `updated_at` (timestamptz) - Last update timestamp

    - `bill_items`
      - `id` (uuid, primary key) - Unique item identifier
      - `bill_id` (uuid, foreign key) - Reference to bills table
      - `serial_no` (text) - Item serial number
      - `description` (text) - Work/supply details
      - `unit` (text) - Measurement unit
      - `qty_since_last_bill` (numeric) - Incremental quantity
      - `qty_to_date` (numeric) - Cumulative quantity
      - `rate` (numeric) - Unit price
      - `amount_to_date` (numeric) - Cumulative cost
      - `amount_since_previous` (numeric) - Incremental cost
      - `remarks` (text) - Additional notes
      - `sort_order` (integer) - Display order
      - `created_at` (timestamptz) - Creation timestamp
      - `updated_at` (timestamptz) - Last update timestamp

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users to manage their own bills
*/

CREATE TABLE IF NOT EXISTS bills (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  voucher_number text DEFAULT '',
  bill_date date DEFAULT CURRENT_DATE,
  contractor_name text DEFAULT '',
  work_name text DEFAULT '',
  serial_number text DEFAULT '',
  previous_bill_number text DEFAULT '',
  previous_bill_date date,
  work_order_reference text DEFAULT '',
  agreement_number text DEFAULT '',
  commencement_date date,
  scheduled_start_date date,
  scheduled_completion_date date,
  actual_completion_date date,
  measurement_date date,
  tender_premium_percentage numeric DEFAULT 0,
  last_bill_deduction numeric DEFAULT 0,
  status text DEFAULT 'draft',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bill_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  bill_id uuid REFERENCES bills(id) ON DELETE CASCADE NOT NULL,
  serial_no text DEFAULT '',
  description text DEFAULT '',
  unit text DEFAULT '',
  qty_since_last_bill numeric DEFAULT 0,
  qty_to_date numeric DEFAULT 0,
  rate numeric DEFAULT 0,
  amount_to_date numeric DEFAULT 0,
  amount_since_previous numeric DEFAULT 0,
  remarks text DEFAULT '',
  sort_order integer DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own bills"
  ON bills FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own bills"
  ON bills FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own bills"
  ON bills FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own bills"
  ON bills FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view items of own bills"
  ON bill_items FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM bills
      WHERE bills.id = bill_items.bill_id
      AND bills.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert items to own bills"
  ON bill_items FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM bills
      WHERE bills.id = bill_items.bill_id
      AND bills.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update items of own bills"
  ON bill_items FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM bills
      WHERE bills.id = bill_items.bill_id
      AND bills.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM bills
      WHERE bills.id = bill_items.bill_id
      AND bills.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete items from own bills"
  ON bill_items FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM bills
      WHERE bills.id = bill_items.bill_id
      AND bills.user_id = auth.uid()
    )
  );

CREATE INDEX IF NOT EXISTS idx_bills_user_id ON bills(user_id);
CREATE INDEX IF NOT EXISTS idx_bill_items_bill_id ON bill_items(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_items_sort_order ON bill_items(bill_id, sort_order);