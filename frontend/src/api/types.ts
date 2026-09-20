// Monetary values always arrive as decimal strings from the API (RB-001:
// never float), so amounts here are `string` and only parsed to Number at
// the last moment for display/formatting.

export interface Profile {
  id: number
  name: string
  base_currency: string
  timezone: string
}

export interface Currency {
  code: string
  name: string
  symbol: string
  decimal_places: number
  is_active: boolean
}

export interface ExchangeRate {
  id: number
  base_code: string
  quote_code: string
  rate_date: string
  rate: string
  source: string
}

export interface Account {
  id: number
  name: string
  account_type: string
  currency: string
  initial_balance: string
  initial_balance_date: string
  is_active: boolean
}

export interface AccountWithBalance extends Account {
  balance: string
  balance_in_base_currency: string | null
  base_currency: string
}

export interface Category {
  id: number
  name: string
  category_type: 'INCOME' | 'EXPENSE'
  parent_id: number | null
  is_active: boolean
}

export interface Transaction {
  id: number
  account_id: number
  category_id: number | null
  transaction_type: 'INCOME' | 'EXPENSE'
  status: 'PLANNED' | 'PENDING' | 'CLEARED' | 'CANCELLED'
  description: string
  currency: string
  planned_amount: string | null
  actual_amount: string | null
  planned_date: string | null
  actual_date: string | null
  source_type: string
  source_reference: string | null
  recurring_rule_id: number | null
  notes: string | null
  tags: string[]
}

export interface Transfer {
  id: number
  source_account_id: number
  destination_account_id: number
  amount: string
  source_currency: string
  destination_amount: string
  destination_currency: string
  exchange_rate: string
  transfer_date: string
  description: string | null
}

export interface RecurringRule {
  id: number
  account_id: number
  category_id: number | null
  transaction_type: 'INCOME' | 'EXPENSE'
  description: string
  amount: string
  frequency: string
  start_date: string
  end_date: string | null
  next_occurrence: string
  is_active: boolean
}

export interface UpcomingOccurrence {
  rule_id: number
  occurrence_date: string
  description: string
  amount: string
  transaction_type: 'INCOME' | 'EXPENSE'
}

export interface BudgetLine {
  id: number
  category_id: number
  planned_amount: string
  notes: string | null
}

export interface Budget {
  id: number
  name: string
  period_start: string
  period_end: string
  status: string
  lines: BudgetLine[]
}

export interface BudgetLineProgress {
  category_id: number
  planned_amount: string
  actual_spent: string
  remaining: string
  used_pct: string
  variance: string
  variance_pct: string | null
}

export interface BudgetProgress {
  budget: Budget
  lines: BudgetLineProgress[]
}

export interface CurrencyBreakdown {
  currency: string
  income: string
  expenses: string
}

export interface DashboardResponse {
  reference_month: string
  base_currency: string
  accounts: AccountWithBalance[]
  total_balance_base_currency: string
  balance_by_account_currency: Record<string, string>
  planned_income: string
  planned_expenses: string
  planned_savings: string
  actual_income: string
  actual_expenses: string
  actual_savings: string
  savings_rate: string | null
  actual_by_currency: CurrencyBreakdown[]
  planned_by_currency: CurrencyBreakdown[]
}

export interface ForecastMonthlyItem {
  reference_month: string
  projected_income: string
  projected_expenses: string
  projected_savings: string
  projected_end_balance: string
}

export interface ForecastRun {
  id: number
  run_at: string
  horizon_end: string
  scenario_name: string | null
  currency: string
  starting_balance: string
  projected_ending_balance: string
  monthly_items: ForecastMonthlyItem[]
}

export interface SavingsCapacity {
  average_3m: string | null
  average_6m: string | null
  average_12m: string | null
  median_6m: string | null
  trend: string
  recommended: string
  currency: string
}

export interface PlannedVsActualLine {
  category_id: number | null
  category_name: string
  planned: string
  actual: string
  variance: string
  variance_pct: string | null
}

export interface PlannedVsActualResponse {
  reference_month: string
  base_currency: string
  lines: PlannedVsActualLine[]
}

export interface MonthlyClosing {
  id: number
  reference_month: string
  currency: string
  status: 'OPEN' | 'CLOSED' | 'REOPENED'
  planned_income: string
  actual_income: string
  planned_expenses: string
  actual_expenses: string
  planned_savings: string
  actual_savings: string
  reconciliation_coverage_pct: string
  closed_at: string | null
  reopen_reason: string | null
  snapshot_json: Record<string, unknown>
}
