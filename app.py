"""
OSAP Optimizer - Flask Backend
Comprehensive API for Ontario student loan optimization.
Now with MongoDB Atlas for saving plans and community comparisons!
"""

from flask import Flask, render_template, request, jsonify, Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import uuid

from calculator import (
    OSAPLoan,
    RAPCalculator,
    calculate_payoff,
    calculate_payment_scenarios,
    debt_vs_invest_comparison,
    optimize_multiple_debts,
    calculate_simple_payoff,
    calculate_payments,
    get_salary_info,
    CURRENT_PRIME_RATE,
    FEDERAL_RATE,
    PROVINCIAL_RATE,
    SALARY_BY_FIELD,
    ONTARIO_SALARY_DATA
)

app = Flask(__name__)


# =============================================================================
# MONGODB ATLAS CONNECTION
# =============================================================================

from pymongo import MongoClient

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://shayanjalali_db_user:LkzYWJ7EfOLhnxEA@cluster0.xu10cxz.mongodb.net/?appName=Cluster0')

# Initialize MongoDB client
try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client['osap_optimizer']
    plans_collection = db['saved_plans']
    stats_collection = db['community_stats']
    print("✅ Connected to MongoDB Atlas!")
except Exception as e:
    print(f"⚠️ MongoDB connection failed: {e}")
    mongo_client = None
    db = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/rates')
def get_current_rates():
    return jsonify({
        'prime_rate': CURRENT_PRIME_RATE,
        'federal_rate': FEDERAL_RATE,
        'provincial_rate': PROVINCIAL_RATE,
        'federal_rate_percent': f"{FEDERAL_RATE * 100:.2f}%",
        'provincial_rate_percent': f"{PROVINCIAL_RATE * 100:.2f}%",
        'last_updated': '2024-12',
        'note': 'Federal = Prime + 0%. Ontario provincial = 0%.'
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

    credit_card = float(data.get('credit_card_balance', 0))
    line_of_credit = float(data.get('line_of_credit_balance', 0))
    car_loan = float(data.get('car_loan_balance', 0))

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

    other_debts = {
        'credit_card': credit_card,
        'line_of_credit': line_of_credit,
        'car_loan': car_loan
    }

    scenarios_result = calculate_payment_scenarios(
        loan,
        monthly_income=income,
        monthly_expenses=expenses,
        field_of_study=field_of_study,
        has_emergency_fund=has_emergency_fund,
        other_debts=other_debts
    )

    response = {
        'loan_details': {
            'total_amount': loan.total_amount,
            'federal_amount': round(loan.federal_amount, 2),
            'provincial_amount': round(loan.provincial_amount, 2),
            'federal_rate': round(loan.federal_rate * 100, 2),
            'provincial_rate': round(loan.provincial_rate * 100, 2),
            'blended_rate': round(loan.blended_rate * 100, 2),
            'repayment_start': loan.repayment_start.strftime('%B %Y')
        },
        'grace_period': {
            'months': 6,
            'interest_accrued': grace_info['total_interest_accrued'],
            'balance_after_grace': grace_info['total_balance_after_grace'],
            'explanation': grace_info['explanation']
        },
        'rap_status': rap_status,
        'payments': {
            'minimum': scenarios_result['scenarios']['minimum']['monthly_payment'],
            'recommended': scenarios_result['scenarios']['recommended']['monthly_payment'],
            'aggressive': scenarios_result['scenarios']['aggressive']['monthly_payment'],
            'disposable_income': scenarios_result['disposable_income']
        },
        'scenarios': scenarios_result['scenarios'],
        'savings': scenarios_result['savings'],
        'income_projection': scenarios_result.get('income_projection'),
        'salary_info': scenarios_result.get('salary_info'),
        'field_recommendation': scenarios_result.get('field_recommendation'),
        'emergency_fund_note': scenarios_result.get('emergency_fund_note')
    }

    # Save anonymous stats to MongoDB for community comparisons
    if db is not None and loan_amount > 0:
        try:
            stats_collection.insert_one({
                'loan_amount': loan_amount,
                'field_of_study': field_of_study,
                'monthly_income': income,
                'federal_portion': federal_portion * 100,
                'timestamp': datetime.now(),
                'province': 'Ontario'
            })
        except Exception as e:
            print(f"Failed to save stats: {e}")

    return jsonify(response)


@app.route('/api/rap-check', methods=['POST'])
def check_rap():
    data = request.get_json()
    annual_income = float(data.get('annual_income', 0))
    family_size = int(data.get('family_size', 1))
    result = RAPCalculator.check_eligibility(annual_income, family_size)
    return jsonify(result)


@app.route('/api/grace-period', methods=['POST'])
def calculate_grace():
    data = request.get_json()
    loan_amount = float(data.get('loan_amount', 0))
    federal_portion = float(data.get('federal_portion', 60)) / 100
    graduation_date = data.get('graduation_date', datetime.now().strftime('%Y-%m-%d'))

    loan = OSAPLoan(
        total_amount=loan_amount,
        federal_portion=federal_portion,
        graduation_date=graduation_date
    )

    result = loan.calculate_grace_period_interest()
    result['repayment_start_date'] = loan.repayment_start.strftime('%B %d, %Y')
    return jsonify(result)


@app.route('/api/debt-vs-invest', methods=['POST'])
def compare_strategies():
    data = request.get_json()
    loan_amount = float(data.get('loan_amount', 0))
    federal_portion = float(data.get('federal_portion', 60)) / 100
    graduation_date = data.get('graduation_date', datetime.now().strftime('%Y-%m-%d'))
    aggressive_payment = float(data.get('aggressive_payment', 500))
    minimum_payment = float(data.get('minimum_payment', 250))
    investment_return = float(data.get('investment_return', 7)) / 100
    years = int(data.get('years', 10))

    loan = OSAPLoan(
        total_amount=loan_amount,
        federal_portion=federal_portion,
        graduation_date=graduation_date
    )

    result = debt_vs_invest_comparison(
        loan,
        monthly_payment=aggressive_payment,
        minimum_payment=minimum_payment,
        investment_return=investment_return,
        years=years
    )
    return jsonify(result)


@app.route('/api/multi-debt', methods=['POST'])
def optimize_debts():
    data = request.get_json()
    loan_amount = float(data.get('loan_amount', 0))
    federal_portion = float(data.get('federal_portion', 60)) / 100
    graduation_date = data.get('graduation_date', datetime.now().strftime('%Y-%m-%d'))

    credit_card = float(data.get('credit_card_balance', 0))
    credit_card_rate = float(data.get('credit_card_rate', 19.99)) / 100
    line_of_credit = float(data.get('line_of_credit_balance', 0))
    loc_rate = float(data.get('line_of_credit_rate', 8)) / 100
    car_loan = float(data.get('car_loan_balance', 0))
    car_rate = float(data.get('car_loan_rate', 7)) / 100
    monthly_budget = float(data.get('monthly_budget', 500))

    loan = OSAPLoan(
        total_amount=loan_amount,
        federal_portion=federal_portion,
        graduation_date=graduation_date
    )

    result = optimize_multiple_debts(
        osap_loan=loan,
        credit_card=credit_card,
        credit_card_rate=credit_card_rate,
        line_of_credit=line_of_credit,
        loc_rate=loc_rate,
        car_loan=car_loan,
        car_rate=car_rate,
        monthly_budget=monthly_budget
    )
    return jsonify(result)


@app.route('/api/whatif', methods=['POST'])
def what_if():
    data = request.get_json()
    loan_amount = float(data.get('loan_amount', 0))
    federal_portion = float(data.get('federal_portion', 60)) / 100
    extra_payment = float(data.get('extra_payment', 0))
    base_payment = float(data.get('base_payment', 0))

    loan = OSAPLoan(
        total_amount=loan_amount,
        federal_portion=federal_portion
    )

    new_payment = base_payment + extra_payment
    result = calculate_payoff(loan, new_payment)
    baseline = calculate_payoff(loan, base_payment)

    if result.get('error') or baseline.get('error'):
        return jsonify({'error': 'Payment too low'})

    return jsonify({
        'new_payment': round(new_payment, 2),
        'months': result['months'],
        'years': result['years'],
        'remaining_months': result['remaining_months'],
        'total_interest': result['total_interest'],
        'payoff_date': result['payoff_date'],
        'interest_saved': round(baseline['total_interest'] - result['total_interest'], 2),
        'months_saved': baseline['months'] - result['months'],
        'breakdown': result['breakdown']
    })


@app.route('/api/salary-data')
def get_salary_data():
    """Return average starting salaries by field (legacy format)."""
    return jsonify(SALARY_BY_FIELD)


@app.route('/api/salary-info')
def get_all_salary_info():
    """Return comprehensive Ontario salary data for all fields."""
    return jsonify(ONTARIO_SALARY_DATA)


@app.route('/api/salary-info/<field>')
def get_field_salary_info(field):
    """Return detailed salary information for a specific field."""
    salary_info = get_salary_info(field)
    
    return jsonify({
        'field': field,
        'data': salary_info,
        'source': 'Job Bank Canada, PayScale, Glassdoor (2025)',
        'region': 'Ontario, Canada'
    })


@app.route('/api/calculate-simple', methods=['POST'])
def calculate_simple():
    data = request.get_json()
    loan_amount = float(data.get('loan_amount', 0))
    federal_rate = float(data.get('federal_rate', 6.5)) / 100
    income = float(data.get('monthly_income', 0))
    expenses = float(data.get('monthly_expenses', 0))

    payments = calculate_payments(loan_amount, income, expenses)

    scenarios = {}
    for name, payment in [('minimum', payments['minimum']),
                          ('recommended', payments['recommended']),
                          ('aggressive', payments['aggressive'])]:
        result = calculate_simple_payoff(loan_amount, federal_rate, payment)

        if 'error' in result:
            scenarios[name] = result
        else:
            payoff_date = datetime.now() + relativedelta(months=result['months'])
            scenarios[name] = {
                'monthly_payment': payment,
                'months': result['months'],
                'years': result['months'] // 12,
                'remaining_months': result['months'] % 12,
                'total_interest': result['total_interest'],
                'total_paid': result['total_paid'],
                'payoff_date': payoff_date.strftime('%B %Y'),
                'breakdown': result['breakdown']
            }

    savings = {}
    if 'months' in scenarios['minimum'] and 'months' in scenarios['recommended']:
        savings['rec_vs_min_interest'] = round(
            scenarios['minimum']['total_interest'] - scenarios['recommended']['total_interest'], 2
        )
        savings['rec_vs_min_months'] = scenarios['minimum']['months'] - scenarios['recommended']['months']

    if 'months' in scenarios['minimum'] and 'months' in scenarios['aggressive']:
        savings['agg_vs_min_interest'] = round(
            scenarios['minimum']['total_interest'] - scenarios['aggressive']['total_interest'], 2
        )
        savings['agg_vs_min_months'] = scenarios['minimum']['months'] - scenarios['aggressive']['months']

    return jsonify({
        'payments': payments,
        'scenarios': scenarios,
        'savings': savings
    })


# =============================================================================
# MONGODB - SAVE & LOAD PLANS
# =============================================================================

@app.route('/api/plans/save', methods=['POST'])
def save_plan():
    """Save a user's loan scenario to MongoDB."""
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    
    data = request.get_json()
    plan_name = data.get('plan_name', 'My Plan')
    
    # Generate a unique plan ID
    plan_id = str(uuid.uuid4())[:8]
    
    plan = {
        'plan_id': plan_id,
        'plan_name': plan_name,
        'created_at': datetime.now(),
        'form_data': {
            'loan_amount': data.get('loan_amount', 0),
            'federal_portion': data.get('federal_portion', 60),
            'graduation_date': data.get('graduation_date', ''),
            'monthly_income': data.get('monthly_income', 0),
            'monthly_expenses': data.get('monthly_expenses', 0),
            'field_of_study': data.get('field_of_study', 'other'),
            'family_size': data.get('family_size', 1),
            'has_emergency_fund': data.get('has_emergency_fund', False),
            'credit_card_balance': data.get('credit_card_balance', 0),
            'line_of_credit_balance': data.get('line_of_credit_balance', 0),
            'car_loan_balance': data.get('car_loan_balance', 0)
        },
        'results': data.get('results', {})
    }
    
    try:
        plans_collection.insert_one(plan)
        return jsonify({
            'success': True,
            'plan_id': plan_id,
            'message': f'Plan "{plan_name}" saved! Your code: {plan_id}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/plans/load/<plan_id>', methods=['GET'])
def load_plan(plan_id):
    """Load a saved plan by ID."""
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        plan = plans_collection.find_one({'plan_id': plan_id})
        if plan:
            # Remove MongoDB's _id field (not JSON serializable)
            plan.pop('_id', None)
            plan['created_at'] = plan['created_at'].isoformat()
            return jsonify({'success': True, 'plan': plan})
        else:
            return jsonify({'error': 'Plan not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/plans/list', methods=['GET'])
def list_recent_plans():
    """List recent saved plans (for demo purposes)."""
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        plans = list(plans_collection.find().sort('created_at', -1).limit(10))
        for plan in plans:
            plan.pop('_id', None)
            plan['created_at'] = plan['created_at'].isoformat()
        return jsonify({'success': True, 'plans': plans})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# MONGODB - COMMUNITY STATS & COMPARISONS
# =============================================================================

@app.route('/api/community/stats', methods=['GET'])
def get_community_stats():
    """Get anonymous aggregate statistics from all users."""
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Get total number of calculations
        total_users = stats_collection.count_documents({})
        
        if total_users == 0:
            return jsonify({
                'success': True,
                'total_calculations': 0,
                'message': 'No data yet - be the first!'
            })
        
        # Calculate aggregate stats using MongoDB aggregation
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'avg_loan': {'$avg': '$loan_amount'},
                    'max_loan': {'$max': '$loan_amount'},
                    'min_loan': {'$min': '$loan_amount'},
                    'avg_income': {'$avg': '$monthly_income'},
                    'total': {'$sum': 1}
                }
            }
        ]
        
        result = list(stats_collection.aggregate(pipeline))
        
        if result:
            stats = result[0]
            
            # Get field of study distribution
            field_pipeline = [
                {'$group': {'_id': '$field_of_study', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 5}
            ]
            field_distribution = list(stats_collection.aggregate(field_pipeline))
            
            return jsonify({
                'success': True,
                'total_calculations': stats['total'],
                'average_loan': round(stats['avg_loan'], 2),
                'highest_loan': round(stats['max_loan'], 2),
                'lowest_loan': round(stats['min_loan'], 2),
                'average_income': round(stats['avg_income'], 2),
                'top_fields': [{'field': f['_id'], 'count': f['count']} for f in field_distribution]
            })
        
        return jsonify({'success': True, 'total_calculations': 0})
        
    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/community/compare', methods=['POST'])
def compare_to_community():
    """Compare a user's loan to community averages."""
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    
    data = request.get_json()
    user_loan = float(data.get('loan_amount', 0))
    user_field = data.get('field_of_study', 'other')
    
    try:
        # Get stats for same field of study
        field_pipeline = [
            {'$match': {'field_of_study': user_field}},
            {
                '$group': {
                    '_id': None,
                    'avg_loan': {'$avg': '$loan_amount'},
                    'count': {'$sum': 1}
                }
            }
        ]
        
        field_result = list(stats_collection.aggregate(field_pipeline))
        
        # Get overall stats
        overall_pipeline = [
            {
                '$group': {
                    '_id': None,
                    'avg_loan': {'$avg': '$loan_amount'},
                    'count': {'$sum': 1}
                }
            }
        ]
        
        overall_result = list(stats_collection.aggregate(overall_pipeline))
        
        response = {
            'success': True,
            'your_loan': user_loan,
            'field_of_study': user_field
        }
        
        if field_result and field_result[0]['count'] > 0:
            field_avg = field_result[0]['avg_loan']
            response['field_average'] = round(field_avg, 2)
            response['field_count'] = field_result[0]['count']
            response['vs_field'] = 'above' if user_loan > field_avg else 'below'
            response['field_difference'] = round(abs(user_loan - field_avg), 2)
            response['field_percent'] = round((user_loan / field_avg - 1) * 100, 1)
        
        if overall_result and overall_result[0]['count'] > 0:
            overall_avg = overall_result[0]['avg_loan']
            response['overall_average'] = round(overall_avg, 2)
            response['total_students'] = overall_result[0]['count']
            response['vs_overall'] = 'above' if user_loan > overall_avg else 'below'
            response['overall_difference'] = round(abs(user_loan - overall_avg), 2)
            response['overall_percent'] = round((user_loan / overall_avg - 1) * 100, 1)
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# GEMINI AI CHAT ENDPOINT
# =============================================================================

import google.generativeai as genai

# Configure Gemini API (set your API key as environment variable)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyASkGzUdphHCu-R5J0lefMGCB9qQWTPyaE')


@app.route('/api/chat', methods=['POST'])
def chat_with_owl():
    """
    AI-powered chat with Professor Hootsworth using Google Gemini API.
    The owl provides personalized OSAP debt advice in character.
    """
    data = request.get_json()
    user_message = data.get('message', '')
    
    # Get user's financial context if available
    loan_amount = data.get('loan_amount', 0)
    monthly_income = data.get('monthly_income', 0)
    monthly_expenses = data.get('monthly_expenses', 0)
    field_of_study = data.get('field_of_study', 'other')
    
    # Build context for the AI
    financial_context = ""
    if loan_amount > 0:
        salary_info = get_salary_info(field_of_study)
        financial_context = f"""
The student's financial situation:
- OSAP Loan: ${loan_amount:,.2f}
- Monthly Income: ${monthly_income:,.2f}
- Monthly Expenses: ${monthly_expenses:,.2f}
- Field of Study: {salary_info['title']}
- Expected Entry Salary: ${salary_info['entry_salary']:,}/year
- Job Outlook: {salary_info['outlook']} - {salary_info['outlook_description']}
"""

    system_prompt = f"""You are Professor Hootsworth, a wise owl NPC in a Stardew Valley-style game called OSAP Optimizer. 
You help Ontario university/college students understand and manage their OSAP (Ontario Student Assistance Program) debt.

Your personality:
- Wise, warm, and encouraging
- Use owl-themed expressions like "Hoo hoo!", "By my feathers!", "Wise choice!"
- Keep responses concise (2-4 sentences max)
- Give practical, actionable advice about student debt
- Reference Ontario-specific programs like RAP (Repayment Assistance Plan) when relevant
- Be encouraging but realistic about debt repayment

IMPORTANT - Always include specific numbers in your advice:
- Calculate yearly costs (e.g., "$75/month = $900/year")
- Show impact on debt (e.g., "That's 2 extra loan payments!")
- Estimate interest saved or added when relevant
- Use the student's actual loan amount and income in calculations

Key OSAP facts you know:
- Federal portion charges prime rate interest (currently 7.25%)
- Ontario provincial portion has 0% interest
- 6-month grace period after graduation (but federal interest still accrues!)
- RAP helps low-income graduates with $0 payments if income under $25k/year
- Avalanche method (highest interest first) saves most money

{financial_context}

Respond to the student's question in character as Professor Hootsworth. Keep it brief but ALWAYS include at least one specific calculation or number."""

    if not GEMINI_API_KEY:
        return jsonify({
            'response': "Hoo hoo! My crystal ball seems cloudy today. Please set up the Gemini API key to unlock my full wisdom!",
            'error': 'No API key configured'
        })
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(f"{system_prompt}\n\nStudent asks: {user_message}")
        
        return jsonify({
            'response': response.text,
            'success': True
        })
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return jsonify({
            'response': "Hoo... my feathers are ruffled! Something went wrong. Try asking again?",
            'error': str(e)
        })


# =============================================================================
# ELEVENLABS TEXT-TO-SPEECH ENDPOINT
# =============================================================================

from elevenlabs.client import ElevenLabs

ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', 'sk_949df7ef1b26bfdbdf9da237c3d8eb4de533dec179735867')

@app.route('/api/speak', methods=['POST'])
def text_to_speech():
    """
    Convert text to speech using ElevenLabs API.
    Returns audio as MP3 binary data.
    """
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    if not ELEVENLABS_API_KEY:
        return jsonify({'error': 'ElevenLabs API key not configured'}), 500
    
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # Generate speech - using "Daniel" voice (wise British broadcaster)
        audio = client.text_to_speech.convert(
            text=text,
            voice_id="onwK4e9ZLuTAKqWW03F9",  # "Daniel" - Steady Broadcaster
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        
        # Collect audio chunks into bytes
        audio_bytes = b''.join(audio)
        
        return Response(
            audio_bytes,
            mimetype='audio/mpeg',
            headers={'Content-Disposition': 'inline; filename="owl_speech.mp3"'}
        )
        
    except Exception as e:
        print(f"ElevenLabs API Error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)