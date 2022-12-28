import traceback
from abc import ABC, abstractmethod
from enum import Enum

from django.db import models

from rest_framework import serializers

from tabdeal.spot import Spot
from tabdeal.enums import OrderSides, OrderTypes

from utils import bases as utils_bases


class BaseExchangeInterFace(ABC):

    def __init__(self, api_key: None, api_secret: None):
        self.api_key = api_key
        self.api_secret = api_secret
        super().__init__()

    @abstractmethod
    def get_client(self):
        raise NotImplementedError

    @abstractmethod
    def get_and_update_markets(self, db_instance):
        raise NotImplementedError

    @abstractmethod
    def submit_order(self, order_dict: dict) -> int:
        raise NotImplementedError

    @abstractmethod
    def update_order_state(self, order_id: int):
        raise NotImplementedError


class Tabdeal(BaseExchangeInterFace):

    def get_client(self):
        return Spot(self.api_key, self.api_secret)

    def get_and_update_markets(self, exchange_db_instance):
        client = self.get_client()
        markets = client.exchange_info()
        markets_id = []
        for market in markets:
            first_currency, _ = Currency.objects.get_or_create(symbol=market['baseAsset'])
            second_currency, _ = Currency.objects.get_or_create(symbol=market['quoteAsset'])
            markets_id.append(
                Market.objects.get_or_create(first_currency=first_currency,
                                             second_currency=second_currency)[0].id)
        exchange_db_instance.markets.add(*markets_id)

    def submit_order(self, order_dict: dict) -> int:
        client = self.get_client()
        order_side = OrderSides.SELL if order_dict.get(
            "side") == Order.Side.Sell.value else OrderSides.BUY
        market = Market.objects.get(id=order_dict.get("market"))
        order = client.new_order(
            symbol=f"{market.first_currency}{market.second_currency}",
            side=order_side,
            type=OrderTypes.LIMIT,
            quantity=order_dict.get("amount"),
            price=order_dict.get("price")
        )
        return int(order['orderId'])

    def update_order_state(self, order_id: int) -> None:
        client = self.get_client()
        db_order = Order.objects.get(id=order_id)
        remote_order = client.get_order(
            symbol=f"{db_order.market.first_currency.symbol}_{db_order.market.second_currency.symbol}",
            order_id=db_order.remote_id
        )
        order_state = remote_order['status']
        if order_state == "NEW":
            db_order.state = Order.State.Waiting.value
        elif order_state == "FILED":
            db_order.state = Order.State.Filled.value
        elif order_state == "PARTIALLY_FILLED":
            db_order.state = Order.State.PartiallyFilled.value
        elif order_state == "PARTIALLY_FILLED_AND_FINISHED":
            db_order.state = Order.State.PartiallyFilledAndFinished.value
        elif order_state == "ERROR":
            db_order.state = Order.State.Error.value
        elif order_state == "CANCELED":
            db_order.state = Order.State.Canceled.value
        else:
            db_order.state = Order.State.Idle.value

        db_order.save(update_fields=["state", "updated"])


class ExchangeProviders(Enum):

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, value: str, exchange_class):
        self._exchange_class = exchange_class

    @property
    def exchange_class(self):
        return self._exchange_class

    Tabdeal = 1, Tabdeal


class Choices:
    exchange_providers = (
        (ExchangeProviders.Tabdeal.value, ExchangeProviders.Tabdeal.name),
    )


class Currency(utils_bases.BaseModel):
    symbol = models.CharField(max_length=123)
    precision = models.IntegerField(default=8)

    class Meta:
        verbose_name = "currencies"

    def __str__(self):
        return self.symbol


class Market(utils_bases.BaseModel):
    first_currency = models.ForeignKey('trading_bot.Currency', on_delete=models.PROTECT,
                                       related_name="first_currencies")
    second_currency = models.ForeignKey('trading_bot.Currency', on_delete=models.PROTECT,
                                        related_name="second_currencies")

    def __str__(self):
        return f"{self.first_currency}@{self.second_currency}"


class Exchange(utils_bases.BaseModel):
    markets = models.ManyToManyField('trading_bot.Market', related_name="exchanges")
    exchange_provider = models.SmallIntegerField(choices=Choices.exchange_providers, unique=True)

    def exchange_interface(self, api_key=None, api_secret=None):
        return ExchangeProviders(self.exchange_provider).exchange_class(api_key=api_key,
                                                                        api_secret=api_secret)

    def get_and_update_markets(self):
        self.exchange_interface().get_and_update_markets(exchange_db_instance=self)

    def submit_order(self, order_dict: dict, account) -> int:
        order_id = self.exchange_interface(api_key=account.api_key, api_secret=account.api_secret).submit_order(
            order_dict)
        return order_id

    def update_order_state(self, order_id: int, account) -> None:
        self.exchange_interface(api_key=account.api_key, api_secret=account.api_secret).update_order_state(
            order_id=order_id
        )

    def __str__(self):
        return ExchangeProviders(self.exchange_provider).name


class Account(utils_bases.BaseModel):
    exchange = models.ForeignKey('trading_bot.Exchange', on_delete=models.PROTECT)
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.id}@{self.exchange}"


class Order(utils_bases.BaseModel):
    class Side(models.IntegerChoices):
        Buy = 1
        Sell = 2

    class State(models.IntegerChoices):
        WaitingToSubmit = 1
        Waiting = 2
        PartiallyFilled = 3
        PartiallyFilledAndFinished = 4
        Filled = 5
        Canceled = 6
        Error = 7
        Idle = 8

        @staticmethod
        def active_states():
            return [Order.State.Waiting.value, Order.State.PartiallyFilled.value]

    exchange = models.ForeignKey('trading_bot.Exchange', on_delete=models.PROTECT)
    grid_bot = models.ForeignKey('trading_bot.GridBot', on_delete=models.PROTECT, related_name="bot_orders")
    account = models.ForeignKey('trading_bot.Account', on_delete=models.PROTECT)
    market = models.ForeignKey('trading_bot.Market', on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=32, decimal_places=8)
    amount = models.DecimalField(max_digits=32, decimal_places=8)
    side = models.SmallIntegerField(choices=Side.choices)
    remote_id = models.PositiveBigIntegerField(null=True, blank=True)
    state = models.SmallIntegerField(choices=State.choices, default=State.WaitingToSubmit.value)
    comments = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ['remote_id', 'exchange']

    def submit_order(self):
        try:
            order_dict = OrderSerializer(instance=self).data
            order_remote_id = self.exchange.submit_order(order_dict=order_dict, account=self.account)
            self.state = Order.State.Waiting.value
            self.remote_id = order_remote_id
            self.save(update_fields=["state", "remote_id", "updated"])
        except Exception as ve:
            self.state = Order.State.Error.value
            self.comments = ve.__str__() + "\n" + str(traceback.format_exc()) + "\n"
            self.save(update_fields=["state", 'comments', 'updated'])

    def update_order_state(self):
        self.exchange.update_order_state(order_id=self.id, account=self.account)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["price", "amount", "side", "market"]


class Trade(utils_bases.BaseModel):
    order = models.ForeignKey('trading_bot.Order', on_delete=models.PROTECT)


class Bot(utils_bases.BaseModel):
    account = models.ForeignKey('trading_bot.Account', on_delete=models.PROTECT)
    market = models.ForeignKey('trading_bot.Market', on_delete=models.PROTECT)
    investment = models.DecimalField(max_digits=32, decimal_places=8)

    def __str__(self):
        return f"{self.account}-{self.market}"


class GridBot(Bot):
    no_grid_lines = models.IntegerField()
    upper_price = models.DecimalField(max_digits=32, decimal_places=8)
    lower_price = models.DecimalField(max_digits=32, decimal_places=8)
    active = models.BooleanField(default=True)

    @property
    def position_distance(self):
        return (self.upper_price - self.lower_price) / self.no_grid_lines

    @property
    def position_value(self):
        return self.investment / (self.no_grid_lines // 2)

    def create_orders(self):
        orders_list = []
        for i in range(self.no_grid_lines // 2):
            price = self.lower_price + (i * self.position_distance)
            orders_list.append(Order(
                side=Order.Side.Buy.value,
                price=price,
                amount=round(self.position_value / price, self.market.first_currency.precision),
                grid_bot=self,
                exchange=self.account.exchange,
                account=self.account,
                market=self.market
            ))
        Order.objects.bulk_create(objs=orders_list)

    def check_and_update_order_state_and_create_new_order_if_needed(self):
        bot_orders = self.bot_orders.exclude(state__in=Order.State.active_states())
        for order in bot_orders:
            order.update_order_state()
            order.refresh_from_db()
            if order.state in [Order.State.Filled.value, Order.State.PartiallyFilled.value] and order.trade is None:
                pass



    def deactivate(self):
        raise NotImplementedError
