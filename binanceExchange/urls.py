from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = 'binance'

urlpatterns = [
    path('futures/', views.FuturesView.as_view(), name='home'),
    path('futures/send_order/', views.FuturesSendOrderView.as_view(), name='futures_send_order'),
    path('futures/cancel_order/<str:symbol>/<str:orderId>/', views.FuturesSendOrderView.cancel_order, name='futures_cancel_order'),
    path('futures/close_position/<str:symbol>/', views.FuturesSendOrderView.close_position, name='futures_close_position'),
    path('futures/test/', views.FuturesSendOrderView.test, name='futures_test'),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
