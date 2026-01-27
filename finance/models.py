from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

# Category Choices
CATEGORY_CHOICES = [
    ('food', 'Food'),
    ('transport', 'Transport'),
    ('entertainment', 'Entertainment'),
    ('shopping', 'Shopping'),
    ('bills', 'Bills & Utilities'),
    ('rent', 'Rent'),
    ('emi', 'EMI'),
    ('healthcare', 'Healthcare'),
    ('education', 'Education'),
    ('subscriptions', 'Subscriptions'),
    ('other', 'Other'),
]

# Expense Classification
EXPENSE_TYPE_CHOICES = [
    ('fixed', 'Fixed Expenses'),
    ('variable_essential', 'Variable Essentials'),
    ('discretionary', 'Discretionary'),
]

# Transaction Source
TRANSACTION_SOURCE_CHOICES = [
    ('upi', 'UPI'),
    ('bank', 'Bank Transfer'),
    ('card', 'Card'),
    ('cash', 'Cash'),
    ('manual', 'Manual Entry'),
]

# Risk Level
RISK_LEVEL_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]


class UserFinancialProfile(models.Model):
    """
    User's financial profile with income, expenses, and stability indicators
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='financial_profile')
    
    # Income details
    monthly_income = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="User's monthly income"
    )
    
    # Derived indicators
    income_stability_score = models.FloatField(
        default=0.0,
        help_text="Score from 0-100 indicating income stability"
    )
    expense_volatility_score = models.FloatField(
        default=0.0,
        help_text="Score from 0-100 indicating expense volatility (higher = more volatile)"
    )
    savings_confidence_indicator = models.FloatField(
        default=0.0,
        help_text="Score from 0-100 indicating confidence in meeting savings goals"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Financial Profile"
        verbose_name_plural = "User Financial Profiles"
    
    def __str__(self):
        return f"{self.user.username}'s Financial Profile"


class Transaction(models.Model):
    """
    Individual transaction record
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction details
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date = models.DateField()
    merchant_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    # Classification
    expense_type = models.CharField(
        max_length=50, 
        choices=EXPENSE_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Fixed, Variable Essential, or Discretionary"
    )
    
    transaction_source = models.CharField(
        max_length=50, 
        choices=TRANSACTION_SOURCE_CHOICES,
        default='manual'
    )
    
    # Additional info
    description = models.TextField(blank=True, null=True)
    is_anomaly = models.BooleanField(
        default=False,
        help_text="Marks one-time large or unusual expenses"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.merchant_name} - ₹{self.amount} on {self.date}"


class BudgetRecommendation(models.Model):
    """
    AI-generated budget recommendations for a specific month
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budget_recommendations')
    
    # Time period
    month = models.DateField(help_text="Month for which budget is recommended (YYYY-MM-01)")
    
    # Savings recommendation
    recommended_savings = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    savings_reason = models.TextField(
        help_text="Explanation for recommended savings amount"
    )
    
    # Overall budget metadata
    total_recommended_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-month', '-generated_at']
        unique_together = ['user', 'month']
        indexes = [
            models.Index(fields=['user', 'month']),
        ]
    
    def __str__(self):
        return f"Budget for {self.user.username} - {self.month.strftime('%B %Y')}"


class CategoryBudget(models.Model):
    """
    Category-wise budget breakdown within a BudgetRecommendation
    """
    budget_recommendation = models.ForeignKey(
        BudgetRecommendation, 
        on_delete=models.CASCADE, 
        related_name='category_budgets'
    )
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    # Budget details
    recommended_limit = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Recommended spending limit for this category"
    )
    
    actual_average = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Historical average spending in this category"
    )
    
    variance = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Difference between recommended and actual (can be negative)"
    )
    
    risk_level = models.CharField(
        max_length=10, 
        choices=RISK_LEVEL_CHOICES,
        default='low'
    )
    
    reason = models.TextField(
        help_text="Explanation for this category's budget recommendation"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category']
        unique_together = ['budget_recommendation', 'category']
    
    def __str__(self):
        return f"{self.category} - ₹{self.recommended_limit}"


class WeeklyBudget(models.Model):
    """
    Weekly budget breakdown for better tracking
    """
    budget_recommendation = models.ForeignKey(
        BudgetRecommendation,
        on_delete=models.CASCADE,
        related_name='weekly_budgets'
    )
    
    week_number = models.IntegerField(
        help_text="Week number in the month (1-4 or 5)"
    )
    week_start_date = models.DateField()
    week_end_date = models.DateField()
    
    recommended_weekly_spending = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    recommended_weekly_savings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    explanation = models.TextField(
        help_text="Why this weekly budget makes sense"
    )
    
    class Meta:
        ordering = ['week_start_date']
        unique_together = ['budget_recommendation', 'week_number']
    
    def __str__(self):
        return f"Week {self.week_number} - ₹{self.recommended_weekly_spending}"