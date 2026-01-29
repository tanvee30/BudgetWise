from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransactionViewSet,
    UserFinancialProfileViewSet,
    BudgetRecommendationViewSet,
    login_view
)
from .frontend_views import (
    home,
    login_page,
    logout_view,
    dashboard,
    transactions_page,
    budget_page,
    profile_page
)

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'profile', UserFinancialProfileViewSet, basename='profile')
router.register(r'budgets', BudgetRecommendationViewSet, basename='budget')

urlpatterns = [
    # Frontend pages
    path('', home, name='home'),
    path('login/', login_page, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('transactions/', transactions_page, name='transactions'),
    path('budget/', budget_page, name='budget'),
    path('profile/', profile_page, name='profile'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/auth/login/', login_view, name='api_login'),
]