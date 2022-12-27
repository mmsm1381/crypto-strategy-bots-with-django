from django.db import models
from django.contrib import admin


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ExchangeAdmin(admin.ModelAdmin):

    actions = ["get_and_update_markets"]
    readonly_fields = ["markets"]

    def get_and_update_markets(self, request, queryset):
        if len(queryset) == 1:
            queryset[0].get_and_update_markets()
        else:
            raise Exception()
