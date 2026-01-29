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

async function loadBudget() {
    try {
        const response = await fetch('/api/budgets/latest/');
        
        if (response.ok) {
            const budget = await response.json();
            displayBudget(budget);
        } else {
            document.getElementById('budgetContent').innerHTML = `
                <div style="text-align: center; padding: 2rem;">
                    <p style="color: var(--text-secondary); margin-bottom: 1rem;">No budget found. Generate one to get started!</p>
                    <button onclick="generateBudget()" class="btn btn-primary">Generate Budget</button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading budget:', error);
        document.getElementById('budgetContent').innerHTML = '<div class="alert alert-error">Failed to load budget</div>';
    }
}

function displayBudget(budget) {
    let categoriesHTML = '';
    budget.category_budgets.forEach(cat => {
        categoriesHTML += `
            <div class="budget-category">
                <div class="category-header">
                    <span class="category-name">${cat.category_display}</span>
                    <span class="category-amount">₹${parseFloat(cat.recommended_limit).toLocaleString('en-IN')}</span>
                </div>
                <div style="margin-top: 0.5rem;">
                    <span class="risk-badge risk-${cat.risk_level}">${cat.risk_level} risk</span>
                    <span style="margin-left: 1rem; color: var(--text-secondary);">Avg: ₹${parseFloat(cat.actual_average).toLocaleString('en-IN')}</span>
                </div>
                <p class="category-reason">${cat.reason}</p>
            </div>
        `;
    });
    
    let weeklyHTML = '';
    budget.weekly_budgets.forEach(week => {
        weeklyHTML += `
            <div style="padding: 1rem; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>Week ${week.week_number}</strong> 
                        <span style="color: var(--text-secondary); font-size: 0.875rem;">(${week.week_start_date} to ${week.week_end_date})</span>
                    </div>
                    <div>
                        <span style="font-weight: 600;">₹${parseFloat(week.recommended_weekly_spending).toLocaleString('en-IN')}</span>
                    </div>
                </div>
                <p style="margin-top: 0.5rem; color: var(--text-secondary); font-size: 0.875rem;">${week.explanation}</p>
            </div>
        `;
    });
    
    const content = `
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 8px; color: white; margin-bottom: 2rem;">
            <h3 style="margin-bottom: 0.5rem;">${budget.month_display}</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-top: 1.5rem;">
                <div>
                    <div style="opacity: 0.9; font-size: 0.875rem;">Total Budget</div>
                    <div style="font-size: 2rem; font-weight: 700;">₹${parseFloat(budget.total_recommended_budget).toLocaleString('en-IN')}</div>
                </div>
                <div>
                    <div style="opacity: 0.9; font-size: 0.875rem;">Recommended Savings</div>
                    <div style="font-size: 2rem; font-weight: 700;">₹${parseFloat(budget.recommended_savings).toLocaleString('en-IN')}</div>
                </div>
            </div>
            <p style="margin-top: 1.5rem; opacity: 0.95;">${budget.savings_reason}</p>
        </div>
        
        <h3 style="margin-bottom: 1rem;">📊 Category Budgets</h3>
        ${categoriesHTML}
        
        <h3 style="margin: 2rem 0 1rem;">📅 Weekly Breakdown</h3>
        ${weeklyHTML}
    `;
    
    document.getElementById('budgetContent').innerHTML = content;
}

async function generateBudget() {
    showConfirmModal(
        'Generate a new budget recommendation? This will analyze your recent transactions.',
        async function() {
            // User clicked OK
            document.getElementById('budgetContent').innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating budget...</p></div>';
            
            try {
                const response = await fetch('/api/budgets/generate/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify({})
                });
                
                if (response.ok) {
                    const result = await response.json();
                    showSuccessModal('Budget generated successfully!', function() {
                        displayBudget(result.budget);
                    });
                } else {
                    const error = await response.json();
                    showErrorModal(error.error || 'Failed to generate budget');
                    loadBudget();
                }
            } catch (error) {
                showErrorModal('Error: ' + error.message);
                loadBudget();
            }
        },
        function() {
            // User clicked Cancel
            console.log('Cancelled');
        }
    );
}

document.addEventListener('DOMContentLoaded', loadBudget);

function exportBudgetPDF() {
    // Add print header
    const budgetContent = document.getElementById('budgetContent');
    const printDate = new Date().toLocaleDateString('en-IN', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
    
    // Add print-only header
    const printHeader = document.createElement('div');
    printHeader.className = 'print-header';
    printHeader.innerHTML = `
        <h1>💰 BudgetWise</h1>
        <p>Budget Recommendation Report</p>
        <p>Generated on ${printDate}</p>
        <hr style="margin: 1rem 0; border: 1px solid #E5E7EB;">
    `;
    
    budgetContent.insertBefore(printHeader, budgetContent.firstChild);
    
    // Set print date attribute
    document.body.setAttribute('data-print-date', printDate);
    
    // Trigger print
    window.print();
    
    // Remove print header after printing
    setTimeout(() => {
        printHeader.remove();
    }, 1000);
}

function exportBudgetPDF() {
    const element = document.getElementById('budgetContent');
    const opt = {
        margin: 1,
        filename: `BudgetWise-Budget-${new Date().toISOString().split('T')[0]}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    
    // Show loading
    showSuccessModal('Generating PDF... Please wait.', null);
    
    // Generate PDF
    html2pdf().set(opt).from(element).save().then(() => {
        closeModal();
    });
}