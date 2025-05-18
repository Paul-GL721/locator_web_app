from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from .models import *


# serializer for the app-user model
class LocAppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocAppUser
        fields = ['locuser_id', 'telephone_Number', 'Last_modified',]


# serializer for the app-user-group model
class LocAppGroupsSerializer(serializers.ModelSerializer):
    LocAppGrp_user = LocAppUserSerializer(many=True)

    class Meta:
        model = LocAppUser
        fields = ['LocAppGrp_id', 'LocAppGrp_name', 'LocAppGrp_address',
                  'LocAppGrp_description', 'server_Captured_on', 'Last_modified', 'LocAppGrp_user']


# serializer for the position model
class LocAppPositionsSerializer(serializers.ModelSerializer):
    LocAppPos_user = serializers.PrimaryKeyRelatedField(
        queryset=LocAppUser.objects.all())
    LocAppPos_user_group = serializers.PrimaryKeyRelatedField(
        queryset=LocAppGroups.objects.all())

    class Meta:
        model = LocAppPositions
        fields = ['LocAppPos_id', 'LocAppPos_Date', 'LocAppPos_timestamp', 'LocAppPos_latitude', 'LocAppPos_longitude',  'LocAppPos_accuracy',
                  'server_Captured_on', 'Last_modified', 'offline_Captured_on', 'offline_pkid', 'LocAppPos_user', 'LocAppPos_user_group']
