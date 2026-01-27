from django.contrib import admin
from .models import (
    UserFinancialProfile,
    Transaction,
    BudgetRecommendation,
    CategoryBudget,
    WeeklyBudget
)


@admin.register(UserFinancialProfile)
class UserFinancialProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'monthly_income', 
        'income_stability_score', 
        'expense_volatility_score',
        'savings_confidence_indicator',
        'updated_at'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'date',
        'merchant_name',
        'amount',
        'category',
        'expense_type',
        'transaction_source',
        'is_anomaly'
    ]
    list_filter = [
        'date',
        'category',
        'expense_type',
        'transaction_source',
        'is_anomaly'
    ]
    search_fields = [
        'merchant_name',
        'description',
        'user__username'
    ]
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date', '-created_at']


@admin.register(BudgetRecommendation)
class BudgetRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'month',
        'recommended_savings',
        'total_recommended_budget',
        'is_active',
        'generated_at'
    ]
    list_filter = ['month', 'is_active', 'generated_at']
    search_fields = ['user__username', 'savings_reason']
    readonly_fields = ['generated_at']
    date_hierarchy = 'month'
    ordering = ['-month', '-generated_at']


@admin.register(CategoryBudget)
class CategoryBudgetAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'budget_recommendation',
        'category',
        'recommended_limit',
        'actual_average',
        'variance',
        'risk_level'
    ]
    list_filter = ['category', 'risk_level', 'created_at']
    search_fields = [
        'budget_recommendation__user__username',
        'category',
        'reason'
    ]
    readonly_fields = ['created_at']
    ordering = ['budget_recommendation', 'category']


@admin.register(WeeklyBudget)
class WeeklyBudgetAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'budget_recommendation',
        'week_number',
        'week_start_date',
        'week_end_date',
        'recommended_weekly_spending',
        'recommended_weekly_savings'
    ]
    list_filter = ['week_number', 'week_start_date']
    search_fields = ['budget_recommendation__user__username']
    ordering = ['budget_recommendation', 'week_start_date']