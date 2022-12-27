from django.contrib import admin

from trading_bot import models as trading_bot_models
from utils import bases as utils_bases


class ExchangeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in trading_bot_models.Exchange._meta.fields]


class CurrencyAdmin(admin.ModelAdmin):
    list_display = [field.name for field in trading_bot_models.Currency._meta.fields]


class MarketAdmin(admin.ModelAdmin):
    list_display = [field.name for field in trading_bot_models.Market._meta.fields]


class GridBotAdmin(admin.ModelAdmin):
    list_display = [field.name for field in trading_bot_models.GridBot._meta.fields]
    actions = ['create_orders_for_bots']

    def create_orders_for_bots(self, request, queryset):
        for bot in queryset:
            bot.create_orders()


class OrderAdmin(admin.ModelAdmin):
    list_display = [field.name for field in trading_bot_models.Order._meta.fields]
    actions = ["submit_order"]

    def submit_order(self, request, queryset):
        for order in queryset:
            order.submit_order()


class AccountAdmin(admin.ModelAdmin):
    list_display = [field.name for field in trading_bot_models.Account._meta.fields]


admin.site.register(trading_bot_models.Exchange, ExchangeAdmin)
admin.site.register(trading_bot_models.Currency, CurrencyAdmin)
admin.site.register(trading_bot_models.Market, MarketAdmin)
admin.site.register(trading_bot_models.GridBot, GridBotAdmin)
admin.site.register(trading_bot_models.Account, AccountAdmin)
admin.site.register(trading_bot_models.Order, OrderAdmin)
