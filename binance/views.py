from config.settings import client
from django.shortcuts import render
from django.views.generic import TemplateView
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import redirect
import random
from .models import Symbol, SizeConfig

class FuturesView(TemplateView):

    def get(self, request):
        return FuturesView.home(request)

    def home(request, error=None):
        user = request.user
        if not user.is_authenticated:
            return redirect('binance:login')
        symbols = Symbol.objects.filter(is_active=True)
        symbols = [symbol.sym_name for symbol in symbols if user in symbol.users.all()]
        context = {'symbols': symbols}
        if error:
            context['error'] = error
        return render(request, 'binance/futures/main.html', context)

class FuturesSendOrderView(TemplateView):

    def post(self, request):
        """
        It takes the data from the form, converts it to JSON,
        and sends it to the trade server
        
        :param request: The request object
        :return: The response is being returned.
        """
        user = request.user
        data = request.POST.dict()
        del data['csrfmiddlewaretoken']
        # return JsonResponse(self.get_order_size_config())
        sym_name = data['symbol']
        symbol = Symbol.objects.filter(sym_name=sym_name)
        if not symbol:
            return FuturesView.home(request, error=f'{sym_name} is invalid Symbol.')
        symbol = symbol[0]
        if not user in symbol.users.all() or symbol.is_active == False:
            return FuturesView.home(request, error=f'Symbol:{symbol} is not allowed for you.')
        # if response.status_code != 200:
        #     return render(request, 'binance/futures/main.html',
        #                   {'error': response.text})
        # else:
        #     return render(request, 'binance/futures/response_order.html', {
        #         'response': response.text,
        #         'message': 'Order sent successfully'
        #     })

    @staticmethod
    def get_stop_orders_input(data):
        orders = []
        i = 1
        while True:
            if f'stop_price{i}' not in data:
                break
            stop_price = data[f'stop_price{i}']
            quantity = data[f'stop_percent{i}']
            orders.append({
                'stopPrice': stop_price,
                'quantity': quantity,
            })
            i += 1
        return orders

    @staticmethod
    def get_order_size_config():
        size_config = SizeConfig.objects.first()
        if not size_config:
            raise Exception('SizeConfig not set.')
        return model_to_dict(size_config)

    @staticmethod
    def send_order(request, symbol, side, type, quantity=None):
        if not quantity:
            Size_config = FuturesSendOrderView.get_order_size_config()
            asset = Size_config['trade_wallet_percent'] * Size_config['margin'] / 100
            price = FuturesSendOrderView.get_price(symbol)
            quantity = FuturesSendOrderView.round(3, asset / price)
        clientOrderId = request.user.username + str(FuturesSendOrderView.generate_random_order_id())
        data = {
            'symbol': symbol,
            'side': side,
            'type': type,
            'quantity': quantity,
            'newClientOrderId': clientOrderId,
        }
        try:
            response = client.futures_create_order(**data)
        except Exception as e:
            return FuturesView.home(request, error=str(e))
        return response

    @staticmethod
    def get_price(symbol):
        return float(client.get_symbol_ticker(symbol=symbol)['price'])

    @staticmethod
    def round(step_size, value):
        return int(value * 10**step_size) / 10**step_size

    @staticmethod
    def generate_random_order_id():
        return str(random.randint(1000000000, 9999999999))

    def get_orders(self, username):
        """
        Get all orders for the user
        :param request: The request object
        :return: The response is being returned.
        """
        orders = client.futures_get_open_orders()
        orders = [order for order in orders if order['clientOrderId'].startswith(username)]
        return orders