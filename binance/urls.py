from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = 'binance'

urlpatterns = [
    path('futures/', views.FuturesView.as_view(), name='home'),
    path('futures/send_order/', views.FuturesSendOrderView.as_view(), name='futures_send_order'),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]




# urlpatterns = [
#     path(
#         "password_change/", views.PasswordChangeView.as_view(), name="password_change"
#     ),
#     path(
#         "password_change/done/",
#         views.PasswordChangeDoneView.as_view(),
#         name="password_change_done",
#     ),
#     path("password_reset/", views.PasswordResetView.as_view(), name="password_reset"),
#     path(
#         "password_reset/done/",
#         views.PasswordResetDoneView.as_view(),
#         name="password_reset_done",
#     ),
#     path(
#         "reset/<uidb64>/<token>/",
#         views.PasswordResetConfirmView.as_view(),
#         name="password_reset_confirm",
#     ),
#     path(
#         "reset/done/",
#         views.PasswordResetCompleteView.as_view(),
#         name="password_reset_complete",
#     ),
# ]
