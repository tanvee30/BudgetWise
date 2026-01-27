from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransactionViewSet,
    UserFinancialProfileViewSet,
    BudgetRecommendationViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'profile', UserFinancialProfileViewSet, basename='profile')
router.register(r'budgets', BudgetRecommendationViewSet, basename='budget')

urlpatterns = [
    path('', include(router.urls)),
]