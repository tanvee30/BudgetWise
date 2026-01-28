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

async function loadTransactions() {
    try {
        const response = await fetch('/api/transactions/');
        const data = await response.json();
        const transactions = data.results || data;
        
        displayTransactions(transactions);
    } catch (error) {
        console.error('Error loading transactions:', error);
        document.getElementById('transactionsBody').innerHTML = '<tr><td colspan="5" class="alert alert-error">Failed to load transactions</td></tr>';
    }
}

function displayTransactions(transactions) {
    const tbody = document.getElementById('transactionsBody');
    
    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-secondary);">No transactions found. Add your first transaction!</td></tr>';
        return;
    }
    
    tbody.innerHTML = transactions.map(t => `
        <tr>
            <td>${t.date}</td>
            <td>${t.merchant_name}</td>
            <td style="text-transform: capitalize;">${t.category.replace('_', ' ')}</td>
            <td style="font-weight: 600; color: var(--primary-color);">₹${parseFloat(t.amount).toLocaleString('en-IN')}</td>
            <td style="font-size: 0.875rem; color: var(--text-secondary); text-transform: capitalize;">
                ${t.expense_type ? t.expense_type.replace('_', ' ') : '-'}
            </td>
        </tr>
    `).join('');
}

function showAddTransactionModal() {
    document.getElementById('addTransactionModal').style.display = 'flex';
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.querySelector('input[name="date"]').value = today;
}

function hideAddTransactionModal() {
    document.getElementById('addTransactionModal').style.display = 'none';
}

// Close modal when clicking outside
document.getElementById('addTransactionModal').addEventListener('click', function(e) {
    if (e.target === this) {
        hideAddTransactionModal();
    }
});

document.getElementById('addTransactionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    // Set default transaction source if not selected
    if (!data.transaction_source) {
        data.transaction_source = 'manual';
    }
    
    try {
        const response = await fetch('/api/transactions/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert('✅ Transaction added successfully!');
            hideAddTransactionModal();
            loadTransactions();
            e.target.reset();
        } else {
            const error = await response.json();
            alert('❌ Error: ' + JSON.stringify(error));
        }
    } catch (error) {
        alert('❌ Error adding transaction: ' + error.message);
    }
});

// Load transactions on page load
document.addEventListener('DOMContentLoaded', loadTransactions);