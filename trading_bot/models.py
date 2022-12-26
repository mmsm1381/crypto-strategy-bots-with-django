from django.db import models

from utils import bases as utils_bases


class Currency(utils_bases.BaseModel):
    symbol = models.CharField(max_length=123)

    class Meta:
        verbose_name = "currencies"


class Market(utils_bases.BaseModel):
    first_currency = models.ForeignKey('trading_bot.Currency', on_delete=models.PROTECT,
                                       related_name="first_currencies")
    second_currency = models.ForeignKey('trading_bot.Currency', on_delete=models.PROTECT,
                                        related_name="second_currencies")


class Exchange(utils_bases.BaseModel):
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)
    markets = models.ManyToManyField('trading_bot.Market', related_name="exchanges")

    class Meta:
        abstract = True

    def get_markets(self):
        raise NotImplementedError


class Tabdeal(Exchange):
    pass
