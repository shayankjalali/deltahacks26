/* ============================================
   OSAP OPTIMIZER - CLEAN VERSION
   ============================================ */

const gameState = {
    playerName: 'Student',
    playerCharacter: null,
    dialogueStep: 0,

    formData: {
        loan_amount: 0,
        federal_portion: 60,
        graduation_date: '',
        monthly_income: 0,
        monthly_expenses: 0,
        field_of_study: 'other',
        family_size: 1,
        has_emergency_fund: false,
        credit_card_balance: 0,
        line_of_credit_balance: 0,
        car_loan_balance: 0
    },

    results: null,
    chart: null,
    currentAudio: null  // Track currently playing audio
};

// ============================================
// SCREEN MANAGEMENT
// ============================================

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById(screenId);
    screen.classList.add('active');
    screen.classList.add('fade-in');
    setTimeout(() => screen.classList.remove('fade-in'), 300);
}

// ============================================
// CHARACTER SELECT
// ============================================

function selectCharacter(charIndex) {
    gameState.playerCharacter = charIndex;
    playSound('select');

    document.querySelectorAll('.character-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    document.querySelector(`.character-option[data-char="${charIndex}"]`).classList.add('selected');

    document.getElementById('startBtn').disabled = false;
}

function startGame() {
    if (gameState.playerCharacter === null) return;
    playSound('click');

    const nameInput = document.getElementById('playerName').value.trim();
    gameState.playerName = nameInput || 'Student';

    showScreen('screen-office');
    setTimeout(startDialogue, 300);
}

// ============================================
// DIALOGUE SYSTEM
// ============================================

function getDialogues() {
    return [
        {
            text: `Hoo hoo! Welcome, <span class="highlight">${gameState.playerName}</span>! I am Professor Hootsworth, keeper of OSAP wisdom. I shall guide you on your quest to financial freedom!`,      
            input: null
        },
        {
            text: `First, tell me - what is your <span class="highlight">total OSAP balance</span>? This includes both federal and provincial portions.`,
            input: {
                type: 'number',
                id: 'loan_amount',
                placeholder: '30000',
                label: 'Total OSAP Balance ($)'
            }
        },
        {
            text: `What <span class="highlight">percentage is federal</span>? Typically around 60%. Federal loans have interest, while Ontario's provincial portion is interest-free!`,
            input: {
                type: 'number',
                id: 'federal_portion',
                placeholder: '60',
                label: 'Federal Portion (%)',
                default: 60
            }
        },
        {
            text: `When do you expect to <span class="highlight">graduate</span>? Your 6-month grace period starts after this - but federal interest still accrues!`,
            input: {
                type: 'date',
                id: 'graduation_date',
                label: 'Graduation Date'
            }
        },
        {
            text: `What is your <span class="highlight">field of study</span>? This helps predict your earning potential.`,
            input: {
                type: 'select',
                id: 'field_of_study',
                label: 'Field of Study',
                options: [
                    { value: 'computer_science', text: 'Computer Science' },
                    { value: 'engineering', text: 'Engineering' },
                    { value: 'business', text: 'Business' },
                    { value: 'nursing', text: 'Healthcare/Nursing' },
                    { value: 'science', text: 'Science' },
                    { value: 'arts', text: 'Arts/Humanities' },
                    { value: 'education', text: 'Education' },
                    { value: 'trades', text: 'Skilled Trades' },
                    { value: 'other', text: 'Other' }
                ]
            }
        },
        {
            text: `What is your expected <span class="highlight">monthly income</span> and <span class="highlight">expenses</span> after graduation?`,
            input: {
                type: 'double',
                fields: [
                    { id: 'monthly_income', label: 'Monthly Income ($)', placeholder: '4000' },
                    { id: 'monthly_expenses', label: 'Monthly Expenses ($)', placeholder: '2500' }
                ]
            }
        },
        {
            text: `How many people in your <span class="highlight">household</span>? This affects RAP eligibility.`,
            input: {
                type: 'number',
                id: 'family_size',
                placeholder: '1',
                label: 'Household Size',
                default: 1
            }
        },
        {
            text: `Do you have a <span class="highlight">3-month emergency fund</span>? Wise scholars save before aggressively paying debt!`,
            input: {
                type: 'checkbox',
                id: 'has_emergency_fund',
                label: 'Yes, I have an emergency fund saved'
            }
        },
        {
            text: `Any <span class="highlight">other debts</span>? Credit cards, lines of credit, car loans? Enter 0 if none.`,
            input: {
                type: 'triple',
                fields: [
                    { id: 'credit_card_balance', label: 'Credit Card ($)', placeholder: '0' },
                    { id: 'line_of_credit_balance', label: 'Line of Credit ($)', placeholder: '0' },
                    { id: 'car_loan_balance', label: 'Car Loan ($)', placeholder: '0' }
                ]
            }
        },
        {
            text: `Excellent! You've provided everything I need. Let me consult the ancient scrolls of financial wisdom...`,
            input: null,
            final: true
        }
    ];
}

function startDialogue() {
    gameState.dialogueStep = 0;
    showDialogue();
}

function showDialogue() {
    const dialogues = getDialogues();
    const d = dialogues[gameState.dialogueStep];
    const textEl = document.getElementById('dialogueText');
    const inputEl = document.getElementById('dialogueInput');
    const btn = document.getElementById('nextBtn');

    textEl.innerHTML = d.text;
    inputEl.innerHTML = d.input ? buildInput(d.input) : '';

    if (d.final) {
        btn.textContent = '🔮 Reveal My Destiny';
        btn.onclick = calculateResults;
    } else {
        btn.textContent = 'Continue →';
        btn.onclick = nextDialogue;
    }
}

function buildInput(input) {
    if (input.type === 'number') {
        return `
            <label>${input.label}</label>
            <input type="number" id="input_${input.id}" placeholder="${input.placeholder}" value="${input.default || ''}">
        `;
    }

    if (input.type === 'date') {
        const d = new Date();
        d.setMonth(d.getMonth() + 4);
        return `
            <label>${input.label}</label>
            <input type="date" id="input_${input.id}" value="${d.toISOString().split('T')[0]}">
        `;
    }

    if (input.type === 'select') {
        const opts = input.options.map(o => `<option value="${o.value}">${o.text}</option>`).join('');
        return `
            <label>${input.label}</label>
            <select id="input_${input.id}">${opts}</select>
        `;
    }

    if (input.type === 'checkbox') {
        return `
            <div class="checkbox-row">
                <input type="checkbox" id="input_${input.id}">
                <label for="input_${input.id}">${input.label}</label>
            </div>
        `;
    }

    if (input.type === 'double') {
        return `
            <div class="input-row">
                ${input.fields.map(f => `
                    <div>
                        <label>${f.label}</label>
                        <input type="number" id="input_${f.id}" placeholder="${f.placeholder}">
                    </div>
                `).join('')}
            </div>
        `;
    }

    if (input.type === 'triple') {
        return `
            <div class="input-row">
                ${input.fields.map(f => `
                    <div>
                        <label>${f.label}</label>
                        <input type="number" id="input_${f.id}" placeholder="${f.placeholder}" value="0">
                    </div>
                `).join('')}
            </div>
        `;
    }

    return '';
}

function nextDialogue() {
    playSound('click');
    saveInput();
    gameState.dialogueStep++;
    const dialogues = getDialogues();
    if (gameState.dialogueStep < dialogues.length) {
        showDialogue();
    }
}

function saveInput() {
    const dialogues = getDialogues();
    const d = dialogues[gameState.dialogueStep];
    if (!d.input) return;

    const input = d.input;

    if (input.type === 'checkbox') {
        const el = document.getElementById(`input_${input.id}`);
        if (el) gameState.formData[input.id] = el.checked;
    } else if (input.type === 'double' || input.type === 'triple') {
        input.fields.forEach(f => {
            const el = document.getElementById(`input_${f.id}`);
            if (el) gameState.formData[f.id] = parseFloat(el.value) || 0;
        });
    } else {
        const el = document.getElementById(`input_${input.id}`);
        if (el) {
            gameState.formData[input.id] = input.type === 'number'
                ? (parseFloat(el.value) || input.default || 0)
                : el.value;
        }
    }
}

// ============================================
// API & RESULTS
// ============================================

async function calculateResults() {
    saveInput();

    const btn = document.getElementById('nextBtn');
    btn.textContent = '🔮 Consulting scrolls...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(gameState.formData)
        });

        gameState.results = await res.json();
        showScreen('screen-results');
        playSound('success');
        displayResults(gameState.results);

    } catch (err) {
        console.error(err);
        btn.textContent = '❌ Error - Try Again';
        btn.disabled = false;
    }
}

function displayResults(r) {
    document.getElementById('r-playerName').textContent = gameState.playerName;

    // Loan summary - use the correct IDs from HTML
    document.getElementById('r-totalLoan').textContent = r.loan_details.total_amount.toLocaleString();
    document.getElementById('r-afterGrace').textContent = r.grace_period.balance_after_grace.toLocaleString();
    document.getElementById('r-graceInt').textContent = r.grace_period.interest_accrued.toLocaleString();
    document.getElementById('r-fedAmount').textContent = r.loan_details.federal_amount.toLocaleString();
    document.getElementById('r-provAmount').textContent = r.loan_details.provincial_amount.toLocaleString();

    const rapBox = document.getElementById('r-rapBox');
    const rap = r.rap_status;
    rapBox.className = `rap-box ${rap.eligible ? 'eligible' : 'not-eligible'}`;
    document.getElementById('r-rapStatus').innerHTML = `
        <strong>${rap.title}</strong><br><br>
        ${rap.description}
        ${rap.eligible ? `<br><br>Required payment: <strong>$${rap.monthly_payment}/mo</strong>` : ''}
    `;

    const s = r.scenarios;

    document.getElementById('r-minPay').textContent = s.minimum.monthly_payment;
    document.getElementById('r-minTime').textContent = formatTime(s.minimum.years, s.minimum.remaining_months);
    document.getElementById('r-minInt').textContent = s.minimum.total_interest.toLocaleString();

    document.getElementById('r-recPay').textContent = s.recommended.monthly_payment;
    document.getElementById('r-recTime').textContent = formatTime(s.recommended.years, s.recommended.remaining_months);
    document.getElementById('r-recInt').textContent = s.recommended.total_interest.toLocaleString();
    document.getElementById('r-recSave').textContent = r.savings.rec_vs_min_interest > 0
        ? `Save $${r.savings.rec_vs_min_interest.toLocaleString()}!` : '';

    document.getElementById('r-aggPay').textContent = s.aggressive.monthly_payment;
    document.getElementById('r-aggTime').textContent = formatTime(s.aggressive.years, s.aggressive.remaining_months);
    document.getElementById('r-aggInt').textContent = s.aggressive.total_interest.toLocaleString();
    document.getElementById('r-aggSave').textContent = r.savings.agg_vs_min_interest > 0
        ? `Save $${r.savings.agg_vs_min_interest.toLocaleString()}!` : '';

    drawChart(s);
    setupSlider(r);

    if (gameState.formData.credit_card_balance > 0 ||
        gameState.formData.line_of_credit_balance > 0 ||
        gameState.formData.car_loan_balance > 0) {
        fetchMultiDebt();
    }

    setWisdom(r);
    
    // Load community comparison from MongoDB
    loadCommunityComparison();
}

function formatTime(y, m) {
    if (y === 0) return `${m} months`;
    if (m === 0) return `${y} years`;
    return `${y}y ${m}m`;
}

function drawChart(s, customData = null) {
    const ctx = document.getElementById('questChart');
    if (!ctx) return;

    if (gameState.chart) {
        gameState.chart.destroy();
    }

    const max = Math.max(s.minimum.months, s.recommended.months, s.aggressive.months);
    const step = Math.max(1, Math.floor(max / 25));
    const labels = [];
    for (let i = 0; i <= max; i += step) labels.push(i);

    function getData(breakdown) {
        return labels.map(m => {
            if (m === 0) return breakdown[0] ? breakdown[0].total_balance + (breakdown[0].principal_paid || 0) : 0;
            if (m <= breakdown.length) return breakdown[m-1].total_balance;
            return 0;
        });
    }

    const datasets = [
        {
            label: '🐢 Minimum',
            data: getData(s.minimum.breakdown),
            borderColor: '#7f8c8d',
            backgroundColor: 'rgba(127,140,141,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 0
        },
        {
            label: '🛡️ Balanced',
            data: getData(s.recommended.breakdown),
            borderColor: '#2980b9',
            backgroundColor: 'rgba(41,128,185,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 0
        },
        {
            label: '⚔️ Aggressive',
            data: getData(s.aggressive.breakdown),
            borderColor: '#c0392b',
            backgroundColor: 'rgba(192,57,43,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 0
        }
    ];

    if (customData && customData.breakdown && customData.breakdown.length > 0) {
        datasets.push({
            label: '✨ Your Plan',
            data: getData(customData.breakdown),
            borderColor: '#FFD700',
            backgroundColor: 'rgba(255,215,0,0.15)',
            fill: true,
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 3
        });
    }

    gameState.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#3d2817',
                        font: { family: "'Press Start 2P'", size: 7 }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Months', color: '#5c4033', font: { family: "'Press Start 2P'", size: 7 } },
                    ticks: { color: '#8B7355', font: { size: 6 } },
                    grid: { color: 'rgba(139,115,85,0.2)' }
                },
                y: {
                    title: { display: true, text: 'Balance', color: '#5c4033', font: { family: "'Press Start 2P'", size: 7 } },
                    ticks: {
                        color: '#8B7355',
                        font: { size: 6 },
                        callback: v => '$' + (v/1000).toFixed(0) + 'k'
                    },
                    grid: { color: 'rgba(139,115,85,0.2)' }
                }
            }
        }
    });
}

function setupSlider(results) {
    const slider = document.getElementById('extraSlider');
    const amountEl = document.getElementById('extraAmount');
    const resultEl = document.getElementById('extraResult');

    slider.oninput = async (e) => {
        const extra = parseInt(e.target.value);
        amountEl.textContent = `$${extra}`;

        if (extra === 0) {
            resultEl.textContent = '';
            drawChart(results.scenarios);
            updateOwlWisdom(0, 0, 0, results);
            return;
        }

        try {
            const res = await fetch('/api/whatif', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    loan_amount: gameState.formData.loan_amount,
                    federal_portion: gameState.formData.federal_portion,
                    extra_payment: extra,
                    base_payment: results.scenarios.recommended.monthly_payment
                })
            });
            const data = await res.json();
            if (!data.error) {
                resultEl.textContent = `✨ Save $${data.interest_saved.toLocaleString()} & finish ${data.months_saved} months sooner!`;
                
                if (data.breakdown) {
                    drawChart(results.scenarios, { breakdown: data.breakdown });
                }
                
                // Update owl wisdom based on slider
                updateOwlWisdom(extra, data.interest_saved, data.months_saved, results);
            }
        } catch (err) {
            console.error(err);
        }
    };
}

function updateOwlWisdom(extra, interestSaved, monthsSaved, results) {
    const el = document.getElementById('owlWisdom');
    const name = gameState.playerName;
    
    let w = '';
    
    if (extra === 0) {
        // Default wisdom when slider is at 0
        w = setDefaultWisdom(results);
    } else if (extra <= 50) {
        w = `"${name}, even $${extra} extra per month makes a difference! You'll save $${interestSaved.toLocaleString()} and finish ${monthsSaved} months sooner. Small steps lead to great victories!"`;
    } else if (extra <= 100) {
        w = `"Hoo hoo! $${extra} extra is a wise choice, ${name}! Saving $${interestSaved.toLocaleString()} in interest and ${monthsSaved} months of payments - that's powerful financial magic!"`;
    } else if (extra <= 200) {
        w = `"Impressive dedication, ${name}! At $${extra} extra per month, you'll save $${interestSaved.toLocaleString()} and be free ${monthsSaved} months sooner. Your future self will thank you!"`;
    } else if (extra <= 350) {
        w = `"By the ancient scrolls! $${extra} extra per month is ambitious, ${name}! You'll save a magnificent $${interestSaved.toLocaleString()} and finish ${monthsSaved} months early. Legendary!"`;
    } else {
        w = `"Extraordinary, ${name}! $${extra} extra per month? You'll vanquish $${interestSaved.toLocaleString()} in interest and finish ${monthsSaved} months ahead of schedule. A true financial warrior!"`;
    }
    
    el.textContent = w;
}

function setDefaultWisdom(r) {
    const rap = r.rap_status;
    const sav = r.savings;
    const name = gameState.playerName;

    if (rap.eligible && rap.stage === 2) {
        return `"Wonderful news, ${name}! You qualify for full RAP assistance. The government covers your payments while income is low. Use this time to build your career!"`;
    } else if (sav.agg_vs_min_interest > 5000) {
        return `"Hoo hoo! The aggressive path saves over $${Math.round(sav.agg_vs_min_interest/1000)}k in interest! A powerful financial spell indeed."`;
    } else if (gameState.formData.credit_card_balance > 0) {
        return `"Beware, ${name}! Credit card debt carries dark magic - high interest that compounds fast. Vanquish it first!"`;
    } else if (!gameState.formData.has_emergency_fund) {
        return `"Before extra debt payments, build a small emergency fund. Even 3 months of expenses protects against life's surprises."`;
    } else {
        return `"Well done, ${name}! Consistent payments and wise choices pave the path to freedom. You have all you need to succeed!"`;
    }
}

async function fetchMultiDebt() {
    try {
        const res = await fetch('/api/multi-debt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                loan_amount: gameState.formData.loan_amount,
                federal_portion: gameState.formData.federal_portion,
                credit_card_balance: gameState.formData.credit_card_balance,
                line_of_credit_balance: gameState.formData.line_of_credit_balance,
                car_loan_balance: gameState.formData.car_loan_balance,
                monthly_budget: (gameState.formData.monthly_income - gameState.formData.monthly_expenses) * 0.5
            })
        });

        const data = await res.json();
        if (!data.error) {
            document.getElementById('r-multiDebt').classList.remove('hidden');
            document.getElementById('r-totalDebt').textContent = data.total_debt.toLocaleString();
            document.getElementById('r-debtOrder').innerHTML = data.recommended_order.map(d => `<li>${d}</li>`).join('');
            document.getElementById('r-strategy').textContent = data.strategy;
        }
    } catch (err) {
        console.error(err);
    }
}

function setWisdom(r) {
    const el = document.getElementById('owlWisdom');
    el.textContent = setDefaultWisdom(r);
}

// ============================================
// MUSIC & SOUND
// ============================================

const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playSound(type) {
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    if (type === 'click') {
        oscillator.frequency.value = 800;
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + 0.1);
    } else if (type === 'success') {
        oscillator.frequency.value = 523.25;
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        oscillator.start(audioCtx.currentTime);
        oscillator.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.1);
        oscillator.frequency.setValueAtTime(783.99, audioCtx.currentTime + 0.2);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        oscillator.stop(audioCtx.currentTime + 0.4);
    } else if (type === 'select') {
        oscillator.frequency.value = 600;
        gainNode.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.05);
        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + 0.05);
    }
}

// Volume control
let lastVolume = 30;

function setVolume(value) {
    const music = document.getElementById('bgMusic');
    const icon = document.querySelector('.volume-icon');
    
    music.volume = value / 100;
    
    if (value == 0) {
        icon.textContent = '🔇';
    } else if (value < 50) {
        icon.textContent = '🔉';
    } else {
        icon.textContent = '🔊';
    }
    
    if (value > 0) {
        lastVolume = value;
    }
}

function toggleMute() {
    const slider = document.getElementById('volumeSlider');
    const music = document.getElementById('bgMusic');
    
    if (music.volume > 0) {
        lastVolume = slider.value;
        slider.value = 0;
        setVolume(0);
    } else {
        slider.value = lastVolume;
        setVolume(lastVolume);
    }
}

// Start music on first interaction
let musicStarted = false;
document.addEventListener('click', function initMusic() {
    if (!musicStarted) {
        const music = document.getElementById('bgMusic');
        const slider = document.getElementById('volumeSlider');
        music.volume = slider.value / 100;
        music.play().then(() => {
            musicStarted = true;
        }).catch(e => console.log('Autoplay blocked:', e));
    }
}, { once: true });

// ============================================
// UTILITIES
// ============================================

function restartGame() {
    gameState.dialogueStep = 0;
    gameState.results = null;
    gameState.playerCharacter = null;
    gameState.formData = {
        loan_amount: 0,
        federal_portion: 60,
        graduation_date: '',
        monthly_income: 0,
        monthly_expenses: 0,
        field_of_study: 'other',
        family_size: 1,
        has_emergency_fund: false,
        credit_card_balance: 0,
        line_of_credit_balance: 0,
        car_loan_balance: 0
    };

    // Destroy chart if exists
    if (gameState.chart) {
        gameState.chart.destroy();
        gameState.chart = null;
    }
    
    // Stop any playing audio
    if (gameState.currentAudio) {
        gameState.currentAudio.pause();
        gameState.currentAudio = null;
    }

    // Reset UI elements
    document.querySelectorAll('.character-option').forEach(o => o.classList.remove('selected'));
    document.getElementById('startBtn').disabled = true;
    document.getElementById('playerName').value = '';
    
    // Reset the next button to default state
    const nextBtn = document.getElementById('nextBtn');
    nextBtn.textContent = 'Continue →';
    nextBtn.onclick = nextDialogue;
    nextBtn.disabled = false;

    showScreen('screen-title');
}

function downloadResults() {
    if (!gameState.results) return;

    const r = gameState.results;
    const s = r.scenarios;

    const txt = `
OSAP OPTIMIZER - FINANCIAL QUEST RESULTS
========================================
Prepared for: ${gameState.playerName}
Date: ${new Date().toLocaleDateString()}

OSAP BREAKDOWN
--------------
Total: $${r.loan_details.total_amount.toLocaleString()}
Federal: $${r.loan_details.federal_amount.toLocaleString()} @ ${r.loan_details.federal_rate}%
Provincial: $${r.loan_details.provincial_amount.toLocaleString()} @ ${r.loan_details.provincial_rate}%
Grace Period Interest: $${r.grace_period.interest_accrued.toLocaleString()}

RAP ELIGIBILITY
---------------
${r.rap_status.title}
${r.rap_status.description}

REPAYMENT PATHS
---------------
🐢 MINIMUM
   $${s.minimum.monthly_payment}/month
   ${s.minimum.years}y ${s.minimum.remaining_months}m
   Interest: $${s.minimum.total_interest.toLocaleString()}

🛡️ BALANCED (Recommended)
   $${s.recommended.monthly_payment}/month
   ${s.recommended.years}y ${s.recommended.remaining_months}m
   Interest: $${s.recommended.total_interest.toLocaleString()}
   Saves: $${r.savings.rec_vs_min_interest.toLocaleString()}

⚔️ AGGRESSIVE
   $${s.aggressive.monthly_payment}/month
   ${s.aggressive.years}y ${s.aggressive.remaining_months}m
   Interest: $${s.aggressive.total_interest.toLocaleString()}
   Saves: $${r.savings.agg_vs_min_interest.toLocaleString()}

========================================
Generated by OSAP Optimizer
DeltaHacks 2025
    `.trim();

    const blob = new Blob([txt], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `OSAP_Results_${gameState.playerName}.txt`;
    a.click();
}

// ============================================
// GEMINI AI CHAT WITH PROFESSOR HOOTSWORTH
// ============================================

async function sendChat() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    const messagesContainer = document.getElementById('chatMessages');
    
    // Add user message
    messagesContainer.innerHTML += `
        <div class="chat-message user">
            <span class="chat-icon">👤</span>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    
    // Clear input
    input.value = '';
    
    // Add loading message
    messagesContainer.innerHTML += `
        <div class="chat-message owl loading" id="loadingMsg">
            <span class="chat-icon">🦉</span>
            <p>
                <span class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </span>
            </p>
        </div>
    `;
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                loan_amount: gameState.formData.loan_amount,
                monthly_income: gameState.formData.monthly_income,
                monthly_expenses: gameState.formData.monthly_expenses,
                field_of_study: gameState.formData.field_of_study
            })
        });
        
        const data = await response.json();
        
        // Remove loading message
        document.getElementById('loadingMsg').remove();
        
        // Add owl response with speak button
        const msgId = 'owl-msg-' + Date.now();
        messagesContainer.innerHTML += `
            <div class="chat-message owl" id="${msgId}">
                <span class="chat-icon">🦉</span>
                <p>${escapeHtml(data.response)}</p>
                <button class="speak-btn" onclick="speakText('${msgId}')" title="Listen to Professor Hootsworth">
                    🔊
                </button>
            </div>
        `;
        
        // Store the text for speaking
        document.getElementById(msgId).dataset.text = data.response;
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
    } catch (error) {
        console.error('Chat error:', error);
        document.getElementById('loadingMsg').remove();
        
        messagesContainer.innerHTML += `
            <div class="chat-message owl">
                <span class="chat-icon">🦉</span>
                <p>Hoo... my connection to the wisdom realm is disrupted. Try again?</p>
            </div>
        `;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// ELEVENLABS TEXT-TO-SPEECH
// ============================================

// Speak the current dialogue text
async function speakDialogue() {
    const dialogueEl = document.getElementById('dialogueText');
    const btn = document.getElementById('dialogueSpeakBtn');
    
    if (!dialogueEl) return;
    
    // Get plain text (strip HTML tags)
    const text = dialogueEl.innerText || dialogueEl.textContent;
    
    if (!text) return;
    
    // Stop any currently playing audio
    if (gameState.currentAudio) {
        gameState.currentAudio.pause();
        gameState.currentAudio = null;
        btn.textContent = '🔊';
        btn.classList.remove('playing');
        return; // Just stop if already playing
    }
    
    // Show loading state
    btn.textContent = '⏳';
    btn.classList.add('loading');
    
    try {
        const response = await fetch('/api/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        if (!response.ok) {
            throw new Error('Speech generation failed');
        }
        
        // Get audio blob
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Create and play audio
        const audio = new Audio(audioUrl);
        gameState.currentAudio = audio;
        
        // Update button to playing state
        btn.textContent = '⏹️';
        btn.classList.remove('loading');
        btn.classList.add('playing');
        
        audio.play();
        
        // Reset button when audio ends
        audio.onended = () => {
            btn.textContent = '🔊';
            btn.classList.remove('playing');
            gameState.currentAudio = null;
            URL.revokeObjectURL(audioUrl);
        };
        
    } catch (error) {
        console.error('Speech error:', error);
        btn.textContent = '🔊';
        btn.classList.remove('loading');
    }
}

async function speakText(msgId) {
    const msgEl = document.getElementById(msgId);
    const text = msgEl.dataset.text;
    const btn = msgEl.querySelector('.speak-btn');
    
    if (!text) return;
    
    // Stop any currently playing audio
    if (gameState.currentAudio) {
        gameState.currentAudio.pause();
        gameState.currentAudio = null;
        // Reset all speak buttons
        document.querySelectorAll('.speak-btn').forEach(b => {
            b.textContent = '🔊';
            b.classList.remove('playing');
        });
    }
    
    // Show loading state
    btn.textContent = '⏳';
    btn.classList.add('loading');
    
    try {
        const response = await fetch('/api/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        if (!response.ok) {
            throw new Error('Speech generation failed');
        }
        
        // Get audio blob
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Create and play audio
        const audio = new Audio(audioUrl);
        gameState.currentAudio = audio;
        
        // Update button to playing state
        btn.textContent = '⏹️';
        btn.classList.remove('loading');
        btn.classList.add('playing');
        
        audio.play();
        
        // Reset button when audio ends
        audio.onended = () => {
            btn.textContent = '🔊';
            btn.classList.remove('playing');
            gameState.currentAudio = null;
            URL.revokeObjectURL(audioUrl);
        };
        
        // Allow stopping
        btn.onclick = () => {
            if (gameState.currentAudio) {
                gameState.currentAudio.pause();
                gameState.currentAudio = null;
                btn.textContent = '🔊';
                btn.classList.remove('playing');
                btn.onclick = () => speakText(msgId);
            }
        };
        
    } catch (error) {
        console.error('Speech error:', error);
        btn.textContent = '🔊';
        btn.classList.remove('loading');
        alert('Could not generate speech. Check if ElevenLabs API key is set.');
    }
}


// ============================================
// MONGODB - SAVE & LOAD PLANS
// ============================================

async function savePlanToMongo() {
    const planName = document.getElementById('savePlanName').value.trim() || 'My Plan';
    const saveResult = document.getElementById('saveResult');
    
    saveResult.innerHTML = '<span class="saving">💾 Saving to MongoDB Atlas...</span>';
    
    try {
        const response = await fetch('/api/plans/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                plan_name: planName,
                ...gameState.formData,
                results: gameState.results
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            saveResult.innerHTML = `
                <div class="save-success">
                    <p>✅ Plan saved successfully!</p>
                    <p class="plan-code">Your code: <strong>${data.plan_id}</strong></p>
                    <p class="plan-hint">Use this code to load your plan later!</p>
                </div>
            `;
        } else {
            saveResult.innerHTML = `<span class="save-error">❌ Error: ${data.error}</span>`;
        }
    } catch (error) {
        console.error('Save error:', error);
        saveResult.innerHTML = '<span class="save-error">❌ Failed to save. Check connection.</span>';
    }
}


async function loadSavedPlan() {
    const planCode = document.getElementById('loadPlanCode').value.trim();
    
    if (!planCode) {
        alert('Please enter a plan code!');
        return;
    }
    
    try {
        const response = await fetch(`/api/plans/load/${planCode}`);
        const data = await response.json();
        
        if (data.success && data.plan) {
            // Load form data into gameState
            gameState.formData = { ...gameState.formData, ...data.plan.form_data };
            gameState.results = data.plan.results;
            gameState.playerName = data.plan.plan_name || 'Student';
            
            // Auto-select first character
            selectCharacter(0);
            
            // Skip dialogue and go straight to results if we have them
            if (gameState.results) {
                showScreen('screen-results');
                displayResults(gameState.results);
                playSound('success');
            } else {
                alert(`✅ Plan "${data.plan.plan_name}" loaded! Click "Begin Quest" to continue.`);
            }
        } else {
            alert('❌ Plan not found. Check the code and try again.');
        }
    } catch (error) {
        console.error('Load error:', error);
        alert('❌ Failed to load plan. Check connection.');
    }
}


// ============================================
// MONGODB - COMMUNITY STATS & COMPARISON
// ============================================

async function loadCommunityComparison() {
    const container = document.getElementById('communityStats');
    
    if (!gameState.formData.loan_amount || gameState.formData.loan_amount <= 0) {
        container.innerHTML = '<p class="no-data">Enter your loan info to see comparisons!</p>';
        return;
    }
    
    try {
        // Get comparison data
        const response = await fetch('/api/community/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                loan_amount: gameState.formData.loan_amount,
                field_of_study: gameState.formData.field_of_study
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            let html = '<div class="comparison-grid">';
            
            // Your loan
            html += `
                <div class="comparison-box your-loan">
                    <div class="comparison-label">Your OSAP Loan</div>
                    <div class="comparison-value">$${formatNumber(data.your_loan)}</div>
                </div>
            `;
            
            // Overall average
            if (data.overall_average) {
                const overallDiff = data.overall_percent;
                const overallClass = overallDiff > 0 ? 'above' : 'below';
                html += `
                    <div class="comparison-box overall-avg">
                        <div class="comparison-label">Ontario Average</div>
                        <div class="comparison-value">$${formatNumber(data.overall_average)}</div>
                        <div class="comparison-diff ${overallClass}">
                            ${overallDiff > 0 ? '↑' : '↓'} ${Math.abs(overallDiff)}% ${data.vs_overall}
                        </div>
                        <div class="comparison-note">${data.total_students} students tracked</div>
                    </div>
                `;
            }
            
            // Field average
            if (data.field_average) {
                const fieldDiff = data.field_percent;
                const fieldClass = fieldDiff > 0 ? 'above' : 'below';
                const fieldName = getFieldName(data.field_of_study);
                html += `
                    <div class="comparison-box field-avg">
                        <div class="comparison-label">${fieldName} Average</div>
                        <div class="comparison-value">$${formatNumber(data.field_average)}</div>
                        <div class="comparison-diff ${fieldClass}">
                            ${fieldDiff > 0 ? '↑' : '↓'} ${Math.abs(fieldDiff)}% ${data.vs_field}
                        </div>
                        <div class="comparison-note">${data.field_count} ${fieldName} students</div>
                    </div>
                `;
            }
            
            html += '</div>';
            
            // Add insights
            if (data.overall_average) {
                const insight = data.vs_overall === 'above' 
                    ? '📈 Your debt is higher than average. Consider aggressive repayment!'
                    : '📉 Your debt is below average. Great job keeping it manageable!';
                html += `<p class="comparison-insight">${insight}</p>`;
            }
            
            container.innerHTML = html;
        } else {
            container.innerHTML = `
                <div class="comparison-box your-loan">
                    <div class="comparison-label">Your OSAP Loan</div>
                    <div class="comparison-value">$${formatNumber(gameState.formData.loan_amount)}</div>
                </div>
                <p class="comparison-note">Be the first to add data! Your info helps other students.</p>
            `;
        }
    } catch (error) {
        console.error('Community stats error:', error);
        container.innerHTML = '<p class="no-data">Could not load community data.</p>';
    }
}


function getFieldName(field) {
    const fieldNames = {
        'engineering': 'Engineering',
        'computer_science': 'Computer Science',
        'business': 'Business',
        'health': 'Health Sciences',
        'arts': 'Arts & Humanities',
        'science': 'Science',
        'trades': 'Trades',
        'education': 'Education',
        'law': 'Law',
        'other': 'General'
    };
    return fieldNames[field] || 'General';
}


function formatNumber(num) {
    return Math.round(num).toLocaleString();
}