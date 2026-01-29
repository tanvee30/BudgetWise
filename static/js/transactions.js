console.log('✅ Transactions script loaded');

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

// Store all transactions for filtering
let allTransactions = [];

async function loadTransactions() {
    console.log('Loading transactions...');
    try {
        const response = await fetch('/api/transactions/');
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Data received:', data);
        
        allTransactions = data.results || data;
        console.log('Total transactions:', allTransactions.length);
        
        displayTransactions(allTransactions);
    } catch (error) {
        console.error('Error loading transactions:', error);
        document.getElementById('transactionsBody').innerHTML = `
            <tr>
                <td colspan="5" class="alert alert-error">
                    Failed to load transactions: ${error.message}
                </td>
            </tr>
        `;
    }
}

function filterTransactions() {
    console.log('Filtering transactions...');
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter').value;
    const monthFilter = document.getElementById('monthFilter').value;
    
    let filtered = allTransactions.filter(t => {
        // Search filter
        const matchesSearch = !searchTerm || 
            t.merchant_name.toLowerCase().includes(searchTerm) ||
            (t.description && t.description.toLowerCase().includes(searchTerm));
        
        // Category filter
        const matchesCategory = !categoryFilter || t.category === categoryFilter;
        
        // Month filter
        const matchesMonth = !monthFilter || t.date.startsWith(monthFilter);
        
        return matchesSearch && matchesCategory && matchesMonth;
    });
    
    console.log('Filtered to', filtered.length, 'transactions');
    displayTransactions(filtered);
}

function clearFilters() {
    console.log('Clearing filters...');
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('monthFilter').value = '';
    displayTransactions(allTransactions);
}

function displayTransactions(transactions) {
    console.log('Displaying', transactions.length, 'transactions');
    const tbody = document.getElementById('transactionsBody');
    const countElement = document.getElementById('transactionCount');
    
    if (countElement) {
        countElement.textContent = transactions.length;
    }
    
    if (transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                    No transactions found. ${allTransactions.length === 0 ? 'Add your first transaction!' : 'Try different filters.'}
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = transactions.map(t => `
        <tr>
            <td>${new Date(t.date).toLocaleDateString('en-IN')}</td>
            <td><strong>${t.merchant_name}</strong></td>
            <td style="text-transform: capitalize;">
                <span style="background: #E0E7FF; color: #4338CA; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">
                    ${t.category.replace('_', ' ')}
                </span>
            </td>
            <td style="font-weight: 600; color: var(--primary-color);">₹${parseFloat(t.amount).toLocaleString('en-IN')}</td>
            <td style="font-size: 0.875rem; color: var(--text-secondary); text-transform: capitalize;">
                ${t.expense_type ? t.expense_type.replace('_', ' ') : '-'}
            </td>
        </tr>
    `).join('');
}

function showAddTransactionModal() {
    console.log('Showing add transaction modal');
    document.getElementById('addTransactionModal').style.display = 'flex';
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.querySelector('input[name="date"]').value = today;
}

function hideAddTransactionModal() {
    console.log('Hiding add transaction modal');
    document.getElementById('addTransactionModal').style.display = 'none';
}

// Close modal when clicking outside
const modal = document.getElementById('addTransactionModal');
if (modal) {
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            hideAddTransactionModal();
        }
    });
}

// Form submit handler
const form = document.getElementById('addTransactionForm');
if (form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('Form submitted');
        
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        
        // Set default transaction source if not selected
        if (!data.transaction_source) {
            data.transaction_source = 'manual';
        }
        
        console.log('Submitting data:', data);
        
        try {
            const response = await fetch('/api/transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(data)
            });
            
            console.log('Response status:', response.status);
            
            if (response.ok) {
                const result = await response.json();
                console.log('Transaction added:', result);
                
                hideAddTransactionModal();
                showSuccessModal('Transaction added successfully!', function() {
                    loadTransactions();
                });
                e.target.reset();
            } else {
                const error = await response.json();
                console.error('Server error:', error);
                showErrorModal('Error: ' + JSON.stringify(error));
            }
        } catch (error) {
            console.error('Request error:', error);
            showErrorModal('Error adding transaction: ' + error.message);
        }
    });
}

// Load transactions when page loads
console.log('Setting up page load listener...');
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, loading transactions...');
    loadTransactions();
});