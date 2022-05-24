from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.models import Group, User

from src.api.models import ApiUser

# Register your models here.

def unregister_model(model):
    try:
        admin.site.unregister(model)
    except NotRegistered:
        pass


unregister_model(User)
unregister_model(Group)


@admin.register(ApiUser)
class OfferAdmin(admin.ModelAdmin):
    model = ApiUser
    list_filter = ('email',)
    list_display = ('email', 'password', 'activated', 'created_at')
    search_fields = ('email',)
    ordering = ('email',)