"""
OSAP Optimizer - Ontario Student Assistance Program Calculator
Comprehensive engine for Ontario university/college students with OSAP debt.
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional
import math


# =============================================================================
# OSAP CONSTANTS (Ontario, 2024-2025)
# =============================================================================

CURRENT_PRIME_RATE = 0.0725  # Bank of Canada prime rate as of late 2024
FEDERAL_RATE = CURRENT_PRIME_RATE  # Federal = Prime + 0%
PROVINCIAL_RATE = 0.0  # Ontario = 0% on provincial portion

DEFAULT_FEDERAL_PORTION = 0.6  # ~60% of OSAP is federal, ~40% provincial
GRACE_PERIOD_MONTHS = 6  # Non-repayment period after graduation
FORGIVENESS_YEARS = 15  # Potential forgiveness after 15 years of RAP

# RAP (Repayment Assistance Program) - Ontario thresholds 2024
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
            'explanation': f'During your 6-month grace period, ${round(accrued_interest, 2)} in interest will accrue on your federal portion. Your provincial portion (${self.provincial_amount:,.2f}) stays at 0% interest.'
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


def calculate_payment_scenarios(
    loan: OSAPLoan,
    monthly_income: float,
    monthly_expenses: float,
    field_of_study: str = 'other',
    years_experience: int = 0,
    has_emergency_fund: bool = False,
    other_debts: Dict = None
) -> Dict:
    disposable = monthly_income - monthly_expenses
    annual_income = monthly_income * 12
    rap = RAPCalculator.check_eligibility(annual_income)
    
    # Get field-specific salary info
    salary_info = get_salary_info(field_of_study)
    field_recommendation = get_payment_recommendation(field_of_study, disposable)

    # FIXED: Always calculate distinct payment amounts
    minimum = max(loan.total_amount / 120, 100)
    
    # Recommended: use field-specific recommendation or fallback
    recommended = max(
        field_recommendation['recommended_payment'] if disposable > 0 else 0,
        minimum * 1.5,
        minimum + 50
    )
    
    # Aggressive: at least 50% more than recommended
    aggressive = max(
        disposable * 0.50 if disposable > 0 else 0,
        recommended * 1.5,
        recommended + 100
    )
    
    minimum = round(minimum, 2)
    recommended = round(recommended, 2)
    aggressive = round(aggressive, 2)

    # Advisory notes (don't change payment amounts)
    if not has_emergency_fund:
        emergency_note = "Consider building a 3-month emergency fund alongside debt payments"
    elif other_debts and other_debts.get('credit_card', 0) > 0:
        emergency_note = "Consider paying off credit card first (higher interest)"
    else:
        emergency_note = None

    scenarios = {}
    for name, payment in [('minimum', minimum), ('recommended', recommended), ('aggressive', aggressive)]:
        result = calculate_payoff(loan, payment)
        if result.get('error'):
            scenarios[name] = result
        else:
            scenarios[name] = {
                'monthly_payment': round(payment, 2),
                'months': result['months'],
                'years': result['years'],
                'remaining_months': result['remaining_months'],
                'total_interest': result['total_interest'],
                'total_paid': result['total_paid'],
                'payoff_date': result['payoff_date'],
                'breakdown': result['breakdown'],
                'grace_period_interest': result['grace_period_interest']
            }

    savings = {}
    if not scenarios['minimum'].get('error') and not scenarios['recommended'].get('error'):
        savings['rec_vs_min_interest'] = round(scenarios['minimum']['total_interest'] - scenarios['recommended']['total_interest'], 2)
        savings['rec_vs_min_months'] = scenarios['minimum']['months'] - scenarios['recommended']['months']
    if not scenarios['minimum'].get('error') and not scenarios['aggressive'].get('error'):
        savings['agg_vs_min_interest'] = round(scenarios['minimum']['total_interest'] - scenarios['aggressive']['total_interest'], 2)
        savings['agg_vs_min_months'] = scenarios['minimum']['months'] - scenarios['aggressive']['months']

    # Enhanced income projection with salary data
    growth = SALARY_GROWTH_CURVE.get(min(years_experience, 10), 1.0)
    projected_salary = salary_info['entry_salary'] * growth
    salary_in_5_years = salary_info['entry_salary'] * (1 + salary_info['growth_5yr'])

    return {
        'scenarios': scenarios,
        'savings': savings,
        'rap_status': rap,
        'disposable_income': round(disposable, 2),
        'emergency_fund_note': emergency_note,
        'field_recommendation': field_recommendation,
        'salary_info': {
            'field': field_of_study,
            'title': salary_info['title'],
            'entry_salary': salary_info['entry_salary'],
            'median_salary': salary_info['median_salary'],
            'high_salary': salary_info['high_salary'],
            'monthly_entry': salary_info['monthly_entry'],
            'outlook': salary_info['outlook'],
            'outlook_description': salary_info['outlook_description'],
            'top_cities': salary_info['top_cities'],
            'sample_jobs': salary_info['sample_jobs'],
            'projected_current': round(projected_salary, 2),
            'projected_5_years': round(salary_in_5_years, 2)
        },
        'income_projection': {
            'field': field_of_study,
            'current_estimated': round(projected_salary, 2),
            'in_5_years': round(salary_in_5_years, 2)
        },
        'loan_details': {
            'total': loan.total_amount,
            'federal': loan.federal_amount,
            'provincial': loan.provincial_amount,
            'federal_rate': f"{loan.federal_rate * 100:.2f}%",
            'provincial_rate': f"{loan.provincial_rate * 100:.2f}%",
            'blended_rate': f"{loan.blended_rate * 100:.2f}%"
        }
    }


def debt_vs_invest_comparison(loan: OSAPLoan, monthly_payment: float, minimum_payment: float, investment_return: float = 0.07, years: int = 10) -> Dict:
    extra_per_month = monthly_payment - minimum_payment
    if extra_per_month <= 0:
        return {'error': 'Aggressive payment must be higher than minimum'}

    aggressive_result = calculate_payoff(loan, monthly_payment)
    minimum_result = calculate_payoff(loan, minimum_payment)

    monthly_return = investment_return / 12
    investment_balance = 0
    investment_months = min(years * 12, minimum_result['months'])

    for month in range(investment_months):
        investment_balance = (investment_balance + extra_per_month) * (1 + monthly_return)

    if aggressive_result['months'] < investment_months:
        remaining_months = investment_months - aggressive_result['months']
        investment_balance_aggressive = 0
        for month in range(remaining_months):
            investment_balance_aggressive = (investment_balance_aggressive + monthly_payment) * (1 + monthly_return)
    else:
        investment_balance_aggressive = 0

    return {
        'aggressive_payoff': {
            'months_to_payoff': aggressive_result['months'],
            'total_interest_paid': aggressive_result['total_interest'],
            'investment_value_after': round(investment_balance_aggressive, 2)
        },
        'minimum_and_invest': {
            'months_to_payoff': minimum_result['months'],
            'total_interest_paid': minimum_result['total_interest'],
            'investment_value': round(investment_balance, 2),
            'extra_interest_cost': round(minimum_result['total_interest'] - aggressive_result['total_interest'], 2)
        },
        'comparison': {
            'years_analyzed': years,
            'assumed_return': f"{investment_return * 100:.1f}%",
            'monthly_invested': round(extra_per_month, 2),
            'winner': 'invest' if investment_balance > (minimum_result['total_interest'] - aggressive_result['total_interest']) else 'pay_debt',
            'explanation': 'If investment returns exceed your loan interest rate, investing wins mathematically. But paying off debt is guaranteed.'
        }
    }


def optimize_multiple_debts(osap_loan: OSAPLoan, credit_card: float = 0, credit_card_rate: float = 0.1999, line_of_credit: float = 0, loc_rate: float = 0.08, car_loan: float = 0, car_rate: float = 0.07, monthly_budget: float = 500) -> Dict:
    debts = []
    if credit_card > 0:
        debts.append({'name': 'Credit Card', 'balance': credit_card, 'rate': credit_card_rate, 'min_payment': max(credit_card * 0.03, 25)})
    if line_of_credit > 0:
        debts.append({'name': 'Line of Credit', 'balance': line_of_credit, 'rate': loc_rate, 'min_payment': line_of_credit * (loc_rate / 12) + 50})
    if car_loan > 0:
        debts.append({'name': 'Car Loan', 'balance': car_loan, 'rate': car_rate, 'min_payment': car_loan / 60})
    if osap_loan.total_amount > 0:
        debts.append({'name': 'OSAP', 'balance': osap_loan.total_amount, 'rate': osap_loan.blended_rate, 'min_payment': max(osap_loan.total_amount / 120, 100)})

    if not debts:
        return {'error': 'No debts provided'}

    debts_avalanche = sorted(debts, key=lambda x: x['rate'], reverse=True)
    total_minimums = sum(d['min_payment'] for d in debts)
    
    if monthly_budget < total_minimums:
        return {'error': f'Budget ${monthly_budget:.2f} is less than minimum payments ${total_minimums:.2f}', 'minimum_needed': round(total_minimums, 2)}

    extra = monthly_budget - total_minimums

    return {
        'recommended_order': [d['name'] for d in debts_avalanche],
        'debts': debts_avalanche,
        'total_debt': round(sum(d['balance'] for d in debts), 2),
        'monthly_budget': monthly_budget,
        'total_minimums': round(total_minimums, 2),
        'extra_to_highest_rate': round(extra, 2),
        'strategy': f"Pay minimums on everything, put extra ${extra:.2f}/month toward {debts_avalanche[0]['name']} ({debts_avalanche[0]['rate']*100:.1f}% rate)",
        'explanation': 'Avalanche method minimizes total interest. Pay highest-rate debt first.'
    }


def calculate_simple_payoff(principal, annual_rate, monthly_payment):
    monthly_rate = annual_rate / 12
    months = 0
    total_interest = 0
    breakdown = []
    balance = principal

    if monthly_rate > 0 and monthly_payment <= principal * monthly_rate:
        return {'error': 'Payment too low', 'minimum_required': round(principal * monthly_rate + 1, 2)}

    while balance > 0.01 and months < 600:
        interest = balance * monthly_rate
        principal_paid = min(monthly_payment - interest, balance)
        balance -= principal_paid
        total_interest += interest
        months += 1
        breakdown.append({'month': months, 'balance': round(max(balance, 0), 2), 'interest': round(interest, 2), 'principal': round(principal_paid, 2)})

    return {'months': months, 'total_interest': round(total_interest, 2), 'total_paid': round(principal + total_interest, 2), 'breakdown': breakdown}


def calculate_payments(loan_amount, income, expenses):
    disposable = income - expenses
    minimum = max(loan_amount / 120, 100)
    recommended = max(disposable * 0.20, minimum * 1.5, minimum + 50)
    aggressive = max(disposable * 0.40, recommended * 1.5, recommended + 100)
    return {'minimum': round(minimum, 2), 'recommended': round(recommended, 2), 'aggressive': round(aggressive, 2), 'disposable_income': round(disposable, 2)}


if __name__ == "__main__":
    print("Testing payment scenarios with salary data...")
    loan = OSAPLoan(total_amount=30000, federal_portion=0.6, graduation_date='2025-04-30')
    scenarios = calculate_payment_scenarios(
        loan, 
        monthly_income=4000, 
        monthly_expenses=2500, 
        field_of_study='computer_science',
        has_emergency_fund=False
    )
    print(f"\nField: {scenarios['salary_info']['title']}")
    print(f"Entry Salary: ${scenarios['salary_info']['entry_salary']:,}")
    print(f"Job Outlook: {scenarios['salary_info']['outlook']}")
    print(f"Top Cities: {', '.join(scenarios['salary_info']['top_cities'])}")
    print(f"\nMinimum: ${scenarios['scenarios']['minimum']['monthly_payment']}/month")
    print(f"Recommended: ${scenarios['scenarios']['recommended']['monthly_payment']}/month")
    print(f"Aggressive: ${scenarios['scenarios']['aggressive']['monthly_payment']}/month")
    print("\nDone!")