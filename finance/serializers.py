from rest_framework import serializers
from .models import (
    Transaction,
    UserFinancialProfile,
    BudgetRecommendation,
    CategoryBudget,
    WeeklyBudget
)


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'amount',
            'date',
            'merchant_name',
            'category',
            'expense_type',
            'transaction_source',
            'description',
            'is_anomaly',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        # Automatically set user from request context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserFinancialProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserFinancialProfile model"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserFinancialProfile
        fields = [
            'id',
            'username',
            'monthly_income',
            'income_stability_score',
            'expense_volatility_score',
            'savings_confidence_indicator',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'income_stability_score',
            'expense_volatility_score',
            'savings_confidence_indicator',
            'updated_at'
        ]


class CategoryBudgetSerializer(serializers.ModelSerializer):
    """Serializer for CategoryBudget model"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = CategoryBudget
        fields = [
            'id',
            'category',
            'category_display',
            'recommended_limit',
            'actual_average',
            'variance',
            'risk_level',
            'reason'
        ]


class WeeklyBudgetSerializer(serializers.ModelSerializer):
    """Serializer for WeeklyBudget model"""
    
    class Meta:
        model = WeeklyBudget
        fields = [
            'id',
            'week_number',
            'week_start_date',
            'week_end_date',
            'recommended_weekly_spending',
            'recommended_weekly_savings',
            'explanation'
        ]


class BudgetRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for BudgetRecommendation model"""
    category_budgets = CategoryBudgetSerializer(many=True, read_only=True)
    weekly_budgets = WeeklyBudgetSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    month_display = serializers.SerializerMethodField()
    
    class Meta:
        model = BudgetRecommendation
        fields = [
            'id',
            'username',
            'month',
            'month_display',
            'recommended_savings',
            'savings_reason',
            'total_recommended_budget',
            'category_budgets',
            'weekly_budgets',
            'generated_at',
            'is_active'
        ]
        read_only_fields = ['id', 'generated_at']
    
    def get_month_display(self, obj):
        return obj.month.strftime('%B %Y')


class BudgetComparisonSerializer(serializers.Serializer):
    """Serializer for budget vs actual comparison"""
    month = serializers.CharField()
    total_budgeted = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    budget_status = serializers.CharField()
    categories = serializers.DictField()