from django.db import models
from django.contrib import admin


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ExchangeAdmin(admin.ModelAdmin):
    readonly_fields = ["markets"]
