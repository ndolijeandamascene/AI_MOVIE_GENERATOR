from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """
    Profile to extend the default User model with Phase 2 attributes
    such as Stripe billing references and YouTube channel linkages.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_premium = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    
    # YouTube channel reference synced from Google OAuth
    youtube_channel_id = models.CharField(max_length=100, blank=True, null=True)
    youtube_channel_name = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

from allauth.account.signals import user_logged_in

@receiver(user_logged_in)
def fetch_youtube_data_on_login(sender, request, user, **kwargs):
    """
    On login (specifically social login), attempt to fetch their YouTube channel
    metadata and sync it with their UserProfile.
    """
    try:
        from allauth.socialaccount.models import SocialAccount
        from movies.services.youtube import fetch_youtube_channel_metadata
        
        # Check if they have a Google social account
        if SocialAccount.objects.filter(user=user, provider='google').exists():
            meta = fetch_youtube_channel_metadata(user)
            if meta:
                user.profile.youtube_channel_id = meta['channel_id']
                user.profile.youtube_channel_name = meta['title']
                user.profile.save()
    except Exception as e:
        print(f"Signal exception - Failed to fetch YouTube data: {e}")
