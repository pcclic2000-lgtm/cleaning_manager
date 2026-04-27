# views/__init__.py
"""Package views — modules organisés par domaine métier.

Structure :
  views/employees/  → EmployeeView, EmployeeDialog, EmployeeArretDialog
  views/invoices/   → InvoicesView, InvoiceDialog, RapportWidget
  views/clients/    → ClientsView
  views/payroll/    → PayeGlobaleView, CotisationView, ModernPayslipView
  views/dashboard/  → DashboardView
  views/settings/   → SettingsView, CompanyInfoView
  views/shared/     → BankView, ExpensesView
"""
import logging

logger = logging.getLogger(__name__)
