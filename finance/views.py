from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import datetime

from .models import (
    Transaction,
    UserFinancialProfile,
    BudgetRecommendation
)
from .serializers import (
    TransactionSerializer,
    UserFinancialProfileSerializer,
    BudgetRecommendationSerializer,
    BudgetComparisonSerializer
)
from .services import BudgetCalculationService


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing transactions
    
    list: Get all transactions for the current user
    create: Create a new transaction
    retrieve: Get a specific transaction
    update: Update a transaction
    destroy: Delete a transaction
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return transactions for the current user only"""
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Save transaction with current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent transactions (last 30 days)"""
        from datetime import timedelta
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent_transactions = self.get_queryset().filter(date__gte=thirty_days_ago)
        serializer = self.get_serializer(recent_transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get transactions grouped by category"""
        from django.db.models import Sum, Count
        
        category_summary = self.get_queryset().values('category').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')
        
        return Response(category_summary)


class UserFinancialProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoints for user financial profile
    
    list: Get current user's profile
    update: Update financial profile
    """
    serializer_class = UserFinancialProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return profile for current user only"""
        return UserFinancialProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create profile for current user"""
        profile, created = UserFinancialProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile


class BudgetRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for budget recommendations
    
    list: Get all budget recommendations for current user
    retrieve: Get a specific budget recommendation
    generate: Generate a new budget recommendation
    latest: Get the latest budget recommendation
    compare: Compare budget vs actual spending
    """
    serializer_class = BudgetRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return budget recommendations for current user only"""
        return BudgetRecommendation.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new budget recommendation
        
        Optional body parameter:
        - target_month: "YYYY-MM-DD" format (defaults to next month)
        """
        target_month_str = request.data.get('target_month')
        target_month = None
        
        if target_month_str:
            try:
                target_month = datetime.strptime(target_month_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            service = BudgetCalculationService(request.user)
            budget = service.generate_budget_recommendation(target_month)
            serializer = self.get_serializer(budget)
            
            return Response({
                'message': 'Budget recommendation generated successfully',
                'budget': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to generate budget: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the most recent budget recommendation"""
        latest_budget = self.get_queryset().order_by('-month', '-generated_at').first()
        
        if not latest_budget:
            return Response(
                {'message': 'No budget recommendations found. Generate one first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(latest_budget)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def compare(self, request, pk=None):
        """
        Compare recommended budget vs actual spending
        
        Returns category-wise comparison of budgeted vs actual amounts
        """
        budget = self.get_object()
        
        try:
            service = BudgetCalculationService(request.user)
            comparison = service.compare_budget_vs_actual(budget)
            serializer = BudgetComparisonSerializer(comparison)
            
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': f'Failed to generate comparison: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get a summary of all budget recommendations"""
        budgets = self.get_queryset().order_by('-month')[:6]  # Last 6 months
        
        summary = []
        for budget in budgets:
            summary.append({
                'month': budget.month.strftime('%B %Y'),
                'total_budget': budget.total_recommended_budget,
                'recommended_savings': budget.recommended_savings,
                'generated_at': budget.generated_at
            })
        
        return Response({
            'count': len(summary),
            'budgets': summary
        })