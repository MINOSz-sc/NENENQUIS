from flask import Flask, render_template, request

app = Flask(__name__)

IVA_RATES = {
    "Argentina": 0.21,
    "México": 0.16,
    "España": 0.21,
    "Colombia": 0.19,
    "Chile": 0.19,
    "Perú": 0.18,
    "Otros": 0.21,
}

CURRENCY_BY_COUNTRY = {
    "Argentina": {"symbol": "$", "code": "ARS", "name": "Peso argentino"},
    "México": {"symbol": "$", "code": "MXN", "name": "Peso mexicano"},
    "España": {"symbol": "€", "code": "EUR", "name": "Euro"},
    "Colombia": {"symbol": "$", "code": "COP", "name": "Peso colombiano"},
    "Chile": {"symbol": "$", "code": "CLP", "name": "Peso chileno"},
    "Perú": {"symbol": "S/", "code": "PEN", "name": "Sol peruano"},
    "Otros": {"symbol": "$", "code": "USD", "name": "Dólar estadounidense"},
}

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    iva_rate = None
    if request.method == 'POST':
        try:
            product_name = request.form.get('product_name', '').strip()
            cost = float(request.form.get('cost', 0))
            profit_pct = float(request.form.get('profit_pct', 0))
            country = request.form.get('country', 'Otros')
            is_service = request.form.get('is_service') == 'on'

            iva_rate = IVA_RATES.get(country, IVA_RATES['Otros'])
            currency = CURRENCY_BY_COUNTRY.get(country, CURRENCY_BY_COUNTRY['Otros'])
            profit_amount = cost * (profit_pct / 100)
            base_price = cost + profit_amount
            iva_amount = base_price * iva_rate
            final_price = base_price + iva_amount

            result = {
                'product_name': product_name or ('Servicio' if is_service else 'Producto'),
                'cost': round(cost, 2),
                'profit_pct': round(profit_pct, 2),
                'profit_amount': round(profit_amount, 2),
                'base_price': round(base_price, 2),
                'iva_pct': round(iva_rate * 100, 2),
                'iva_amount': round(iva_amount, 2),
                'final_price': round(final_price, 2),
                'country': country,
                'currency_symbol': currency['symbol'],
                'currency_code': currency['code'],
                'currency_name': currency['name'],
                'product_type': 'Servicio' if is_service else 'Producto',
            }
        except ValueError:
            result = {'error': 'Por favor ingresa valores numéricos válidos para costo y porcentaje.'}

    return render_template('index.html', result=result, iva_rates=IVA_RATES)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
