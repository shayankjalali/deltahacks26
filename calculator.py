"""
OSAP Optimizer - Ontario Student Assistance Program Calculator
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional
import math


# =============================================================================
# OSAP CONSTANTS (Ontario, 2024-2025)
# =============================================================================

CURRENT_PRIME_RATE = 0.0725
FEDERAL_RATE = CURRENT_PRIME_RATE
PROVINCIAL_RATE = 0.0

DEFAULT_FEDERAL_PORTION = 0.6
GRACE_PERIOD_MONTHS = 6
FORGIVENESS_YEARS = 15

RAP_THRESHOLDS = {
    1: {'stage1': 40000, 'stage2': 25000},
    2: {'stage1': 50000, 'stage2': 31250},
    3: {'stage1': 60000, 'stage2': 37500},
    4: {'stage1': 70000, 'stage2': 43750},
    5: {'stage1': 80000, 'stage2': 50000},
}


class OSAPLoan:
    def __init__(
        self,
        total_amount: float,
        federal_portion: float = DEFAULT_FEDERAL_PORTION,
        graduation_date: str = None,
        in_school: bool = False
    ):
        self.total_amount = total_amount
        self.federal_portion = federal_portion
        self.provincial_portion = 1 - federal_portion
        self.federal_amount = total_amount * federal_portion
        self.provincial_amount = total_amount * self.provincial_portion
        self.federal_rate = FEDERAL_RATE
        self.provincial_rate = PROVINCIAL_RATE
        self.blended_rate = (self.federal_amount * self.federal_rate +
                           self.provincial_amount * self.provincial_rate) / total_amount if total_amount > 0 else 0

        if graduation_date:
            self.graduation_date = datetime.strptime(graduation_date, '%Y-%m-%d')
        else:
            self.graduation_date = datetime.now()

        self.in_school = in_school
        self.grace_period_end = self.graduation_date + relativedelta(months=GRACE_PERIOD_MONTHS)
        self.repayment_start = self.grace_period_end

    def calculate_grace_period_interest(self) -> Dict:
        monthly_rate = self.federal_rate / 12
        accrued_interest = 0
        balance = self.federal_amount
        monthly_breakdown = []

        for month in range(GRACE_PERIOD_MONTHS):
            interest = balance * monthly_rate
            accrued_interest += interest
            balance += interest

            monthly_breakdown.append({
                'month': month + 1,
                'interest_accrued': round(interest, 2),
                'federal_balance': round(balance, 2)
            })

        return {
            'total_interest_accrued': round(accrued_interest, 2),
            'federal_balance_after_grace': round(balance, 2),
            'provincial_balance': round(self.provincial_amount, 2),
            'total_balance_after_grace': round(balance + self.provincial_amount, 2),
            'monthly_breakdown': monthly_breakdown,
            'explanation': f'During your 6-month grace period, ${round(accrued_interest, 2)} in interest will accrue on your federal portion.'
        }