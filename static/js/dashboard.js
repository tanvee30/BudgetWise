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

// Global chart instances
let categoryChart = null;
let trendChart = null;
let budgetComparisonChart = null;

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
        if (!profileRes.ok) throw new Error('Profile API failed');
        
        const profileData = await profileRes.json();
        const profile = Array.isArray(profileData) ? profileData[0] : profileData;
        
        console.log('💳 Fetching transactions...');
        const transactionsRes = await fetch('/api/transactions/');
        if (!transactionsRes.ok) throw new Error('Transactions API failed');
        
        const transactionsData = await transactionsRes.json();
        const allTransactions = Array.isArray(transactionsData) ? transactionsData : (transactionsData.results || []);
        
        // Get recent transactions (last 30 days)
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        const recentTransactions = allTransactions.filter(t => new Date(t.date) >= thirtyDaysAgo);
        
        console.log('💼 Fetching budget...');
        const budgetRes = await fetch('/api/budgets/latest/');
        let budget = null;
        if (budgetRes.ok) {
            budget = await budgetRes.json();
        }
        
        // Display everything
        displayStats(profile, budget, recentTransactions);
        renderCategoryChart(recentTransactions);
        renderTrendChart(allTransactions);
        
        if (budget) {
            displayBudget(budget);
            renderBudgetComparisonChart(budget, recentTransactions);
            loadAdherenceScore();
        } else {
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
    const totalSpent = transactions.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);
    
    const html = `
        <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-label">Monthly Income</div>
            <div class="stat-value">₹${parseFloat(profile.monthly_income).toLocaleString('en-IN')}</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-icon">💸</div>
            <div class="stat-label">Recent Spending (30 days)</div>
            <div class="stat-value">₹${totalSpent.toLocaleString('en-IN', {maximumFractionDigits: 0})}</div>
            <div style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.5rem;">
                ${transactions.length} transactions
            </div>
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
}

// Chart 1: Spending by Category (Pie Chart)
function renderCategoryChart(transactions) {
    const categoryTotals = {};
    
    transactions.forEach(t => {
        const category = t.category || 'other';
        categoryTotals[category] = (categoryTotals[category] || 0) + parseFloat(t.amount);
    });
    
    const labels = Object.keys(categoryTotals).map(cat => cat.charAt(0).toUpperCase() + cat.slice(1).replace('_', ' '));
    const data = Object.values(categoryTotals);
    
    const ctx = document.getElementById('categoryChart');
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#4F46E5', '#10B981', '#F59E0B', '#EF4444', 
                    '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12,
                            family: 'Inter'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return label + ': ₹' + value.toLocaleString('en-IN');
                        }
                    }
                }
            }
        }
    });
}

// Chart 2: Monthly Trend (Line Chart)
function renderTrendChart(transactions) {
    // Group transactions by month
    const monthlyData = {};
    
    transactions.forEach(t => {
        const date = new Date(t.date);
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        monthlyData[monthKey] = (monthlyData[monthKey] || 0) + parseFloat(t.amount);
    });
    
    // Sort by month and get last 6 months
    const sortedMonths = Object.keys(monthlyData).sort().slice(-6);
    const labels = sortedMonths.map(m => {
        const [year, month] = m.split('-');
        const date = new Date(year, month - 1);
        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    });
    const data = sortedMonths.map(m => monthlyData[m]);
    
    const ctx = document.getElementById('trendChart');
    
    if (trendChart) {
        trendChart.destroy();
    }
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Monthly Spending',
                data: data,
                borderColor: '#4F46E5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointBackgroundColor: '#4F46E5',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Spent: ₹' + context.parsed.y.toLocaleString('en-IN');
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + value.toLocaleString('en-IN');
                        }
                    }
                }
            }
        }
    });
}

// Chart 3: Budget vs Actual (Bar Chart)
function renderBudgetComparisonChart(budget, transactions) {
    const budgetCard = document.getElementById('budgetComparisonCard');
    budgetCard.style.display = 'block';
    
    // Calculate actual spending by category
    const actualSpending = {};
    transactions.forEach(t => {
        const category = t.category || 'other';
        actualSpending[category] = (actualSpending[category] || 0) + parseFloat(t.amount);
    });
    
    // Prepare data
    const categories = [];
    const budgetedAmounts = [];
    const actualAmounts = [];
    
    budget.category_budgets.forEach(cat => {
        categories.push(cat.category_display);
        budgetedAmounts.push(parseFloat(cat.recommended_limit));
        actualAmounts.push(actualSpending[cat.category] || 0);
    });
    
    const ctx = document.getElementById('budgetComparisonChart');
    
    if (budgetComparisonChart) {
        budgetComparisonChart.destroy();
    }
    
    budgetComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [
                {
                    label: 'Budgeted',
                    data: budgetedAmounts,
                    backgroundColor: 'rgba(79, 70, 229, 0.8)',
                    borderColor: '#4F46E5',
                    borderWidth: 2
                },
                {
                    label: 'Actual',
                    data: actualAmounts,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: '#10B981',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12,
                            family: 'Inter'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ₹' + context.parsed.y.toLocaleString('en-IN');
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + value.toLocaleString('en-IN');
                        }
                    }
                }
            }
        }
    });
}

function showNoBudgetMessage() {
    const card = document.getElementById('latestBudgetCard');
    card.style.display = 'block';
    document.getElementById('budgetContent').innerHTML = `
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📊</div>
            <h3>No Budget Yet</h3>
            <p style="color: var(--text-secondary);">Generate your first budget!</p>
            <button onclick="generateNewBudget()" class="btn btn-primary" style="margin-top: 1rem;">Generate Budget</button>
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
    showConfirmModal(
        'Generate a new budget recommendation? This will analyze your recent transactions.',
        async function() {
            const budgetContent = document.getElementById('budgetContent');
            budgetContent.innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating budget...</p></div>';
            
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
                    showSuccessModal('Budget generated successfully!', function() {
                        location.reload();
                    });
                } else {
                    const error = await res.json();
                    showErrorModal(error.error || 'Failed to generate budget');
                    showNoBudgetMessage();
                }
            } catch (error) {
                showErrorModal('Error: ' + error.message);
                showNoBudgetMessage();
            }
        }
    );
}

// Load on page ready
document.addEventListener('DOMContentLoaded', loadDashboard);


// Load Budget Adherence Score
async function loadAdherenceScore() {
    try {
        const res = await fetch('/api/budgets/adherence/');
        if (res.ok) {
            const data = await res.json();
            displayAdherenceScore(data);
        }
    } catch (error) {
        console.log('No adherence data available');
    }
}

function displayAdherenceScore(data) {
    const card = document.getElementById('adherenceCard');
    const content = document.getElementById('adherenceContent');
    
    card.style.display = 'block';
    
    // Score gauge
    const scoreColor = data.score >= 90 ? '#10B981' : 
                       data.score >= 70 ? '#F59E0B' : '#EF4444';
    
    let insightsHTML = '';
    if (data.category_insights) {
        data.category_insights.forEach(insight => {
            const icon = insight.type === 'success' ? '✅' : 
                        insight.type === 'warning' ? '⚠️' : '🚨';
            insightsHTML += `
                <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;">
                    ${icon} ${insight.message}
                </div>
            `;
        });
    }
    
    content.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 2rem; padding: 1.5rem 0;">
            <div style="text-align: center;">
                <div style="width: 150px; height: 150px; margin: 0 auto; position: relative;">
                    <svg viewBox="0 0 100 100" style="transform: rotate(-90deg);">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="10"/>
                        <circle cx="50" cy="50" r="45" fill="none" stroke="${scoreColor}" stroke-width="10"
                                stroke-dasharray="${data.score * 2.827} 282.7"
                                stroke-linecap="round"/>
                    </svg>
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 2rem; font-weight: 700;">
                        ${data.score}%
                    </div>
                </div>
                <div style="margin-top: 1rem; font-size: 1.5rem;">
                    ${data.message}
                </div>
            </div>
            <div>
                <h4 style="margin-bottom: 1rem;">📊 This Month</h4>
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span>Budgeted:</span>
                        <span style="font-weight: 600;">₹${parseFloat(data.total_budgeted).toLocaleString('en-IN')}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span>Spent:</span>
                        <span style="font-weight: 600;">₹${parseFloat(data.total_spent).toLocaleString('en-IN')}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Remaining:</span>
                        <span style="font-weight: 600;">₹${(parseFloat(data.total_budgeted) - parseFloat(data.total_spent)).toLocaleString('en-IN')}</span>
                    </div>
                </div>
                <h4 style="margin-bottom: 1rem;">💡 Key Insights</h4>
                ${insightsHTML}
            </div>
        </div>
    `;
}