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
            'uid': '{uid}',
            'username': '{username}',
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


class GenerateQRCodeView(View):
    '''
    Generate QRcode which when scanned picks the GPS location of the user
    '''

    def get(self, request, *args, **kwargs):
        unit_id = request.GET.get("unit_id", "123")
        timestamp = int(time.time())
        query = urlencode({"unit_id": unit_id, "timestamp": timestamp})
        qr_url = f"https://yourdomain.com/open-app?{query}"

        img = qrcode.make(qr_url)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer.getvalue(), content_type="image/png")


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
