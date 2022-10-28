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

    def home(request, error=None, message=None):
        user = request.user
        if not user.is_authenticated:
            return redirect('binance:login')
        symbols = Symbol.objects.filter(is_active=True)
        symbols = [symbol.sym_name for symbol in symbols if user in symbol.users.all()]
        try:
            orders = FuturesSendOrderView.get_orders(user=user)
            positions = FuturesSendOrderView.get_positions(user=user)
            context = {'symbols': symbols, 'orders': orders, 'positions': positions, 'error': error, 'message': message}
        except Exception as e:
            context = {'symbols': symbols, 'error': 'Couldnt load positions and orders. Please refresh the page.'}
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
        sym_name = data['symbol']
        symbol = Symbol.objects.filter(sym_name=sym_name)
        if not symbol:
            return FuturesView.home(request, error=f'{sym_name} is invalid Symbol.')
        symbol = symbol[0]
        if (not user in symbol.users.all() or symbol.is_active == False) and not user.is_superuser:
            return FuturesView.home(request, error=f'Symbol:{symbol} is not allowed for you.')
        stop_orders = FuturesSendOrderView.get_stop_orders_input(data)
        side = data.get('side', 'BUY')
        _type = data.get('type', 'MARKET')
        quantity = data.get('quantity', None)
        try:
            response = FuturesSendOrderView.send_order(request, symbol, side, _type, stop_orders, quantity)
        except Exception as e:
            return FuturesView.home(request, error=str(e))
        return FuturesView.home(request, message='Order Successfully Sent!')

    def cancel_order(request, symbol, orderId):
        """
        It takes the data from the form, converts it to JSON,
        and sends it to the trade server
        
        :param request: The request object
        :return: The response is being returned.
        """
        user = request.user
        sym_name = symbol
        symbol = Symbol.objects.filter(sym_name=sym_name)
        if not symbol:
            return FuturesView.home(request, error=f'{sym_name} is invalid Symbol.')
        symbol = symbol[0]
        if (not user in symbol.users.all() or symbol.is_active == False) and not user.is_superuser:
            return FuturesView.home(request, error=f'Symbol:{symbol} is not allowed for you.')
        try:
            client.futures_cancel_order(symbol=sym_name, orderId=orderId)
        except Exception as e:
            return FuturesView.home(request, error=str(e))
        return FuturesView.home(request, message=f'Order:{orderId} cancelled successfully.')

    def close_position(request, symbol):
        """
        It takes the data from the form, converts it to JSON,
        and sends it to the trade server
        
        :param request: The request object
        :return: The response is being returned.
        """
        user = request.user
        if not user.is_authenticated:
            return redirect('binance:login')
        sym_name = symbol
        symbol = Symbol.objects.filter(sym_name=sym_name)
        if not symbol:
            return FuturesView.home(request, error=f'{sym_name} is invalid Symbol.')
        symbol = symbol[0]
        if (not user in symbol.users.all() or symbol.is_active == False) and not user.is_superuser:
            return FuturesView.home(request, error=f'Symbol:{symbol} is not allowed for you.')
        position_info = client.futures_position_information(symbol=symbol)[0]
        if float(position_info['positionAmt']) == 0:
            return FuturesView.home(request, error=f'No position found for {symbol}')
        side = 'BUY' if float(position_info['positionAmt']) < 0 else 'SELL'
        _type = 'MARKET'
        quantity = abs(float(position_info['positionAmt']))
        try:
            FuturesSendOrderView.send_order(request, symbol, side, _type,  [], quantity=quantity, close=True)
        except Exception as e:
            return FuturesView.home(request, error=str(e))
        return FuturesView.home(request, message='Order Successfully Sent!')

    def test(request):
        data = client.get_exchange_info()
        # symbols = [dt['symbol'] for dt in data['symbols']]
        for symbol in data['symbols']:
            sym_name = symbol['symbol']
            for filt in symbol['filters']:
                if filt['filterType'] == 'LOT_SIZE':
                    minQty = float(filt['minQty'])
                    # maxQty = float(filt['maxQty'])
                    stepSize = float(filt['stepSize'])
            sym = Symbol(sym_name=sym_name, is_active=False, min_qty=minQty, step_size=stepSize)
            sym.save()
        return JsonResponse(data['symbols'][0])

    @staticmethod
    def get_stop_orders_input(data):
        orders = []
        i = 1
        while True:
            if f'stop_price{i}' not in data:
                break
            stop_price = data[f'stop_price{i}']
            quantity = data[f'stop_percent{i}'].replace('%', '')
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
    def send_order(request, symbol, side, type, stop_orders, quantity=None, close=False):
        if not quantity:
            Size_config = FuturesSendOrderView.get_order_size_config()
            asset = Size_config['trade_wallet_percent'] * Size_config['margin'] / 100
            price = FuturesSendOrderView.get_price(symbol.sym_name)
            quantity = FuturesSendOrderView.round(FuturesSendOrderView.get_float_step_size(symbol.step_size), asset / price)
        leverage = FuturesSendOrderView.get_order_size_config()['leverage']
        if (quantity*leverage < symbol.min_qty or ((quantity*leverage*10**5) % (symbol.step_size*10**5)) !=0 ) and not close:
            raise Exception(f'Quantity should be greater than {symbol.min_qty} \
                    and should be multiple of {symbol.step_size} for the main order but it is {quantity*leverage}, call admin for help.')
        for stop_order in stop_orders:
            qty = (float(stop_order['quantity'])*leverage)
            if qty < symbol.min_qty or ((qty*10**5) % (symbol.step_size*10**5)) != 0:
                raise Exception(f'Quantity should be greater than {symbol.min_qty} \
                    and should be multiple of {symbol.step_size} for stop orders but it is {qty}, call admin for help.')
        clientOrderId = request.user.username + str(FuturesSendOrderView.generate_random_order_id())
        data = {
            'symbol': symbol.sym_name,
            'side': side,
            'type': type,
            'quantity': quantity,
            'newClientOrderId': clientOrderId,
            'newOrderRespType': 'RESULT',
        }
        response = client.futures_create_order(**data)
        FuturesSendOrderView.send_stop_orders(request, stop_orders, response)
        return 
        

    @staticmethod
    def send_stop_orders(request, stop_orders, data):
        symbol = data['symbol']
        entryPrice = data['avgPrice']
        side = data['side']
        qty = float(data['origQty'])
        for order in stop_orders:
            params = dict()
            # set order type sl or tp
            _type = 'STOP_MARKET' if float(order['stopPrice']) < float(entryPrice) else 'TAKE_PROFIT_MARKET'
            if side == 'SELL':
                if _type == 'STOP_MARKET':
                    _type = 'TAKE_PROFIT_MARKET'
                else:
                    _type = 'STOP_MARKET'
            params['type'] = _type
            params['symbol'] = symbol
            params['side'] = 'SELL' if side == 'BUY' else 'BUY'
            params['stopPrice'] = order['stopPrice']
            quantity = (float(order['quantity']) * qty * 0.01)
            params['quantity'] = FuturesSendOrderView.round(3, quantity)
            params['newClientOrderId'] = request.user.username + str(FuturesSendOrderView.generate_random_order_id())
            client.futures_create_order(**params)
        
    @staticmethod
    def get_price(symbol):
        return float(client.get_symbol_ticker(symbol=symbol)['price'])

    @staticmethod
    def round(step_size, value):
        return int(value * 10**step_size) / 10**step_size

    @staticmethod
    def generate_random_order_id():
        return str(random.randint(1000000000, 9999999999))

    @staticmethod
    def get_orders(user):
        """
        Get all orders for the user
        :param request: The request object
        :return: The response is being returned.
        """
        orders = client.futures_get_open_orders()
        valid_orders = []
        for order in orders:
            if not order['clientOrderId'].startswith(user.username) and not user.is_superuser:
                continue
            if order['origType'] in ['STOP_MARKET', 'TAKE_PROFIT_MARKET']:
                order['price'] = order['stopPrice']
            valid_orders.append(order)
        return valid_orders

    @staticmethod
    def get_positions(user):
        """
        Get all positions for the user
        :param request: The request object
        :return: The response is being returned.
        """
        positions = client.futures_position_information()
        valid_positions = []
        for position in positions:
            if float(position['positionAmt']) == 0:
                continue
            symbol = Symbol.objects.filter(sym_name=position['symbol'])
            if not symbol:
                continue
            symbol = symbol[0]
            if (not user in symbol.users.all() or symbol.is_active == False) and not user.is_superuser:
                continue
            valid_positions.append(position)
        return valid_positions

    @staticmethod
    def get_float_step_size(number):
        step_size = 0
        number = str(number)
        if 'e' in number:
            step_size += int(number.split('e-')[1])
        if '.' in number:
            step_size += len(number.split('e-')[0].split('.')[1])
        return step_size