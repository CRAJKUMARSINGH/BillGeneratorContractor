/**
 * Bill Service — abstraction layer over Supabase.
 * Replace supabase calls here with FastAPI fetch calls in Phase 7
 * without touching any component code.
 */
import { supabase } from './supabase';
import type { Bill, BillItem } from '../types/bill';

// ─── Bills ────────────────────────────────────────────────────────────────────
export async function fetchBills(): Promise<Bill[]> {
  const { data, error } = await supabase
    .from('bills')
    .select('*')
    .order('created_at', { ascending: false });
  if (error) throw new Error(error.message);
  return data ?? [];
}

export async function fetchBill(id: string): Promise<Bill> {
  const { data, error } = await supabase
    .from('bills')
    .select('*')
    .eq('id', id)
    .single();
  if (error) throw new Error(error.message);
  return data;
}

export async function fetchBillItems(billId: string): Promise<BillItem[]> {
  const { data, error } = await supabase
    .from('bill_items')
    .select('*')
    .eq('bill_id', billId)
    .order('sort_order');
  if (error) throw new Error(error.message);
  return data ?? [];
}

export async function upsertBill(
  bill: Partial<Bill>,
  items: BillItem[],
  userId: string
): Promise<Bill> {
  let billId = bill.id;

  if (billId) {
    const { error } = await supabase
      .from('bills')
      .update({ ...bill, updated_at: new Date().toISOString() })
      .eq('id', billId);
    if (error) throw new Error(error.message);
  } else {
    const { data, error } = await supabase
      .from('bills')
      .insert({ ...bill, user_id: userId })
      .select()
      .single();
    if (error) throw new Error(error.message);
    billId = data.id;
    bill = data;
  }

  // Replace all items (simple strategy; upgrade to diff-patch in Phase 7)
  await supabase.from('bill_items').delete().eq('bill_id', billId);

  if (items.length > 0) {
    const { error } = await supabase.from('bill_items').insert(
      items.map((item, i) => ({
        ...item,
        id: undefined,
        bill_id: billId,
        sort_order: i,
      }))
    );
    if (error) throw new Error(error.message);
  }

  return { ...bill, id: billId! } as Bill;
}

export async function deleteBill(id: string): Promise<void> {
  const { error } = await supabase.from('bills').delete().eq('id', id);
  if (error) throw new Error(error.message);
}

export async function updateBillStatus(
  id: string,
  status: Bill['status'],
  workflowStatus: Bill['workflow_status']
): Promise<void> {
  const { error } = await supabase
    .from('bills')
    .update({ status, workflow_status: workflowStatus, updated_at: new Date().toISOString() })
    .eq('id', id);
  if (error) throw new Error(error.message);
}
