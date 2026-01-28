console.log('✅ Dashboard script loaded');

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Load dashboard data
async function loadDashboard() {
    console.log('🔄 loadDashboard() called');
    const statsGrid = document.getElementById('statsGrid');
    
    if (!statsGrid) {
        console.error('❌ statsGrid element not found!');
        return;
    }
    
    try {
        console.log('📊 Fetching profile...');
        const profileRes = await fetch('/api/profile/');
        console.log('Profile status:', profileRes.status);
        
        if (!profileRes.ok) {
            throw new Error('Profile API failed');
        }
        
        const profileData = await profileRes.json();
        console.log('Profile data:', profileData);
        
        const profile = Array.isArray(profileData) ? profileData[0] : profileData;
        
        console.log('💳 Fetching transactions...');
        const transactionsRes = await fetch('/api/transactions/recent/');
        console.log('Transactions status:', transactionsRes.status);
        
        if (!transactionsRes.ok) {
            throw new Error('Transactions API failed');
        }
        
        const transactionsData = await transactionsRes.json();
        console.log('Transactions data:', transactionsData);
        
        const transactions = Array.isArray(transactionsData) ? transactionsData : (transactionsData.results || []);
        
        console.log('💼 Fetching budget...');
        const budgetRes = await fetch('/api/budgets/latest/');
        console.log('Budget status:', budgetRes.status);
        
        let budget = null;
        if (budgetRes.ok) {
            budget = await budgetRes.json();
            console.log('Budget data:', budget);
        }
        
        console.log('🎨 Displaying stats...');
        displayStats(profile, budget, transactions);
        
        if (budget) {
            console.log('📊 Displaying budget...');
            displayBudget(budget);
        } else {
            console.log('ℹ️ No budget found');
            showNoBudgetMessage();
        }
        
        console.log('✅ Dashboard loaded successfully!');
        
    } catch (error) {
        console.error('❌ Error:', error);
        statsGrid.innerHTML = `
            <div style="grid-column: 1 / -1;">
                <div class="alert alert-error">
                    <h3>Error Loading Dashboard</h3>
                    <p>${error.message}</p>
                    <button onclick="location.reload()" class="btn btn-primary">Retry</button>
                </div>
            </div>
        `;
    }
}

function displayStats(profile, budget, transactions) {
    console.log('Rendering stats with profile:', profile);
    
    const totalSpent = transactions.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);
    
    const html = `
        <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-label">Monthly Income</div>
            <div class="stat-value">₹${parseFloat(profile.monthly_income).toLocaleString('en-IN')}</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-icon">💸</div>
            <div class="stat-label">Recent Spending</div>
            <div class="stat-value">₹${totalSpent.toLocaleString('en-IN', {maximumFractionDigits: 0})}</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-label">Expense Volatility</div>
            <div class="stat-value">${parseFloat(profile.expense_volatility_score || 0).toFixed(1)}%</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-icon">✅</div>
            <div class="stat-label">Savings Confidence</div>
            <div class="stat-value">${parseFloat(profile.savings_confidence_indicator || 0).toFixed(1)}%</div>
        </div>
    `;
    
    document.getElementById('statsGrid').innerHTML = html;
    console.log('✅ Stats rendered');
}

function showNoBudgetMessage() {
    const card = document.getElementById('latestBudgetCard');
    card.style.display = 'block';
    document.getElementById('budgetContent').innerHTML = `
        <div style="text-align: center; padding: 2rem;">
            <h3>No Budget Yet</h3>
            <p>Generate your first budget!</p>
            <button onclick="generateNewBudget()" class="btn btn-primary">Generate Budget</button>
        </div>
    `;
}

function displayBudget(budget) {
    const card = document.getElementById('latestBudgetCard');
    card.style.display = 'block';
    
    let categoriesHTML = '';
    if (budget.category_budgets) {
        budget.category_budgets.forEach(cat => {
            categoriesHTML += `
                <div class="budget-category">
                    <div class="category-header">
                        <span class="category-name">${cat.category_display}</span>
                        <span class="category-amount">₹${parseFloat(cat.recommended_limit).toLocaleString('en-IN')}</span>
                    </div>
                    <span class="risk-badge risk-${cat.risk_level}">${cat.risk_level}</span>
                    <p class="category-reason">${cat.reason}</p>
                </div>
            `;
        });
    }
    
    document.getElementById('budgetContent').innerHTML = `
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 8px; color: white; margin-bottom: 2rem;">
            <h3>${budget.month_display}</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                <div>
                    <div style="opacity: 0.9;">Total Budget</div>
                    <div style="font-size: 2rem; font-weight: 700;">₹${parseFloat(budget.total_recommended_budget).toLocaleString('en-IN')}</div>
                </div>
                <div>
                    <div style="opacity: 0.9;">Savings</div>
                    <div style="font-size: 2rem; font-weight: 700;">₹${parseFloat(budget.recommended_savings).toLocaleString('en-IN')}</div>
                </div>
            </div>
            <p style="margin-top: 1rem;">${budget.savings_reason}</p>
        </div>
        <h3>Categories</h3>
        ${categoriesHTML}
    `;
}

async function generateNewBudget() {
    if (!confirm('Generate new budget?')) return;
    
    try {
        const res = await fetch('/api/budgets/generate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({})
        });
        
        if (res.ok) {
            alert('✅ Budget generated!');
            location.reload();
        } else {
            const error = await res.json();
            alert('❌ Error: ' + (error.error || 'Failed'));
        }
    } catch (error) {
        alert('❌ Error: ' + error.message);
    }
}

// Start loading when page is ready
console.log('📄 Setting up DOMContentLoaded listener...');
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM ready! Starting dashboard load...');
    loadDashboard();
});
console.log('✅ Script initialization complete');