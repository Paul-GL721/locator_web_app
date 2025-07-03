from django.shortcuts import get_object_or_404, render
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
from django.db.models import F, Max, Value
from django.db.models.functions import Concat
from django.db.models import CharField
from django.contrib.auth import login
from django.utils.http import urlencode
import time
import datetime
from django.views import View
from django.views.generic import ListView
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
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


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
            'LocAppGrp_id', 'LocAppGrp_name', 'LocAppGrp_code').order_by('-LocAppGrp_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_groups'] = self.get_user_groups()
        return context


class GetUsersinaGroupView(View):
    '''
    Get users that belong to a given group
    '''

    def get(self, request, *args, **kwargs):
        grpid = request.GET.getlist('groupId')
        # print(f'group id is {grpid}')
        try:
            users = LocAppGrpStatus.objects.filter(LocAppGrp_Fkeyid__LocAppGrp_code__in=grpid).annotate(
                userid=F("locuser_Fkeyid__locuser_id"), usernames=Concat(F(
                    "locuser_Fkeyid__first_name"), Value(" "), F("locuser_Fkeyid__last_name"),
                    output_field=CharField())).values('userid', 'usernames').order_by('userid')
            user_list = list(users)
            # print(f'users list is {user_list}')
            # json for the onchange event
            return JsonResponse({'user_list': user_list})

        except LocAppGrpStatus.DoesNotExist:
            return JsonResponse({'user_list': ''}, status=404)


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
            'usergroupcode': '{usergroupcode}',
            'token': '{token}',
        })

        # Construct shell login URL
        login_url = f"{settings.APP_DOMAIN}/locator/qr-login/?{query_params}"

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


class UsernamePasswdLogin(TemplateView):
    """
    Show a template that allows a user to login with a username and password
    """
    template_name = "authentication/login.html"


@method_decorator(csrf_exempt, name='dispatch')
class CreateUserProfile(View):
    """
    Here we a create a profile for a new user. This is from the mobile application
    """

    def post(self, request):
        data = request.POST
        # 1.get user data from the form
        print(data)
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone = data.get('telephone')
        group_status = data.get('group-status')
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

        user_group = None  # Initialize to avoid UnboundLocalError

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
        elif group_status == "two":  # add user to existing group using an exisiting group code
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

        # get all groups a user belong to
        groups = LocAppGrpStatus.objects.filter(locuser_Fkeyid=user) \
            .select_related('LocAppGrp_Fkeyid') \
            .order_by('-grpstatus_id')  # assumes later grpstatus_id = more recent

        groupdata = [
            {
                'groupname': status.LocAppGrp_Fkeyid.LocAppGrp_name,
                'groupcode': status.LocAppGrp_Fkeyid.LocAppGrp_code,
                'useradmin': status.useradmin
            }
            for status in groups
        ]
        # return user variables to user
        return JsonResponse({
            "token": token.key,
            "userid": user.locuser_id,
            "username": user.username,
            'groups': groupdata,
        })


class QrLoginView(View):
    """
    Handles login when a user on the mobile device scans the QR code
    Expects `userid` and `token` in GET params.
    """

    def get(self, request, *args, **kwargs):
        print("Incoming GET request to qr-login")
        print("GET data:", request.GET)
        print("Headers:", request.headers)

        userid = request.GET.get('userid')
        token = request.GET.get('token')

        print(f"Extracted userid: {userid}")
        print(f"Extracted token: {token}")

        if not userid or not token:
            return HttpResponse("Missing user ID or token", status=400)

        try:
            user = LocAppUser.objects.get(locuser_id=userid)
        except LocAppUser.DoesNotExist:
            return HttpResponse("User not found", status=404)

        try:
            user_token = Token.objects.get(user=user)
        except Token.DoesNotExist:
            return HttpResponse("Token not found", status=403)

        if user_token.key != token:
            return HttpResponse("Invalid token", status=403)

        # Log in the user
        login(request, user)

        # Check if request is from Cordova
        # is_cordova = request.headers.get("X-Cordova-App") == "true"
        is_cordova = request.META.get("HTTP_X_CORDOVA_APP") == "true"

        if is_cordova:
            return JsonResponse({"redirect_url": "after_login.html"})
        else:
            return redirect('after_login')


class TabularPositionReport(UserDetailsMixin, ListView):
    '''
    Get a list of all positions of groups a user belongs to as an admin,
    Allow a user to filter results based on group selection.
    '''
    model = LocAppPositions
    template_name = 'table_report.html'

    def get(self, request, *args, **kwargs):
        # all groups where a user is an admin
        user = self.request.user
        # 1. Groups where the user is admin
        admin_grps = LocAppGroups.objects.filter(
            statusgrps__locuser_Fkeyid=user,
            statusgrps__useradmin=True
        ).distinct()

        # 2. All users in those admin groups
        group_users = LocAppUser.objects.filter(
            locigroup__LocAppGrp_id__in=admin_grps.values_list(
                'LocAppGrp_id', flat=True)
        ).distinct()

        # 3. Get the most recent date in positions table
        latest_date = LocAppPositions.objects.aggregate(Max('LocAppPos_Date'))[
            'LocAppPos_Date__max'] or datetime.date.today()

        # 4. Filter positions: in groups where user is admin, by group users, within 30-day window
        start_date = latest_date - datetime.timedelta(days=30)

        positions = LocAppPositions.objects.filter(
            LocAppPos_user_group__in=admin_grps,
            LocAppPos_user__in=group_users,
            LocAppPos_Date__range=(start_date, latest_date)
        ).select_related('LocAppPos_user', 'LocAppPos_user_group')

        return render(request, self.template_name, {
            'available_groups': admin_grps,
            'available_positions': positions,
            'end_date': latest_date,
            'start_date': start_date,
            'groupname': 'All Groups'
        })

    def post(self, request, *args, **kwargs):
        group_ids = request.POST.getlist('groupIds')
        user_ids = request.POST.getlist('userIds')
        start_date = request.POST.get('fromDate')
        latest_date = request.POST.get('toDate')

        # Parse start date
        try:
            start_date = datetime.datetime.strptime(
                start_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid start date format'}, status=400)

        # Parse end date (fallback to today or 30 days after start)
        try:
            latest_date = datetime.datetime.strptime(
                latest_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            latest_date = start_date + datetime.timedelta(days=30)  # fallback

        # print(f'submitted data are {group_ids} {user_ids} {start_date} {latest_date}')

        positions = LocAppPositions.objects.filter(
            LocAppPos_user_group__LocAppGrp_code__in=group_ids,
            LocAppPos_user__locuser_id__in=user_ids,
            LocAppPos_Date__range=(start_date, latest_date)
        ).select_related('LocAppPos_user', 'LocAppPos_user_group')

        # Get group names for display
        groupname_qs = LocAppGroups.objects.filter(
            LocAppGrp_code__in=group_ids)
        groupname = ", ".join(
            group.LocAppGrp_name for group in groupname_qs) if groupname_qs.exists() else "Selected Groups"

        # print(f'data on post event {groupname} {positions} {start_date} {latest_date}')

        return JsonResponse({
            'table_html': render_to_string('partial_position_table.html', {
                'available_positions': positions,
                'groupname': groupname,
                'start_date': start_date,
                'end_date': latest_date,
            }),
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
        usergroupcode = request.POST.get("usergrp")
        timestamp = int(time.time())
        print(f"group code is {usergroupcode}")
        # Prepare placeholder query parameters
        query_params = urlencode({
            'usergroup': usergroupcode,
            'qr_timestamp': timestamp,
        })

        qr_url = f"{settings.APP_DOMAIN}/locator/generatepositonqr/?{query_params}"

        # Generate QR code
        qr = qrcode.make(qr_url)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        qr_image_data = f"data:image/png;base64,{img_base64}"

        rendered_html = render(request, 'gps_qrcode_partial.html', {
                               'qr_image_data': qr_image_data, }).content.decode('utf-8')
        return JsonResponse({'html': rendered_html}, status=200)


def convert_timestamp_to_fields(timestamp_ms, created_at=None):
    # covert timestamp to seconds from millseconds
    dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0)
    # Extract date and time
    date_part = dt.date()
    time_part = dt.time()

    # remove the z from created at
    if created_at:
        try:
            offline_captured = datetime.datetime.fromisoformat(
                created_at.replace("z", "+00.00"))
        except Exception:
            offline_captured = dt
    else:
        offline_captured = dt
    return date_part, time_part, offline_captured


class mobile_add_newgpsdata(APIView):
    """
    An api to add gps position data from mobile device local storage to the
    remote  server database
    """

    def post(self, request, format=None):
        raw_data = request.data
        print(raw_data)

        if not isinstance(raw_data, list):
            return Response({'error': 'Expected a list of objects'}, status=status.HTTP_400_BAD_REQUEST)

        transformed_data = []

        for item in raw_data:
            try:
                timestamp = item["timestamp"]
                created_at = item.get("created_at")
                date_part, time_part, offline_captured = convert_timestamp_to_fields(
                    timestamp, created_at)

                # lookup groupid
                group_code = item.get('groupcode')
                try:
                    group = LocAppGroups.objects.get(LocAppGrp_code=group_code)
                    group_id = group.LocAppGrp_id
                except LocAppGroups.DoesNotExist:
                    return Response({'error': f'Group with code {group_code} not found.'}, status=status.HTTP_400_BAD_REQUEST)

                # mapping frontend keys to backend field names
                transformed_items = {
                    "LocAppPos_Date": date_part,
                    "LocAppPos_user": item['userid'],
                    "LocAppPos_user_group": group_id,
                    "LocAppPos_timestamp": time_part,
                    "LocAppPos_latitude": item['latitude'],
                    "LocAppPos_longitude": item['longitude'],
                    "LocAppPos_accuracy": item['Accuracy'],
                    "offline_Captured_on": offline_captured,
                    "offline_pkid": item.get('pid'),
                }
                transformed_data.append(transformed_items)
            except KeyError as e:
                return Response({'error': f'Missing field: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LocAppPositionsSerializer(
            data=transformed_data, many=True)

        if serializer.is_valid():
            serializer.save()
            synced_ids = [entry.get(
                "offline_pkid") for entry in transformed_data if entry.get("offline_pkid")]
            return Response({"message": "Data synced successfully", "synced_ids": synced_ids}, status=status.HTTP_201_CREATED)
        else:
            print("Serializer errors:", serializer.errors)
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
        # return all the groups a user belongs to
        groups = LocAppGrpStatus.objects.filter(locuser_Fkeyid=user) \
            .select_related('LocAppGrp_Fkeyid') \
            .order_by('-grpstatus_id')
        groupdata = [
            {
                'groupname': status.LocAppGrp_Fkeyid.LocAppGrp_name,
                'groupcode': status.LocAppGrp_Fkeyid.LocAppGrp_code,
                'useradmin': status.useradmin
            }
            for status in groups
        ]
        token, created = Token.objects.get_or_create(user=user)
        user_id = user.locuser_id
        username = user.username
        return Response({
            'token': token.key,
            'userid': user_id,
            'username': username,
            'groups': groupdata
        })


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
