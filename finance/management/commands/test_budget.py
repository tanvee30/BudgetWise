from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from finance.services import BudgetCalculationService
from datetime import datetime
import json


class Command(BaseCommand):
    help = 'Test budget calculation engine'

    def handle(self, *args, **options):
        # Get test user
        try:
            user = User.objects.get(username='testuser')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Test user not found. Run seed_data first.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n🧠 Testing Budget Engine for {user.username}...\n'))
        
        # Initialize service
        service = BudgetCalculationService(user)
        
        # Generate budget recommendation
        try:
            budget = service.generate_budget_recommendation()
            
            self.stdout.write(self.style.SUCCESS(f'✓ Budget generated for {budget.month.strftime("%B %Y")}'))
            self.stdout.write(f'\n📊 BUDGET SUMMARY:')
            self.stdout.write(f'  Total Budget: ₹{budget.total_recommended_budget}')
            self.stdout.write(f'  Recommended Savings: ₹{budget.recommended_savings}')
            self.stdout.write(f'  Reason: {budget.savings_reason}\n')
            
            self.stdout.write(f'📋 CATEGORY BREAKDOWN:')
            for cat_budget in budget.category_budgets.all():
                self.stdout.write(f'\n  {cat_budget.category.upper()}:')
                self.stdout.write(f'    Recommended: ₹{cat_budget.recommended_limit}')
                self.stdout.write(f'    Your Average: ₹{cat_budget.actual_average}')
                self.stdout.write(f'    Variance: ₹{cat_budget.variance}')
                self.stdout.write(f'    Risk: {cat_budget.risk_level}')
                self.stdout.write(f'    💡 {cat_budget.reason}')
            
            self.stdout.write(f'\n📅 WEEKLY BUDGETS:')
            for week in budget.weekly_budgets.all():
                self.stdout.write(f'\n  Week {week.week_number} ({week.week_start_date} to {week.week_end_date}):')
                self.stdout.write(f'    Spending: ₹{week.recommended_weekly_spending}')
                self.stdout.write(f'    Savings: ₹{week.recommended_weekly_savings}')
            
            self.stdout.write(self.style.SUCCESS(f'\n\n🎉 Budget engine test successful!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))