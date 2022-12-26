from django.contrib import admin

from trading_bot import models as trading_bot_models
from utils import bases as utils_bases


class TabdealAdmin(utils_bases.ExchangeAdmin):
    list_display = [field.name for field in trading_bot_models.Tabdeal._meta.fields]


class CurrencyAdmin(admin.ModelAdmin):
    list_display = [field.name for field in trading_bot_models.Currency._meta.fields]


class MarketAdmin(admin.ModelAdmin):
    list_display = [field.name for field in trading_bot_models.Market._meta.fields]


admin.site.register(trading_bot_models.Tabdeal, TabdealAdmin)
admin.site.register(trading_bot_models.Currency, CurrencyAdmin)
admin.site.register(trading_bot_models.Market, MarketAdmin)



