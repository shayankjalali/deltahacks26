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

# =============================================================================
# ONTARIO SALARY DATA (2025) - Sources: Job Bank Canada, PayScale, Glassdoor
# =============================================================================

ONTARIO_SALARY_DATA = {
    'computer_science': {
        'title': 'Software Developer / IT Professional',
        'entry_salary': 60000,
        'median_salary': 85000,
        'high_salary': 120000,
        'monthly_entry': 5000,
        'outlook': 'excellent',
        'outlook_description': 'Strong demand across Ontario tech sector',
        'top_cities': ['Toronto', 'Ottawa', 'Waterloo', 'Kitchener'],
        'growth_5yr': 0.35,
        'sample_jobs': ['Software Developer', 'Data Analyst', 'IT Consultant', 'Web Developer']
    },
    'engineering': {
        'title': 'Engineer',
        'entry_salary': 65000,
        'median_salary': 85000,
        'high_salary': 130000,
        'monthly_entry': 5400,
        'outlook': 'very_good',
        'outlook_description': 'Solid prospects across multiple industries',
        'top_cities': ['Toronto', 'Hamilton', 'Ottawa', 'Windsor'],
        'growth_5yr': 0.30,
        'sample_jobs': ['Mechanical Engineer', 'Civil Engineer', 'Electrical Engineer', 'Chemical Engineer']
    },
    'business': {
        'title': 'Business / Finance Professional',
        'entry_salary': 50000,
        'median_salary': 70000,
        'high_salary': 110000,
        'monthly_entry': 4200,
        'outlook': 'good',
        'outlook_description': 'Competitive market, networking is key',
        'top_cities': ['Toronto', 'Ottawa', 'Mississauga', 'Markham'],
        'growth_5yr': 0.25,
        'sample_jobs': ['Financial Analyst', 'Marketing Coordinator', 'Accountant', 'Business Analyst']
    },
    'nursing': {
        'title': 'Registered Nurse / Healthcare',
        'entry_salary': 70000,
        'median_salary': 85000,
        'high_salary': 100000,
        'monthly_entry': 5800,
        'outlook': 'excellent',
        'outlook_description': 'High demand, stable employment across Ontario',
        'top_cities': ['Toronto', 'Ottawa', 'London', 'Hamilton'],
        'growth_5yr': 0.20,
        'sample_jobs': ['Registered Nurse', 'Nurse Practitioner', 'Healthcare Administrator']
    },
    'science': {
        'title': 'Science Professional',
        'entry_salary': 45000,
        'median_salary': 60000,
        'high_salary': 90000,
        'monthly_entry': 3750,
        'outlook': 'moderate',
        'outlook_description': 'Often requires graduate studies for advancement',
        'top_cities': ['Toronto', 'Ottawa', 'Hamilton', 'Kingston'],
        'growth_5yr': 0.20,
        'sample_jobs': ['Research Assistant', 'Lab Technician', 'Environmental Scientist', 'Biologist']
    },
    'arts': {
        'title': 'Arts / Humanities Professional',
        'entry_salary': 38000,
        'median_salary': 50000,
        'high_salary': 75000,
        'monthly_entry': 3200,
        'outlook': 'challenging',
        'outlook_description': 'Diverse career paths, entrepreneurship common',
        'top_cities': ['Toronto', 'Ottawa', 'Hamilton'],
        'growth_5yr': 0.15,
        'sample_jobs': ['Content Writer', 'Graphic Designer', 'Social Media Manager', 'Teacher']
    },
    'education': {
        'title': 'Teacher / Educator',
        'entry_salary': 55000,
        'median_salary': 75000,
        'high_salary': 95000,
        'monthly_entry': 4600,
        'outlook': 'good',
        'outlook_description': 'Stable with good benefits, regional variation',
        'top_cities': ['Toronto', 'Ottawa', 'London', 'Windsor'],
        'growth_5yr': 0.20,
        'sample_jobs': ['Elementary Teacher', 'High School Teacher', 'Educational Assistant', 'Professor']
    },
    'trades': {
        'title': 'Skilled Trades Professional',
        'entry_salary': 50000,
        'median_salary': 70000,
        'high_salary': 100000,
        'monthly_entry': 4200,
        'outlook': 'excellent',
        'outlook_description': 'High demand, apprenticeship pathway',
        'top_cities': ['Toronto', 'Hamilton', 'London', 'Windsor'],
        'growth_5yr': 0.30,
        'sample_jobs': ['Electrician', 'Plumber', 'HVAC Technician', 'Welder']
    },
    'other': {
        'title': 'General',
        'entry_salary': 45000,
        'median_salary': 55000,
        'high_salary': 80000,
        'monthly_entry': 3750,
        'outlook': 'varies',
        'outlook_description': 'Depends on specific field and experience',
        'top_cities': ['Toronto', 'Ottawa'],
        'growth_5yr': 0.20,
        'sample_jobs': ['Various entry-level positions']
    }
}

# Legacy format for backward compatibility
SALARY_BY_FIELD = {k: v['entry_salary'] for k, v in ONTARIO_SALARY_DATA.items()}

SALARY_GROWTH_CURVE = {
    0: 1.0,
    1: 1.05,
    2: 1.12,
    3: 1.20,
    5: 1.35,
    10: 1.70,
}

OUTLOOK_MULTIPLIERS = {
    'excellent': 1.15,
    'very_good': 1.10,
    'good': 1.05,
    'moderate': 1.0,
    'challenging': 0.95,
    'varies': 1.0
}


def get_salary_info(field_of_study: str) -> Dict:
    """Get comprehensive salary information for a field of study."""
    return ONTARIO_SALARY_DATA.get(field_of_study, ONTARIO_SALARY_DATA['other'])


def get_payment_recommendation(field_of_study: str, disposable_income: float) -> Dict:
    """
    Get field-specific payment recommendations based on job outlook.
    Better outlook = can be more aggressive with payments.
    """
    info = get_salary_info(field_of_study)
    outlook = info['outlook']
    
    # Recommended % of disposable income for debt repayment
    outlook_percentages = {
        'excellent': 0.35,      # High job security, can be aggressive
        'very_good': 0.30,
        'good': 0.25,
        'moderate': 0.20,
        'challenging': 0.15,   # Keep more cushion
        'varies': 0.20
    }
    
    recommended_percent = outlook_percentages.get(outlook, 0.20)
    recommended_payment = disposable_income * recommended_percent
    
    return {
        'recommended_percent': recommended_percent,
        'recommended_payment': round(recommended_payment, 2),
        'reasoning': f"Based on {outlook} job outlook in {info['title']}"
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
    
class RAPCalculator:
    @staticmethod
    def check_eligibility(gross_annual_income: float, family_size: int = 1) -> Dict:
        family_size = min(family_size, 5)
        thresholds = RAP_THRESHOLDS[family_size]

        if gross_annual_income <= thresholds['stage2']:
            return {
                'eligible': True,
                'stage': 2,
                'monthly_payment': 0,
                'title': 'Full RAP Eligibility',
                'description': 'You qualify for $0 payments. Government covers all interest.',
                'government_covers': 'Interest + potential principal reduction',
                'how_to_apply': 'Apply through NSLSC every 6 months',
                'threshold_used': thresholds['stage2'],
                'next_threshold': thresholds['stage1']
            }
        elif gross_annual_income <= thresholds['stage1']:
            excess_income = gross_annual_income - thresholds['stage2']
            affordable_payment = (excess_income * 0.20) / 12
            return {
                'eligible': True,
                'stage': 1,
                'monthly_payment': round(affordable_payment, 2),
                'title': 'Partial RAP Eligibility',
                'description': f'Reduced payment of ${affordable_payment:.2f}/month. Government covers remaining interest.',
                'government_covers': 'Interest above your affordable payment',
                'how_to_apply': 'Apply through NSLSC every 6 months',
                'threshold_used': thresholds['stage1'],
                'income_to_lose_eligibility': thresholds['stage1']
            }
        else:
            return {
                'eligible': False,
                'stage': 0,
                'monthly_payment': None,
                'title': 'Not Currently Eligible',
                'description': f'Income too high for RAP (threshold: ${thresholds["stage1"]:,}/year for family of {family_size})',
                'suggestion': 'You may qualify if income decreases or family size increases',
                'threshold_needed': thresholds['stage1']
            }

    @staticmethod
    def calculate_rap_vs_standard(loan: OSAPLoan, current_income: float, years_on_rap: int = 5, family_size: int = 1) -> Dict:
        rap_status = RAPCalculator.check_eligibility(current_income, family_size)
        results = {'rap_eligible': rap_status['eligible'], 'rap_stage': rap_status['stage'], 'analysis': {}}
        if rap_status['eligible']:
            rap_payment = rap_status['monthly_payment']
            total_user_pays_rap = rap_payment * 12 * years_on_rap
            annual_federal_interest = loan.federal_amount * loan.federal_rate
            total_gov_covers = annual_federal_interest * years_on_rap
            remaining_balance = loan.total_amount
            results['analysis'] = {
                'years_analyzed': years_on_rap,
                'your_total_payments': round(total_user_pays_rap, 2),
                'government_covers': round(total_gov_covers, 2),
                'remaining_balance': round(remaining_balance, 2),
                'strategy_note': 'RAP can be smart if you expect income to rise significantly.'
            }
        return results
    
    def calculate_payoff(loan: OSAPLoan, monthly_payment: float, include_grace_period: bool = True, extra_annual_payment: float = 0) -> Dict:
        if include_grace_period:
            grace = loan.calculate_grace_period_interest()
            federal_balance = grace['federal_balance_after_grace']
            provincial_balance = grace['provincial_balance']
            grace_interest = grace['total_interest_accrued']
        else:
            federal_balance = loan.federal_amount
            provincial_balance = loan.provincial_amount
            grace_interest = 0

        monthly_federal_interest = federal_balance * (loan.federal_rate / 12)
        monthly_provincial_interest = provincial_balance * (loan.provincial_rate / 12)
        min_payment = monthly_federal_interest + monthly_provincial_interest + 1

        if monthly_payment < min_payment:
            return {
                'error': True,
                'message': f'Payment of ${monthly_payment:.2f} is too low. Minimum ${min_payment:.2f} needed.',
                'minimum_payment': round(min_payment, 2)
            }
        
        months = 0
        total_interest = grace_interest
        federal_interest_paid = 0
        provincial_interest_paid = 0
        breakdown = []

        while (federal_balance > 0.01 or provincial_balance > 0.01) and months < 600:
            months += 1
            fed_interest = federal_balance * (loan.federal_rate / 12) if federal_balance > 0 else 0
            prov_interest = provincial_balance * (loan.provincial_rate / 12) if provincial_balance > 0 else 0
            total_interest += fed_interest + prov_interest
            federal_interest_paid += fed_interest
            provincial_interest_paid += prov_interest

            total_remaining = federal_balance + provincial_balance
            payment_this_month = monthly_payment
            if extra_annual_payment > 0 and months % 12 == 0:
                payment_this_month += extra_annual_payment

            if total_remaining > 0:
                fed_share = federal_balance / total_remaining
                prov_share = provincial_balance / total_remaining
                fed_payment = payment_this_month * fed_share
                prov_payment = payment_this_month * prov_share
                fed_principal = max(0, fed_payment - fed_interest)
                prov_principal = max(0, prov_payment - prov_interest)
                federal_balance = max(0, federal_balance - fed_principal)
                provincial_balance = max(0, provincial_balance - prov_principal)

            breakdown.append({
                'month': months,
                'federal_balance': round(federal_balance, 2),
                'provincial_balance': round(provincial_balance, 2),
                'total_balance': round(federal_balance + provincial_balance, 2),
                'interest_paid': round(fed_interest + prov_interest, 2),
                'principal_paid': round(payment_this_month - fed_interest - prov_interest, 2)
            })

        payoff_date = loan.repayment_start + relativedelta(months=months)

        return {
            'error': False,
            'months': months,
            'years': months // 12,
            'remaining_months': months % 12,
            'total_interest': round(total_interest, 2),
            'federal_interest': round(federal_interest_paid, 2),
            'provincial_interest': round(provincial_interest_paid, 2),
            'grace_period_interest': round(grace_interest, 2),
            'total_paid': round(loan.total_amount + total_interest, 2),
            'payoff_date': payoff_date.strftime('%B %Y'),
            'breakdown': breakdown
        }
