from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Avg, Sum, Count, StdDev, Q
from django.core.cache import cache
import logging

from .models import (
    Transaction,
    UserFinancialProfile,
    BudgetRecommendation,
    CategoryBudget,
    WeeklyBudget
)

logger = logging.getLogger(__name__)


class BudgetCalculationService:
    """
    Service class for calculating intelligent budget recommendations
    with Redis caching and optimized database queries
    """
    
    # Cache timeout constants
    BUDGET_CACHE_TIMEOUT = 3600  # 1 hour
    STATS_CACHE_TIMEOUT = 1800   # 30 minutes
    
    def __init__(self, user):
        self.user = user
        self.profile, _ = UserFinancialProfile.objects.get_or_create(
            user=user,
            defaults={
                'monthly_income': Decimal('50000.00'),
                'income_stability_score': 85.0,
                'expense_volatility_score': 0.0,
                'savings_confidence_indicator': 0.0
            }
        )
    
    def generate_budget_recommendation(self, target_month=None):
        """
        Generate intelligent budget recommendation with caching
        """
        if target_month is None:
            target_month = datetime.now().date().replace(day=1)
        
        # Check cache first
        cache_key = f'budget_{self.user.id}_{target_month.strftime("%Y-%m")}'
        cached_budget = cache.get(cache_key)
        
        if cached_budget:
            logger.info(f"✅ Cache HIT for budget {cache_key}")
            return cached_budget
        
        logger.info(f"❌ Cache MISS for budget {cache_key} - Generating new...")
        
        # Validate sufficient data
        transaction_count = Transaction.objects.filter(user=self.user).count()
        if transaction_count < 30:
            raise ValueError(
                f"Insufficient transaction data. Need at least 30 transactions "
                f"for reliable recommendations. Current count: {transaction_count}"
            )
        
        # Analyze spending patterns (OPTIMIZED with single query)
        analysis = self._analyze_spending_patterns_optimized(months_to_analyze=3)
        
        # Calculate category budgets
        category_budgets_data = self._calculate_category_budgets(analysis, target_month)
        
        # Calculate total budget
        total_budget = sum(cat['recommended_limit'] for cat in category_budgets_data)
        
        # Calculate recommended savings
        savings_data = self._calculate_recommended_savings(total_budget, analysis)
        
        # Create or update budget recommendation
        budget, created = BudgetRecommendation.objects.update_or_create(
            user=self.user,
            month=target_month,
            defaults={
                'recommended_savings': savings_data['amount'],
                'savings_reason': savings_data['reason'],
                'total_recommended_budget': total_budget,
                'is_active': True
            }
        )
        
        # Clear old category and weekly budgets
        CategoryBudget.objects.filter(budget_recommendation=budget).delete()
        WeeklyBudget.objects.filter(budget_recommendation=budget).delete()
        
        # Create category budgets
        for cat_data in category_budgets_data:
            CategoryBudget.objects.create(
                budget_recommendation=budget,
                **cat_data
            )
        
        # Generate weekly budgets
        self._generate_weekly_budgets(budget, target_month, total_budget, savings_data['amount'])
        
        # Update user's financial health scores
        self._update_financial_health_scores(analysis)
        
        # Cache the result
        cache.set(cache_key, budget, self.BUDGET_CACHE_TIMEOUT)
        logger.info(f"💾 Cached budget for {cache_key}")
        
        return budget
    
    def _analyze_spending_patterns_optimized(self, months_to_analyze=3):
        """
        OPTIMIZED: Single database query with aggregation
        """
        # Check cache first
        cache_key = f'spending_analysis_{self.user.id}_{months_to_analyze}m'
        cached_analysis = cache.get(cache_key)
        
        if cached_analysis:
            logger.info(f"✅ Cache HIT for analysis {cache_key}")
            return cached_analysis
        
        logger.info(f"❌ Cache MISS for analysis {cache_key} - Analyzing...")
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30 * months_to_analyze)
        
        # OPTIMIZED: Single aggregated query instead of multiple queries
        category_stats = Transaction.objects.filter(
            user=self.user,
            date__gte=start_date,
            date__lte=end_date,
            is_anomaly=False
        ).values('category', 'expense_type').annotate(
            avg_amount=Avg('amount'),
            total_amount=Sum('amount'),
            count=Count('id'),
            std_dev=StdDev('amount')
        ).order_by('category')
        
        # Process results
        analysis = {
            'categories': {},
            'total_spending': Decimal('0.00'),
            'transaction_count': 0,
            'start_date': start_date,
            'end_date': end_date
        }
        
        for stat in category_stats:
            category = stat['category']
            avg = Decimal(str(stat['avg_amount'] or 0))
            std = Decimal(str(stat['std_dev'] or 0))
            
            # Calculate volatility
            volatility = (std / avg * 100) if avg > 0 else Decimal('0.00')
            
            analysis['categories'][category] = {
                'average': avg,
                'total': Decimal(str(stat['total_amount'] or 0)),
                'count': stat['count'],
                'std_dev': std,
                'volatility': volatility,
                'expense_type': stat['expense_type'] or 'discretionary'
            }
            
            analysis['total_spending'] += Decimal(str(stat['total_amount'] or 0))
            analysis['transaction_count'] += stat['count']
        
        # Calculate overall volatility
        if analysis['categories']:
            avg_volatility = sum(
                cat['volatility'] for cat in analysis['categories'].values()
            ) / len(analysis['categories'])
            analysis['overall_volatility'] = float(avg_volatility)
        else:
            analysis['overall_volatility'] = 0.0
        
        # Cache the analysis
        cache.set(cache_key, analysis, self.STATS_CACHE_TIMEOUT)
        logger.info(f"💾 Cached analysis for {cache_key}")
        
        return analysis
    
    def _calculate_category_budgets(self, analysis, target_month):
        """
        Calculate recommended budget for each category with intelligent buffering
        """
        category_budgets = []
        
        for category, stats in analysis['categories'].items():
            avg = stats['average']
            volatility = stats['volatility']
            expense_type = stats['expense_type']
            
            # Intelligent buffer based on volatility and expense type
            if expense_type == 'fixed':
                buffer_percent = Decimal('0.05')  # 5% for fixed expenses
                risk_level = 'low'
            elif volatility < 10:
                buffer_percent = Decimal('0.10')  # 10% for low volatility
                risk_level = 'low'
            elif volatility < 30:
                buffer_percent = Decimal('0.15')  # 15% for moderate volatility
                risk_level = 'medium'
            else:
                buffer_percent = Decimal('0.20')  # 20% for high volatility
                risk_level = 'high'
            
            # Calculate recommended limit
            recommended_limit = avg * (1 + buffer_percent)
            variance = recommended_limit - avg
            
            # Generate explanation
            reason = self._generate_category_explanation(
                category, avg, volatility, buffer_percent, expense_type, risk_level
            )
            
            category_budgets.append({
                'category': category,
                'recommended_limit': recommended_limit,
                'actual_average': avg,
                'variance': variance,
                'risk_level': risk_level,
                'reason': reason
            })
        
        return category_budgets
    
    def _generate_category_explanation(self, category, avg, volatility, buffer, expense_type, risk):
        """Generate human-readable explanation"""
        category_name = category.replace('_', ' ').title()
        
        if expense_type == 'fixed':
            return f"Your {category_name} is a fixed expense at ₹{avg:,.0f}/month. Added minimal 5% buffer."
        
        if volatility < 10:
            return f"Your {category_name} spending is stable at ₹{avg:,.0f}/month. Added {buffer*100:.0f}% buffer for minor fluctuations."
        elif volatility < 30:
            return f"{category_name} shows moderate variation (±{volatility:.1f}%). Recommended ₹{avg * (1 + buffer):,.0f} with {buffer*100:.0f}% safety buffer."
        else:
            return f"⚠️ {category_name} spending is highly irregular (volatility: {volatility:.1f}%). Added {buffer*100:.0f}% buffer or consider reducing spending."
    
    def _calculate_recommended_savings(self, total_budget, analysis):
        """Calculate realistic savings recommendation"""
        monthly_income = self.profile.monthly_income
        available_for_savings = monthly_income - total_budget
        
        volatility = Decimal(str(analysis['overall_volatility']))
        
        # Savings confidence based on volatility
        if volatility < 20:
            savings_percent = Decimal('0.70')  # Can save 70% of available
            confidence = "high"
        elif volatility < 40:
            savings_percent = Decimal('0.50')  # Save 50%
            confidence = "moderate"
        else:
            savings_percent = Decimal('0.30')  # Save only 30% (keep buffer)
            confidence = "low"
        
        recommended_savings = available_for_savings * savings_percent
        savings_percent_of_income = (recommended_savings / monthly_income * 100)
        
        # Generate explanation
        if confidence == "high":
            reason = f"Excellent financial discipline! You can save ₹{recommended_savings:,.0f} ({savings_percent_of_income:.1f}% of income). Your low expense volatility ({volatility:.1f}%) makes this achievable."
        elif confidence == "moderate":
            reason = f"Good savings potential! Recommended ₹{recommended_savings:,.0f} ({savings_percent_of_income:.1f}% of income). Moderate expense volatility ({volatility:.1f}%) requires some buffer."
        else:
            reason = f"Conservative savings goal of ₹{recommended_savings:,.0f} ({savings_percent_of_income:.1f}% of income) due to high spending volatility ({volatility:.1f}%). Focus on stabilizing expenses first."
        
        return {
            'amount': recommended_savings,
            'reason': reason,
            'confidence': confidence
        }
    
    def _generate_weekly_budgets(self, budget, target_month, total_budget, total_savings):
        """Generate weekly breakdown of budget"""
        import calendar
        
        num_weeks = 4
        weekly_spending = total_budget / num_weeks
        weekly_savings = total_savings / num_weeks
        
        for week_num in range(1, num_weeks + 1):
            week_start = target_month.replace(day=1) + timedelta(weeks=week_num-1)
            week_end = week_start + timedelta(days=6)
            
            if week_end.month != target_month.month:
                week_end = target_month.replace(day=calendar.monthrange(target_month.year, target_month.month)[1])
            
            explanation = f"Week {week_num} budget based on monthly allocation."
            if week_num == 1:
                explanation += " Start strong!"
            elif week_num == num_weeks:
                explanation += " Final week - stay on track!"
            
            WeeklyBudget.objects.create(
                budget_recommendation=budget,
                week_number=week_num,
                week_start_date=week_start,
                week_end_date=week_end,
                recommended_weekly_spending=weekly_spending,
                recommended_weekly_savings=weekly_savings,
                explanation=explanation
            )
    
    def _update_financial_health_scores(self, analysis):
        """Update user's financial health indicators"""
        volatility = analysis['overall_volatility']
        
        # Expense volatility score (0-100, lower is better)
        self.profile.expense_volatility_score = min(100.0, volatility)
        
        # Savings confidence (inverse of volatility)
        self.profile.savings_confidence_indicator = max(0.0, 100.0 - volatility)
        
        self.profile.save()
    
    def compare_budget_vs_actual(self, budget):
        """Compare budget recommendation vs actual spending"""
        month_start = budget.month
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # OPTIMIZED: Single aggregated query
        actual_spending = Transaction.objects.filter(
            user=self.user,
            date__gte=month_start,
            date__lte=month_end
        ).values('category').annotate(
            total=Sum('amount')
        )
        
        actual_by_category = {item['category']: item['total'] for item in actual_spending}
        
        comparisons = []
        for cat_budget in budget.category_budgets.all():
            actual = Decimal(str(actual_by_category.get(cat_budget.category, 0)))
            difference = cat_budget.recommended_limit - actual
            percentage = (actual / cat_budget.recommended_limit * 100) if cat_budget.recommended_limit > 0 else 0
            
            comparisons.append({
                'category': cat_budget.category,
                'budgeted': cat_budget.recommended_limit,
                'actual': actual,
                'difference': difference,
                'percentage_used': percentage,
                'status': 'over' if actual > cat_budget.recommended_limit else 'under'
            })
        
        return comparisons


def calculate_budget_adherence(user):
    """
    Calculate budget adherence score with caching
    """
    # Check cache
    cache_key = f'adherence_{user.id}_{datetime.now().strftime("%Y-%m")}'
    cached_score = cache.get(cache_key)
    
    if cached_score:
        logger.info(f"✅ Cache HIT for adherence {cache_key}")
        return cached_score
    
    logger.info(f"❌ Cache MISS for adherence {cache_key} - Calculating...")
    
    # Get current month's budget
    current_month = datetime.now().date().replace(day=1)
    
    try:
        budget = BudgetRecommendation.objects.get(
            user=user,
            month=current_month,
            is_active=True
        )
    except BudgetRecommendation.DoesNotExist:
        return None
    
    # Get actual spending (OPTIMIZED)
    month_end = datetime.now().date()
    actual_spending = Transaction.objects.filter(
        user=user,
        date__gte=current_month,
        date__lte=month_end,
        is_anomaly=False
    ).values('category').annotate(
        total=Sum('amount')
    )
    
    actual_by_category = {item['category']: Decimal(str(item['total'])) for item in actual_spending}
    
    # Calculate scores
    category_scores = []
    category_insights = []
    
    for cat_budget in budget.category_budgets.all():
        actual = actual_by_category.get(cat_budget.category, Decimal('0'))
        budgeted = cat_budget.recommended_limit
        
        if budgeted == 0:
            continue
        
        percentage_used = (actual / budgeted * 100)
        
        # Score calculation
        if percentage_used <= 90:
            score = 100
            insight_type = 'success'
            message = f"Great job on {cat_budget.get_category_display()}! You're {100-percentage_used:.0f}% under budget."
        elif percentage_used <= 100:
            score = 80
            insight_type = 'warning'
            message = f"{cat_budget.get_category_display()}: {percentage_used:.0f}% used. Stay mindful!"
        else:
            overage = percentage_used - 100
            score = max(0, 60 - overage)
            insight_type = 'danger'
            message = f"⚠️ {cat_budget.get_category_display()}: {overage:.0f}% over budget!"
        
        category_scores.append(score)
        category_insights.append({
            'category': cat_budget.get_category_display(),
            'type': insight_type,
            'message': message
        })
    
    # Overall score
    overall_score = sum(category_scores) / len(category_scores) if category_scores else 0
    
    # Generate message
    if overall_score >= 90:
        message = "🌟 Excellent! You're doing great with your budget!"
    elif overall_score >= 70:
        message = "👍 Good job! Minor adjustments recommended."
    elif overall_score >= 50:
        message = "⚠️ Caution: Several categories need attention."
    else:
        message = "🚨 Alert: Significant budget overruns detected."
    
    # Total calculations
    total_budgeted = sum(cb.recommended_limit for cb in budget.category_budgets.all())
    total_spent = sum(actual_by_category.values())
    
    result = {
        'score': round(overall_score, 1),
        'message': message,
        'category_insights': sorted(category_insights, key=lambda x: ['danger', 'warning', 'success'].index(x['type']))[:3],
        'total_budgeted': total_budgeted,
        'total_spent': total_spent,
        'on_track': overall_score >= 70
    }
    
    # Cache for 10 minutes (shorter because it changes frequently)
    cache.set(cache_key, result, 600)
    logger.info(f"💾 Cached adherence for {cache_key}")
    
    return result