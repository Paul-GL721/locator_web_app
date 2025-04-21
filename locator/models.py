from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.urls import reverse
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.utils import timezone


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


# manager for the custom employee abstract model
class LocAppUserManager(BaseUserManager):
    def create_user(self, telephone_Number, password=None,):
        """
        Creates and saves a User with a telephone_Number and password.
        """
        if not telephone_Number:
            raise ValueError('Users must have a username')

        locuser = self.model(
            telephone_Number=telephone_Number,
        )

        locuser.set_password(password)
        locuser.save(using=self._db)
        return locuser

    def create_superuser(self, telephone_Number, password=None):
        """
        Creates and saves a superuser.
        """
        superuser = self.model(
            telephone_Number=telephone_Number,
            password=password,
        )

        superuser.is_admin = True
        superuser.save(using=self._db)
        return superuser


class LocAppUser(AbstractUser):  # Inherits from the default user model
    locuser_id = models.AutoField(primary_key=True)
    telephone_Number = models.CharField(
        max_length=200, unique=True, help_text='Contact Number of the employee')
    Last_modified = models.DateTimeField(blank=True, null=True, auto_now=True)

    objects = LocAppUserManager()
    REQUIRED_FIELDS = ['telephone_Number']

    def __str__(self):
        return f'{self.first_name}, {self.last_name}'


# model to store locations
class LocAppPositions(models.Model):
    # fields
    LocAppPos_id = models.AutoField(primary_key=True)
    LocAppPos_Date = models.DateField(
        help_text='Date the position was captured')
    LocAppPos_user = models.ForeignKey(
        'LocAppUser', on_delete=models.CASCADE, related_name='lociposition')
    LocAppPos_user_group = models.ForeignKey(
        'LocAppGroups', on_delete=models.CASCADE, related_name='locgruposition')
    LocAppPos_timestamp = models.TimeField(
        help_text='Time the reading was taken in HH:MM:SS')
    LocAppPos_latitude = models.FloatField(
        default=0, help_text='Latitude in decimal degrees from GPS')
    LocAppPos_longitude = models.FloatField(
        default=0, help_text='Longitude in decimal degrees captured from GPS')
    LocAppPos_accuracy = models.FloatField(
        default=0, help_text='Accuracy of latitude and Longitude in metres')
    server_Captured_on = models.DateTimeField(
        blank=False, auto_now_add=True, help_text='Date and time data was input in the server')
    Last_modified = models.DateTimeField(
        blank=False, auto_now=True, help_text='Date and time data was last updated in the server')
    offline_Captured_on = models.DateTimeField(
        blank=True, null=True, help_text='Date and Time the data was locally captured')
    offline_pkid = models.CharField(
        blank=True, null=True, max_length=20, help_text='Offline primary_key')

    # Meta
    class Meta:
        ordering = ['LocAppPos_Date']

    # Methods
    def __str__(self):
        return str(self.LocAppPos_id)

    def get_absolute_url(self):
        return reverse('position-detail', args=[str(self.LocAppPos_id)])

# model to store LocAppgroups of user, who share the same tracking poistions


class LocAppGroups(models.Model):
    # Fields
    LocAppGrp_id = models.AutoField(primary_key=True)
    LocAppGrp_name = models.CharField(
        blank=False, max_length=200, help_text='Enter Group name')
    LocAppGrp_address = models.TextField(
        blank=True, null=True, max_length=60, help_text='Enter Group address')
    LocAppGrp_user = models.ManyToManyField('LocAppUser', through='LocAppGrpStatus', through_fields=(
        'LocAppGrp_Fkeyid', 'locuser_Fkeyid'), related_name='locigroup')
    LocAppGrp_description = models.TextField(
        blank=True, null=True, max_length=150, help_text='Decribe your company')
    LocAppGrp_code = models.CharField(
        max_length=10, help_text='Code to uniquely indentify group', unique=True, blank=True)
    server_Captured_on = models.DateTimeField(
        blank=False, auto_now_add=True, help_text='Date and time data was input in the server')
    Last_modified = models.DateTimeField(blank=True, auto_now=True)

    # Meta
    class Meta:
        ordering = ['LocAppGrp_name']

    # Methods
    def __str__(self):
        return f'{self.LocAppGrp_name}'


class LocAppGrpStatus(models.Model):
    grpstatus_id = models.AutoField(primary_key=True)
    LocAppGrp_Fkeyid = models.ForeignKey(
        LocAppGroups, on_delete=models.CASCADE, related_name='statusgrps')
    locuser_Fkeyid = models.ForeignKey(
        LocAppUser, on_delete=models.CASCADE, related_name='statuser')
    useradmin = models.BooleanField(
        help_text='Choose whether the user is a group admin or not')

    # Meta
    class Meta:
        ordering = ['grpstatus_id']

    # Methods
    def __str__(self):
        return (self.useradmin)


class QRLoginSession(models.Model):
    session_token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey('LocAppUser', null=True,
                             blank=True, on_delete=models.CASCADE)
    is_authenticated = models.BooleanField(default=False)

    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 120  # 2 minutes
