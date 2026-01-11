"""
OSAP Optimizer - Flask Backend
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

from calculator import (
    OSAPLoan,
    RAPCalculator,
    calculate_payoff,
    calculate_payment_scenarios,
    debt_vs_invest_comparison,
    optimize_multiple_debts,
    get_salary_info,
    CURRENT_PRIME_RATE,
    FEDERAL_RATE,
    PROVINCIAL_RATE,
    SALARY_BY_FIELD,
    ONTARIO_SALARY_DATA
)

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/rates')
def get_current_rates():
    return jsonify({
        'prime_rate': CURRENT_PRIME_RATE,
        'federal_rate': FEDERAL_RATE,
        'provincial_rate': PROVINCIAL_RATE,
    })


@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.get_json()

    loan_amount = float(data.get('loan_amount', 0))
    federal_portion = float(data.get('federal_portion', 60)) / 100
    graduation_date = data.get('graduation_date')
    income = float(data.get('monthly_income', 0))
    expenses = float(data.get('monthly_expenses', 0))
    field_of_study = data.get('field_of_study', 'other')
    has_emergency_fund = data.get('has_emergency_fund', False)
    family_size = int(data.get('family_size', 1))

    if not graduation_date:
        graduation_date = datetime.now().strftime('%Y-%m-%d')

    loan = OSAPLoan(
        total_amount=loan_amount,
        federal_portion=federal_portion,
        graduation_date=graduation_date
    )

    grace_info = loan.calculate_grace_period_interest()
    annual_income = income * 12
    rap_status = RAPCalculator.check_eligibility(annual_income, family_size)

    scenarios_result = calculate_payment_scenarios(
        loan,
        monthly_income=income,
        monthly_expenses=expenses,
        field_of_study=field_of_study,
        has_emergency_fund=has_emergency_fund
    )

    response = {
        'loan_details': {
            'total_amount': loan.total_amount,
            'federal_amount': round(loan.federal_amount, 2),
            'provincial_amount': round(loan.provincial_amount, 2),
            'federal_rate': round(loan.federal_rate * 100, 2),
            'provincial_rate': round(loan.provincial_rate * 100, 2),
        },
        'grace_period': {
            'months': 6,
            'interest_accrued': grace_info['total_interest_accrued'],
            'balance_after_grace': grace_info['total_balance_after_grace'],
        },
        'rap_status': rap_status,
        'scenarios': scenarios_result['scenarios'],
        'savings': scenarios_result['savings'],
    }

    return jsonify(response)


@app.route('/api/whatif', methods=['POST'])
def what_if():
    data = request.get_json()
    loan_amount = float(data.get('loan_amount', 0))
    federal_portion = float(data.get('federal_portion', 60)) / 100
    extra_payment = float(data.get('extra_payment', 0))
    base_payment = float(data.get('base_payment', 0))

    loan = OSAPLoan(total_amount=loan_amount, federal_portion=federal_portion)

    new_payment = base_payment + extra_payment
    result = calculate_payoff(loan, new_payment)
    baseline = calculate_payoff(loan, base_payment)

    if result.get('error') or baseline.get('error'):
        return jsonify({'error': 'Payment too low'})

    return jsonify({
        'new_payment': round(new_payment, 2),
        'months': result['months'],
        'total_interest': result['total_interest'],
        'interest_saved': round(baseline['total_interest'] - result['total_interest'], 2),
        'months_saved': baseline['months'] - result['months'],
        'breakdown': result['breakdown']
    })


@app.route('/api/multi-debt', methods=['POST'])
def optimize_debts():
    data = request.get_json()
    loan_amount = float(data.get('loan_amount', 0))
    federal_portion = float(data.get('federal_portion', 60)) / 100

    loan = OSAPLoan(total_amount=loan_amount, federal_portion=federal_portion)

    result = optimize_multiple_debts(
        osap_loan=loan,
        credit_card=float(data.get('credit_card_balance', 0)),
        line_of_credit=float(data.get('line_of_credit_balance', 0)),
        car_loan=float(data.get('car_loan_balance', 0)),
        monthly_budget=float(data.get('monthly_budget', 500))
    )
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)