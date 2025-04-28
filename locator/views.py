from django.shortcuts import render
from .models import *
from .serializers import *
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.contrib.auth import login
from django.utils.http import urlencode
import time
from django.views import View
from django.views.generic.base import TemplateView
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
import io
import qrcode
import secrets
import base64
from urllib.parse import urlencode
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string




class UserDetailsMixin:
    """
    Mixin that returns user details[userid, username, usergroups ]
    """    
    def get_user_groups(self):
        '''
        get groups a user belongs to
        '''
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied('You Must be Logged in')
        return LocAppGroups.objects.filter(statusgrps__locuser_Fkeyid=user).values(
            'LocAppGrp_id', 'LocAppGrp_name').order_by('-LocAppGrp_id')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_groups'] = self.get_user_groups()
        return context


class index_page(TemplateView):
    """
    Display the indexpage/ landing page, with a QRcode that will allow the user 
    to login from their mobile application 
    """
    template_name = "indexpage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Prepare placeholder query parameters
        query_params = urlencode({
            'userid': '{userid}',
            'username': '{username}',
            'usergroup': '{usergroup}',
            'token': '{token}',
        })

        # Construct shell login URL
        login_url = f"{settings.APP_DOMAIN}/qr-login/?{query_params}"

        # Generate QR code
        qr = qrcode.make(login_url)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        qr_image_data = f"data:image/png;base64,{img_base64}"

        # Add QR code to template context
        context["qr_image"] = qr_image_data
        return context


class after_login(TemplateView):
    """
    After login display this template
    """
    template_name = "after_login.html"


class add_user(TemplateView):
    """
    Allow an existing user to add a user to the same group
    """
    template_name = "add_user.html"


class CreateUserProfile(View):
    """
    Here we a create a profile for a new user. This is from the mobile application
    """

    def post(self, request):
        data = request.POST
        # 1.get user data from the form
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone = data.get('telephone')
        group_status = data.get('group_status')
        group_code = data.get('group_code')
        # generated variables
        gen_username = first_name
        user_password = make_password(phone)

        # generate a unique code for each group
        def generate_unique_group_code(length=6):
            while True:
                code = get_random_string(length).upper()
                if not LocAppGroups.objects.filter(LocAppGrp_code=code).exists():
                    return code

        # 2. create the user
        user = LocAppUser.objects.create(
            first_name=first_name,
            last_name=last_name,
            telephone_Number=phone,
            username=gen_username,
            password=user_password,
        )

        # 3. Add a user to a group
        if group_status == "one":
            group_name = f"{first_name}'s Group"
            group_desc = f"This group was created by {first_name} {last_name}"
            group_code_generated = generate_unique_group_code()
            # create user grp
            user_group = LocAppGroups.objects.create(
                LocAppGrp_name=group_name,
                LocAppGrp_description=group_desc,
                LocAppGrp_code=group_code_generated,
            )
            # create user status as admin
            LocAppGrpStatus.objects.create(
                LocAppGrp_Fkeyid=user_group,
                locuser_Fkeyid=user,
                useradmin=True
            )
        elif group_status == "two": #add user to existing group using an exisiting group code
            try:
                user_group = LocAppGroups.objects.get(
                    LocAppGrp_code=group_code)
                # create user WITHOUT admin status
                LocAppGrpStatus.objects.create(
                    LocAppGrp_Fkeyid=user_group,
                    locuser_Fkeyid=user,
                    useradmin=False
                )
            except LocAppGroups.DoesNotExist:
                return JsonResponse({"error": "Group doesnot exist"}, status=404)

        # 4. generate token
        token, _ = Token.objects.get_or_create(user=user)
        # return user variables to user
        return JsonResponse({
            "token": token.key,
            "userid": user.locuser_id,
            "username": user.username,
            "groupname": user_group.LocAppGrp_name if user_group else None,
            "groupcode": user_group.LocAppGrp_code if user_group else None,
        })

class GenerateQRCodeView(UserDetailsMixin, View):
    '''
    Generate QRcode which when scanned picks the GPS location of the user
    '''
    template_name = 'gps_qrcode.html'

    def get(self, request, *args, **kwargs):
        available_groups = self.get_user_groups()
        return render(request, self.template_name, {
            'available_groups': available_groups,
        })
        
    def post(self, request, *args, **kwargs):
        usergroup = request.POST.get("usergrp")
        timestamp = int(time.time())
        # Prepare placeholder query parameters
        query_params = urlencode({
            'usergroup': usergroup,
            'qr_timestamp': timestamp,
        })

        qr_url = f"{settings.APP_DOMAIN}/generatepositonqr/?{query_params}"

        # Generate QR code
        qr = qrcode.make(qr_url)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        qr_image_data = f"data:image/png;base64,{img_base64}"

        # Now render a partial HTML
        html = render_to_string('gps_qrcode_partial.html', {
            'qr_image_data': qr_image_data,
        })

        return JsonResponse({'html': html})


class mobile_add_newgpsdata(APIView):
    """
    An api to add gps position data from mobile device local storage to the
    remote  server database
    """

    def post(self, request, format=None):
        serializer = LocAppPositionsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomAuthToken(ObtainAuthToken):

    '''
    Add the username and userid to the token when the user logins.
    Used to track the user issuing invoices and receipts and the mobile client
    '''

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        user_id = user.locuser_id
        username = user.telephone_Number
        return Response({'token': token.key, 'user_id': user_id, 'username': username})


class OpenAppRedirectView(View):
    '''
    check if the user is scaning from the installed app, if not, give them the option
    to install from the play stores.
    '''

    def get(self, request, *args, **kwargs):
        unit_id = request.GET.get("unit_id", "123")
        timestamp = int(time.time())
        query = urlencode({"unit_id": unit_id, "timestamp": timestamp})

        # Mobile deep link (used by your app)
        app_link = f"myapp://activate?{query}"

        # Fallback URLs
        android_store = "https://play.google.com/store/apps/details?id=com.yourapp"
        ios_store = "https://apps.apple.com/app/id123456789"

        # HTML with JS redirect to app, and fallback if app is not installed
        html = f"""
        <html>
        <head>
            <title>Opening App...</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script>
                setTimeout(function() {{
                    window.location.href = "{android_store}";
                }}, 2000);

                window.location.href = "{app_link}";
            </script>
        </head>
        <body>
            <p>If you are not redirected, <a href="{android_store}">install the app</a>.</p>
        </body>
        </html>
        """
        return HttpResponse(html)

class QRLoginGenerateView(View):
    '''
    Generate a QRcode that a user will scan to login
    '''

    def get(self, request):
        session_token = secrets.token_urlsafe(32)
        QRLoginSession.objects.create(session_token=session_token)

        qr_url = f"https://yourdomain.com/qr-login/?session_token={session_token}"
        img = qrcode.make(qr_url)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return HttpResponse(buffer.getvalue(), content_type="image/png")


class QRLoginAuthenticateView(APIView):
    '''
    API to validate sessions
    '''
    permission_classes = [IsAuthenticated]  # Validates mobile token

    def post(self, request):
        session_token = request.data.get("session_token")
        if not session_token:
            return Response({"error": "Missing session_token"}, status=400)

        try:
            qr_session = QRLoginSession.objects.get(
                session_token=session_token)
        except QRLoginSession.DoesNotExist:
            return Response({"error": "Invalid token"}, status=404)

        if qr_session.is_expired():
            return Response({"error": "Token expired"}, status=410)

        qr_session.user = request.user
        qr_session.is_authenticated = True
        qr_session.save()

        return Response({"message": "Session authenticated"})


def check_qr_login_status(request, session_token):
    try:
        qr_session = QRLoginSession.objects.get(session_token=session_token)
    except QRLoginSession.DoesNotExist:
        return JsonResponse({"authenticated": False})

    if qr_session.is_authenticated and qr_session.user:
        login(request, qr_session.user)
        qr_session.delete()  # Clean up used session
        return JsonResponse({"authenticated": True})

    return JsonResponse({"authenticated": False})
