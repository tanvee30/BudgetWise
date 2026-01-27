from django.db.models import Sum, Avg, Count, StdDev, Q
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import statistics

from .models import (
    Transaction,
    UserFinancialProfile,
    BudgetRecommendation,
    CategoryBudget,
    WeeklyBudget,
    CATEGORY_CHOICES
)


class BudgetCalculationService:
    """
    Intelligent Budget Recommendation Engine
    Analyzes historical transaction data and generates personalized budget recommendations
    """
    
    def __init__(self, user):
        self.user = user
        self.profile = self._get_or_create_profile()
    
    def _get_or_create_profile(self):
        """Get or create user's financial profile"""
        profile, created = UserFinancialProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'monthly_income': Decimal('0.00'),
                'income_stability_score': 0.0,
                'expense_volatility_score': 0.0,
                'savings_confidence_indicator': 0.0
            }
        )
        return profile
    
    def generate_budget_recommendation(self, target_month=None):
        """
        Main method to generate complete budget recommendation
        
        Args:
            target_month: datetime.date object for which month to generate budget
                         If None, generates for next month
        
        Returns:
            BudgetRecommendation object with all category budgets and weekly budgets
        """
        # Set target month
        if target_month is None:
            today = datetime.now().date()
            if today.month == 12:
                target_month = today.replace(year=today.year + 1, month=1, day=1)
            else:
                target_month = today.replace(month=today.month + 1, day=1)
        
        # Analyze historical data
        analysis_data = self._analyze_spending_patterns()
        
        if not analysis_data:
            raise ValueError("Insufficient transaction data to generate budget recommendation")
        
        # Calculate category-wise budgets
        category_budgets_data = self._calculate_category_budgets(analysis_data)
        
        # Calculate total budget and savings
        total_budget = sum(cat['recommended_limit'] for cat in category_budgets_data.values())
        recommended_savings = self._calculate_recommended_savings(
            total_budget, 
            analysis_data
        )
        
        # Generate savings explanation
        savings_reason = self._generate_savings_explanation(
            recommended_savings,
            total_budget,
            analysis_data
        )
        
        # Create or update budget recommendation
        budget_recommendation, created = BudgetRecommendation.objects.update_or_create(
            user=self.user,
            month=target_month,
            defaults={
                'recommended_savings': recommended_savings,
                'savings_reason': savings_reason,
                'total_recommended_budget': total_budget,
                'is_active': True
            }
        )
        
        # Create category budgets
        for category, budget_data in category_budgets_data.items():
            CategoryBudget.objects.update_or_create(
                budget_recommendation=budget_recommendation,
                category=category,
                defaults={
                    'recommended_limit': budget_data['recommended_limit'],
                    'actual_average': budget_data['actual_average'],
                    'variance': budget_data['variance'],
                    'risk_level': budget_data['risk_level'],
                    'reason': budget_data['reason']
                }
            )
        
        # Generate weekly budgets
        self._generate_weekly_budgets(budget_recommendation, total_budget, recommended_savings)
        
        # Update user profile scores
        self._update_profile_scores(analysis_data)
        
        return budget_recommendation
    
    def _analyze_spending_patterns(self, months_to_analyze=3):
        """
        Analyze historical spending patterns
        
        Returns:
            Dictionary with spending analysis data
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30 * months_to_analyze)
        
        # Get all transactions in the period (excluding anomalies from averages)
        transactions = Transaction.objects.filter(
            user=self.user,
            date__gte=start_date,
            date__lte=end_date
        )
        
        if not transactions.exists():
            return None
        
        # Analyze by category
        category_analysis = {}
        
        for category_code, category_name in CATEGORY_CHOICES:
            category_transactions = transactions.filter(category=category_code)
            
            if not category_transactions.exists():
                continue
            
            # Get transactions excluding anomalies for average calculation
            normal_transactions = category_transactions.filter(is_anomaly=False)
            
            if normal_transactions.exists():
                amounts = list(normal_transactions.values_list('amount', flat=True))
                amounts_float = [float(amt) for amt in amounts]
                
                avg_spending = statistics.mean(amounts_float)
                
                # Calculate volatility (standard deviation / mean)
                if len(amounts_float) > 1:
                    std_dev = statistics.stdev(amounts_float)
                    volatility = (std_dev / avg_spending * 100) if avg_spending > 0 else 0
                else:
                    volatility = 0
                
                # Determine expense type (most common in this category)
                expense_type = normal_transactions.values('expense_type').annotate(
                    count=Count('id')
                ).order_by('-count').first()
                
                category_analysis[category_code] = {
                    'category_name': category_name,
                    'average_spending': Decimal(str(avg_spending)),
                    'total_transactions': category_transactions.count(),
                    'normal_transactions': normal_transactions.count(),
                    'volatility': volatility,
                    'expense_type': expense_type['expense_type'] if expense_type else 'discretionary',
                    'has_anomalies': category_transactions.filter(is_anomaly=True).exists(),
                    'monthly_frequency': normal_transactions.count() / months_to_analyze
                }
        
        return {
            'categories': category_analysis,
            'total_transactions': transactions.count(),
            'analysis_period_months': months_to_analyze,
            'start_date': start_date,
            'end_date': end_date
        }
    
    def _calculate_category_budgets(self, analysis_data):
        """
        Calculate recommended budget for each category
        
        Returns:
            Dictionary with category budget recommendations
        """
        category_budgets = {}
        
        for category_code, data in analysis_data['categories'].items():
            avg_spending = data['average_spending']
            volatility = data['volatility']
            expense_type = data['expense_type']
            
            # Base recommendation on average spending
            recommended_limit = avg_spending
            
            # Adjust based on expense type and volatility
            if expense_type == 'fixed':
                # Fixed expenses: minimal buffer (5%)
                buffer_percent = Decimal('0.05')
                risk_level = 'low'
                reason = f"Based on your consistent {data['category_name']} expenses with minimal variation."
            
            elif expense_type == 'variable_essential':
                # Variable essentials: moderate buffer based on volatility
                if volatility < 20:
                    buffer_percent = Decimal('0.10')
                    risk_level = 'low'
                    reason = f"Your {data['category_name']} spending is fairly stable (avg ₹{avg_spending:.0f}/month). Added 10% buffer."
                elif volatility < 40:
                    buffer_percent = Decimal('0.15')
                    risk_level = 'medium'
                    reason = f"Your {data['category_name']} spending varies moderately. Added 15% buffer for fluctuations."
                else:
                    buffer_percent = Decimal('0.20')
                    risk_level = 'medium'
                    reason = f"Your {data['category_name']} spending is quite variable. Added 20% safety buffer."
            
            else:  # discretionary
                # Discretionary: recommend reduction if high volatility
                if volatility < 25:
                    buffer_percent = Decimal('0.05')
                    risk_level = 'low'
                    reason = f"Your {data['category_name']} spending is stable. Maintaining current level with small buffer."
                elif volatility < 50:
                    buffer_percent = Decimal('0.00')  # No increase
                    risk_level = 'medium'
                    reason = f"Your {data['category_name']} spending fluctuates. Budget set at average to encourage control."
                else:
                    buffer_percent = Decimal('-0.10')  # Recommend 10% reduction
                    risk_level = 'high'
                    reason = f"Your {data['category_name']} spending is highly irregular. Recommending 10% reduction for better control."
            
            # Apply buffer
            recommended_limit = avg_spending * (Decimal('1.00') + buffer_percent)
            recommended_limit = recommended_limit.quantize(Decimal('0.01'))
            
            # Calculate variance
            variance = recommended_limit - avg_spending
            
            category_budgets[category_code] = {
                'recommended_limit': recommended_limit,
                'actual_average': avg_spending,
                'variance': variance,
                'risk_level': risk_level,
                'reason': reason,
                'volatility': volatility,
                'expense_type': expense_type
            }
        
        return category_budgets
    
    def _calculate_recommended_savings(self, total_budget, analysis_data):
        """
        Calculate realistic savings recommendation
        
        This is NOT a fixed percentage - it's based on:
        1. User's income
        2. Historical spending patterns
        3. Expense volatility
        4. Income stability
        """
        monthly_income = self.profile.monthly_income
        
        if monthly_income <= 0:
            return Decimal('0.00')
        
        # Calculate available amount after budgeted expenses
        available_for_savings = monthly_income - total_budget
        
        # If already overspending, recommend minimal savings
        if available_for_savings <= 0:
            return Decimal('0.00')
        
        # Calculate average volatility across all categories
        volatilities = [cat['volatility'] for cat in analysis_data['categories'].values()]
        avg_volatility = statistics.mean(volatilities) if volatilities else 50
        
        # Determine savings percentage based on stability
        if avg_volatility < 20:
            # Low volatility - can save more confidently
            savings_percent = Decimal('0.70')  # 70% of available
        elif avg_volatility < 40:
            # Medium volatility - moderate savings
            savings_percent = Decimal('0.50')  # 50% of available
        else:
            # High volatility - conservative savings
            savings_percent = Decimal('0.30')  # 30% of available
        
        recommended_savings = available_for_savings * savings_percent
        
        # Ensure savings is at least 5% of income if possible
        min_savings = monthly_income * Decimal('0.05')
        if recommended_savings < min_savings and available_for_savings >= min_savings:
            recommended_savings = min_savings
        
        return recommended_savings.quantize(Decimal('0.01'))
    
    def _generate_savings_explanation(self, recommended_savings, total_budget, analysis_data):
        """
        Generate human-readable explanation for savings recommendation
        """
        monthly_income = self.profile.monthly_income
        savings_percent = (recommended_savings / monthly_income * 100) if monthly_income > 0 else 0
        
        # Calculate average volatility
        volatilities = [cat['volatility'] for cat in analysis_data['categories'].values()]
        avg_volatility = statistics.mean(volatilities) if volatilities else 50
        
        # Count expense types
        fixed_count = sum(1 for cat in analysis_data['categories'].values() if cat['expense_type'] == 'fixed')
        total_categories = len(analysis_data['categories'])
        
        # Generate contextual explanation
        if savings_percent < 5:
            reason = f"Your fixed commitments are high (₹{total_budget:.0f}). Recommended minimal savings of ₹{recommended_savings:.0f} "
            reason += "to maintain financial stability. Consider reviewing discretionary expenses."
        
        elif savings_percent < 15:
            if avg_volatility > 40:
                reason = f"Your spending shows high variability. Recommended conservative savings of ₹{recommended_savings:.0f} "
                reason += f"({savings_percent:.1f}% of income) to build an emergency buffer."
            else:
                reason = f"Based on your stable spending pattern, you can save ₹{recommended_savings:.0f} "
                reason += f"({savings_percent:.1f}% of income) comfortably."
        
        elif savings_percent < 25:
            reason = f"Your spending is well-controlled! You can save ₹{recommended_savings:.0f} "
            reason += f"({savings_percent:.1f}% of income) while maintaining your lifestyle."
        
        else:
            reason = f"Excellent financial discipline! You can save ₹{recommended_savings:.0f} "
            reason += f"({savings_percent:.1f}% of income). Your low expense volatility makes this achievable."
        
        return reason
    
    def _generate_weekly_budgets(self, budget_recommendation, total_budget, recommended_savings):
        """
        Generate weekly budget breakdowns for the month
        """
        target_month = budget_recommendation.month
        
        # Calculate number of weeks in the month
        if target_month.month == 12:
            next_month = target_month.replace(year=target_month.year + 1, month=1, day=1)
        else:
            next_month = target_month.replace(month=target_month.month + 1, day=1)
        
        month_end = next_month - timedelta(days=1)
        days_in_month = (month_end - target_month).days + 1
        
        # Typically 4-5 weeks
        num_weeks = (days_in_month + 6) // 7
        
        weekly_spending = total_budget / num_weeks
        weekly_savings = recommended_savings / num_weeks
        
        # Create weekly budgets
        current_date = target_month
        for week_num in range(1, num_weeks + 1):
            week_start = current_date
            week_end = min(current_date + timedelta(days=6), month_end)
            
            explanation = f"Week {week_num} budget based on monthly allocation. "
            if week_num == 1:
                explanation += "Start strong to set the tone for the month!"
            elif week_num == num_weeks:
                explanation += "Final week - review your progress and adjust if needed."
            else:
                explanation += "Stay on track with consistent spending."
            
            WeeklyBudget.objects.update_or_create(
                budget_recommendation=budget_recommendation,
                week_number=week_num,
                defaults={
                    'week_start_date': week_start,
                    'week_end_date': week_end,
                    'recommended_weekly_spending': weekly_spending.quantize(Decimal('0.01')),
                    'recommended_weekly_savings': weekly_savings.quantize(Decimal('0.01')),
                    'explanation': explanation
                }
            )
            
            current_date = week_end + timedelta(days=1)
    
    def _update_profile_scores(self, analysis_data):
        """
        Update user's financial profile scores based on analysis
        """
        if not analysis_data or not analysis_data['categories']:
            return
        
        # Calculate expense volatility score (0-100, higher = more volatile)
        volatilities = [cat['volatility'] for cat in analysis_data['categories'].values()]
        avg_volatility = statistics.mean(volatilities) if volatilities else 50
        expense_volatility_score = min(avg_volatility, 100)
        
        # Calculate income stability score (hardcoded for now, could be enhanced)
        # In a real system, this would analyze income transaction patterns
        income_stability_score = 85.0  # Placeholder
        
        # Calculate savings confidence (inverse of volatility, adjusted for fixed expenses)
        fixed_expenses = sum(
            1 for cat in analysis_data['categories'].values() 
            if cat['expense_type'] == 'fixed'
        )
        total_categories = len(analysis_data['categories'])
        
        fixed_ratio = (fixed_expenses / total_categories * 100) if total_categories > 0 else 0
        
        # Higher confidence if more fixed expenses and lower volatility
        savings_confidence = (100 - expense_volatility_score) * 0.6 + fixed_ratio * 0.4
        
        # Update profile
        self.profile.income_stability_score = income_stability_score
        self.profile.expense_volatility_score = expense_volatility_score
        self.profile.savings_confidence_indicator = savings_confidence
        self.profile.save()
    
    def compare_budget_vs_actual(self, budget_recommendation):
        """
        Compare recommended budget vs actual spending for a given budget period
        
        Returns:
            Dictionary with comparison data
        """
        target_month = budget_recommendation.month
        
        # Get actual spending for the month
        if target_month.month == 12:
            next_month = target_month.replace(year=target_month.year + 1, month=1, day=1)
        else:
            next_month = target_month.replace(month=target_month.month + 1, day=1)
        
        month_end = next_month - timedelta(days=1)
        
        actual_transactions = Transaction.objects.filter(
            user=self.user,
            date__gte=target_month,
            date__lte=month_end,
            is_anomaly=False
        )
        
        # Aggregate by category
        actual_by_category = actual_transactions.values('category').annotate(
            total_spent=Sum('amount')
        )
        
        actual_spending_dict = {
            item['category']: item['total_spent'] 
            for item in actual_by_category
        }
        
        # Compare with budget
        comparison = {
            'month': target_month.strftime('%B %Y'),
            'categories': {},
            'total_budgeted': budget_recommendation.total_recommended_budget,
            'total_spent': sum(actual_spending_dict.values()),
            'budget_status': 'under' if sum(actual_spending_dict.values()) <= budget_recommendation.total_recommended_budget else 'over'
        }
        
        for category_budget in budget_recommendation.category_budgets.all():
            actual_spent = actual_spending_dict.get(category_budget.category, Decimal('0.00'))
            difference = category_budget.recommended_limit - actual_spent
            
            comparison['categories'][category_budget.category] = {
                'budgeted': category_budget.recommended_limit,
                'actual': actual_spent,
                'difference': difference,
                'status': 'under' if difference >= 0 else 'over',
                'percentage_used': (actual_spent / category_budget.recommended_limit * 100) if category_budget.recommended_limit > 0 else 0
            }
        
        return comparison