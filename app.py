import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, g

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'products.db')

IVA_RATES = {
    'Argentina': 0.21,
    'México': 0.16,
    'España': 0.21,
    'Colombia': 0.19,
    'Chile': 0.19,
    'Perú': 0.18,
    'Otros': 0.21,
}

CURRENCY_BY_COUNTRY = {
    'Argentina': {'symbol': '$', 'code': 'ARS', 'name': 'Peso argentino'},
    'México': {'symbol': '$', 'code': 'MXN', 'name': 'Peso mexicano'},
    'España': {'symbol': '€', 'code': 'EUR', 'name': 'Euro'},
    'Colombia': {'symbol': '$', 'code': 'COP', 'name': 'Peso colombiano'},
    'Chile': {'symbol': '$', 'code': 'CLP', 'name': 'Peso chileno'},
    'Perú': {'symbol': 'S/', 'code': 'PEN', 'name': 'Sol peruano'},
    'Otros': {'symbol': '$', 'code': 'USD', 'name': 'Dólar estadounidense'},
}

CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    cost REAL NOT NULL,
    profit_pct REAL NOT NULL,
    country TEXT NOT NULL,
    is_service INTEGER NOT NULL DEFAULT 0,
    iva_rate REAL NOT NULL,
    profit_amount REAL NOT NULL,
    base_price REAL NOT NULL,
    iva_amount REAL NOT NULL,
    final_price REAL NOT NULL,
    currency_code TEXT NOT NULL,
    currency_symbol TEXT NOT NULL,
    created_at TEXT NOT NULL
);
'''


def get_db_connection():
    conn = getattr(g, '_database', None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g._database = conn
    return conn


@app.teardown_appcontext
def close_connection(exception):
    conn = getattr(g, '_database', None)
    if conn is not None:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
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

            conn = get_db_connection()
            conn.execute(
                '''INSERT INTO products (
                    product_name, cost, profit_pct, country, is_service,
                    iva_rate, profit_amount, base_price, iva_amount,
                    final_price, currency_code, currency_symbol, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    result['product_name'],
                    result['cost'],
                    result['profit_pct'],
                    result['country'],
                    int(is_service),
                    iva_rate,
                    result['profit_amount'],
                    result['base_price'],
                    result['iva_amount'],
                    result['final_price'],
                    result['currency_code'],
                    result['currency_symbol'],
                    datetime.utcnow().isoformat(sep=' ', timespec='seconds'),
                ),
            )
            conn.commit()
        except ValueError:
            result = {'error': 'Por favor ingresa valores numéricos válidos para costo y porcentaje.'}

    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY created_at DESC').fetchall()
    return render_template('index.html', result=result, iva_rates=IVA_RATES, products=products)


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
