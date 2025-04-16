from django.shortcuts import render
from .models import *
from .serializers import *
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken


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
