from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from finance.models import UserFinancialProfile, Transaction
from datetime import datetime, timedelta
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Seeds the database with sample financial data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=3,
            help='Number of months of transaction history to generate (default: 3)'
        )

    def handle(self, *args, **options):
        months = options['months']
        
        # Create or get test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'testuser@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created user: {user.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'! User already exists: {user.username}'))
        
        # Create or update financial profile
        profile, created = UserFinancialProfile.objects.update_or_create(
            user=user,
            defaults={
                'monthly_income': Decimal('50000.00'),
                'income_stability_score': 85.0,
                'expense_volatility_score': 35.0,
                'savings_confidence_indicator': 70.0
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created financial profile for {user.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'! Updated financial profile for {user.username}'))
        
        # Delete existing transactions for clean slate
        Transaction.objects.filter(user=user).delete()
        self.stdout.write(self.style.WARNING(f'! Deleted existing transactions'))
        
        # Generate transactions for the last N months
        transactions_created = 0
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30 * months)
        
        # Transaction templates with realistic patterns
        transaction_templates = {
            'rent': {
                'category': 'rent',
                'expense_type': 'fixed',
                'merchants': ['ABC Apartments', 'Landlord'],
                'amount_range': (15000, 15000),  # Fixed
                'frequency': 'monthly',  # Once per month
                'day_of_month': 1
            },
            'food': {
                'category': 'food',
                'expense_type': 'variable_essential',
                'merchants': ['Swiggy', 'Zomato', 'BigBasket', 'D-Mart', 'Local Restaurant', 'Cafe Coffee Day'],
                'amount_range': (150, 800),
                'frequency': 'high',  # 20-25 times per month
                'transactions_per_month': (20, 25)
            },
            'transport': {
                'category': 'transport',
                'expense_type': 'variable_essential',
                'merchants': ['Uber', 'Ola', 'Metro Card Recharge', 'Petrol Pump', 'Rapido'],
                'amount_range': (50, 500),
                'frequency': 'high',
                'transactions_per_month': (15, 20)
            },
            'entertainment': {
                'category': 'entertainment',
                'expense_type': 'discretionary',
                'merchants': ['Netflix', 'Amazon Prime', 'BookMyShow', 'PVR Cinemas', 'Spotify'],
                'amount_range': (200, 1500),
                'frequency': 'medium',
                'transactions_per_month': (8, 12)
            },
            'shopping': {
                'category': 'shopping',
                'expense_type': 'discretionary',
                'merchants': ['Amazon', 'Flipkart', 'Myntra', 'Ajio', 'Decathlon', 'Lifestyle'],
                'amount_range': (500, 3000),
                'frequency': 'medium',
                'transactions_per_month': (5, 8)
            },
            'bills': {
                'category': 'bills',
                'expense_type': 'fixed',
                'merchants': ['Electricity Bill', 'Water Bill', 'Internet Bill', 'Mobile Recharge'],
                'amount_range': (500, 2000),
                'frequency': 'monthly',
                'transactions_per_month': (3, 4)
            },
            'subscriptions': {
                'category': 'subscriptions',
                'expense_type': 'fixed',
                'merchants': ['Netflix', 'Amazon Prime', 'Spotify Premium', 'YouTube Premium', 'Gym Membership'],
                'amount_range': (199, 999),
                'frequency': 'monthly',
                'transactions_per_month': (2, 3)
            },
            'healthcare': {
                'category': 'healthcare',
                'expense_type': 'variable_essential',
                'merchants': ['Apollo Pharmacy', 'MedPlus', '1mg', 'Local Clinic', 'Diagnostic Center'],
                'amount_range': (200, 1500),
                'frequency': 'low',
                'transactions_per_month': (2, 4)
            },
        }
        
        # Generate transactions month by month
        current_date = start_date
        
        while current_date <= end_date:
            month_start = current_date.replace(day=1)
            
            # Get the last day of the month
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
            
            # Ensure we don't go beyond end_date
            if month_end > end_date:
                month_end = end_date
            
            self.stdout.write(f'\nGenerating transactions for {month_start.strftime("%B %Y")}...')
            
            # Generate transactions for each category
            for template_name, template in transaction_templates.items():
                if template['frequency'] == 'monthly':
                    # Fixed monthly transactions
                    if 'day_of_month' in template:
                        transaction_date = month_start.replace(day=template['day_of_month'])
                    else:
                        num_transactions = random.randint(*template['transactions_per_month'])
                        for _ in range(num_transactions):
                            transaction_date = month_start + timedelta(days=random.randint(0, (month_end - month_start).days))
                            
                            amount = Decimal(str(random.uniform(*template['amount_range']))).quantize(Decimal('0.01'))
                            merchant = random.choice(template['merchants'])
                            
                            Transaction.objects.create(
                                user=user,
                                amount=amount,
                                date=transaction_date,
                                merchant_name=merchant,
                                category=template['category'],
                                expense_type=template['expense_type'],
                                transaction_source=random.choice(['upi', 'card', 'bank']),
                                description=f'{merchant} payment'
                            )
                            transactions_created += 1
                    
                    if transaction_date <= month_end:
                        amount = Decimal(str(random.uniform(*template['amount_range']))).quantize(Decimal('0.01'))
                        merchant = random.choice(template['merchants'])
                        
                        Transaction.objects.create(
                            user=user,
                            amount=amount,
                            date=transaction_date,
                            merchant_name=merchant,
                            category=template['category'],
                            expense_type=template['expense_type'],
                            transaction_source=random.choice(['upi', 'card', 'bank']),
                            description=f'{merchant} payment'
                        )
                        transactions_created += 1
                
                else:
                    # Variable frequency transactions
                    num_transactions = random.randint(*template['transactions_per_month'])
                    
                    for _ in range(num_transactions):
                        # Random date within the month
                        days_in_month = (month_end - month_start).days
                        random_day = random.randint(0, days_in_month)
                        transaction_date = month_start + timedelta(days=random_day)
                        
                        if transaction_date > end_date:
                            continue
                        
                        # Random amount with some volatility
                        base_amount = random.uniform(*template['amount_range'])
                        # Add 10% volatility for some categories
                        if template['category'] in ['entertainment', 'shopping']:
                            volatility = random.uniform(-0.1, 0.3)
                            amount = base_amount * (1 + volatility)
                        else:
                            amount = base_amount
                        
                        amount = Decimal(str(amount)).quantize(Decimal('0.01'))
                        merchant = random.choice(template['merchants'])
                        
                        Transaction.objects.create(
                            user=user,
                            amount=amount,
                            date=transaction_date,
                            merchant_name=merchant,
                            category=template['category'],
                            expense_type=template['expense_type'],
                            transaction_source=random.choice(['upi', 'card', 'bank', 'cash']),
                            description=f'{merchant} payment'
                        )
                        transactions_created += 1
            
            # Add a few anomalies (one-time large expenses)
            if random.random() > 0.7:  # 30% chance per month
                anomaly_date = month_start + timedelta(days=random.randint(5, 25))
                if anomaly_date <= end_date:
                    anomaly_categories = ['healthcare', 'shopping', 'other']
                    anomaly_category = random.choice(anomaly_categories)
                    anomaly_merchants = {
                        'healthcare': ['Hospital Emergency', 'Dental Clinic', 'Eye Care Center'],
                        'shopping': ['Electronics Store', 'Furniture Store', 'Appliance Store'],
                        'other': ['Home Repair', 'Car Service', 'Event Expense']
                    }
                    
                    Transaction.objects.create(
                        user=user,
                        amount=Decimal(str(random.uniform(5000, 15000))).quantize(Decimal('0.01')),
                        date=anomaly_date,
                        merchant_name=random.choice(anomaly_merchants[anomaly_category]),
                        category=anomaly_category,
                        expense_type='discretionary',
                        transaction_source='card',
                        description='One-time large expense',
                        is_anomaly=True
                    )
                    transactions_created += 1
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {transactions_created} transactions'))
        self.stdout.write(self.style.SUCCESS(f'✓ Data spans from {start_date} to {end_date}'))
        self.stdout.write(self.style.SUCCESS(f'\n🎉 Seed data generation complete!'))
        self.stdout.write(self.style.SUCCESS(f'\nYou can now login with:'))
        self.stdout.write(self.style.SUCCESS(f'  Username: testuser'))
        self.stdout.write(self.style.SUCCESS(f'  Password: testpass123'))