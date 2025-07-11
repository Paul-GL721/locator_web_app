from django.urls import path
from .views import *

urlpatterns = [
    # web urls
    path('', index_page.as_view(), name="index_page"),
    path('locator/', index_page.as_view(), name="index_page_indexed"),
    path("afterlogin/", after_login.as_view(), name="after_login"),
    path("getuserspergroup/", GetUsersinaGroupView.as_view(), name="users_in_group"),
    path("usernamepasswd/", UsernamePasswdLogin.as_view(),
         name="username_passwd_login"),
    path("adduser/", add_user.as_view(), name="add_user"),
    path("generatepositonqr/", GenerateQRCodeView.as_view(), name="generate_qr"),
    path("qr-login/", QrLoginView.as_view(), name='qr_login'),
    # path("open-app/", OpenAppRedirectView.as_view(), name="open_app_redirect"),
    # path("login-generate-qr/", QRLoginGenerateView.as_view(), name="generate_qr"),
    # path("check-qr-login-status/<str:session_token>/", check_qr_login_status, name="qr_login_check"),
    # path("api/qr-login-authenticate/",QRLoginAuthenticateView.as_view(), name="qr_authenticate"),

    # Reports
    path("tablereport/", TabularPositionReport.as_view(), name="tabular_report"),



    # mobile urls
    path('mobile/newgpsdata/', mobile_add_newgpsdata.as_view(),
         name='add_newgpsdata'),
    path("mobile/createuserprofile/", CreateUserProfile.as_view(),
         name="create_user_profile"),


    # mobile authentication
    # path('api-token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),
]
