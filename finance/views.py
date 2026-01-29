from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def login_view(request):
    """
    Simple login endpoint for testing
    
    POST /api/auth/login/
    Body: {"username": "testuser", "password": "testpass123"}
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user:
        login(request, user)
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    else:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@method_decorator(csrf_exempt, name='dispatch')
class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing transactions
    """
    serializer_class = TransactionSerializer
    permission_classes = []
    
    def get_queryset(self):
        """Return transactions for the current user only"""
        if not self.request.user.is_authenticated:
            return Transaction.objects.none()
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Save transaction with current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent transactions (last 30 days)"""
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=401)
            
        from datetime import timedelta
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent_transactions = self.get_queryset().filter(date__gte=thirty_days_ago)
        serializer = self.get_serializer(recent_transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get transactions grouped by category"""
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=401)
            
        from django.db.models import Sum, Count
        
        category_summary = self.get_queryset().values('category').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')
        
        return Response(category_summary)


@method_decorator(csrf_exempt, name='dispatch')
class UserFinancialProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoints for user financial profile
    """
    serializer_class = UserFinancialProfileSerializer
    permission_classes = []
    
    def get_queryset(self):
        """Return profile for current user only"""
        if not self.request.user.is_authenticated:
            return UserFinancialProfile.objects.none()
        return UserFinancialProfile.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """Override list to return single profile"""
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=401)
            
        profile, created = UserFinancialProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'monthly_income': 50000.00,
                'income_stability_score': 85.0,
                'expense_volatility_score': 0.0,
                'savings_confidence_indicator': 0.0
            }
        )
        serializer = self.get_serializer(profile)
        return Response([serializer.data])
    
    def update(self, request, *args, **kwargs):
        """Update user profile"""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        instance = self.get_object()
        
        if 'monthly_income' in request.data:
            instance.monthly_income = request.data['monthly_income']
            instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class BudgetRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for budget recommendations
    """
    serializer_class = BudgetRecommendationSerializer
    permission_classes = []
    
    def get_queryset(self):
        """Return budget recommendations for current user only"""
        if not self.request.user.is_authenticated:
            return BudgetRecommendation.objects.none()
        return BudgetRecommendation.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new budget recommendation"""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
            
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
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
            
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
        """Compare recommended budget vs actual spending"""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
            
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
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
            
        budgets = self.get_queryset().order_by('-month')[:6]
        
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
    
    @action(detail=False, methods=['get'])
    def adherence(self, request):
        """Get budget adherence score and insights"""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        from .services import calculate_budget_adherence
        
        adherence_data = calculate_budget_adherence(request.user)
        
        if not adherence_data:
            return Response({
                'message': 'No active budget found for current month'
            }, status=404)
        
        return Response(adherence_data)