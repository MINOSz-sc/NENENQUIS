import os
from datetime import datetime
from flask import Flask, render_template, request, g
import pymysql

app = Flask(__name__)

DB_CONFIG = {
    'host': 'sql5.freesqldatabase.com',
    'user': 'sql5832072',
    'password': 'A4k3Ls28x1',
    'db': 'sql5832072',
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

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
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    cost DECIMAL(12,2) NOT NULL,
    profit_pct DECIMAL(7,2) NOT NULL,
    country VARCHAR(100) NOT NULL,
    is_service TINYINT(1) NOT NULL DEFAULT 0,
    iva_rate DECIMAL(5,4) NOT NULL,
    profit_amount DECIMAL(12,2) NOT NULL,
    base_price DECIMAL(12,2) NOT NULL,
    iva_amount DECIMAL(12,2) NOT NULL,
    final_price DECIMAL(12,2) NOT NULL,
    currency_code VARCHAR(10) NOT NULL,
    currency_symbol VARCHAR(5) NOT NULL,
    created_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''


def get_db_connection():
    conn = getattr(g, '_database', None)
    if conn is None:
        conn = pymysql.connect(**DB_CONFIG)
        g._database = conn
    return conn


@app.teardown_appcontext
def close_connection(exception):
    conn = getattr(g, '_database', None)
    if conn is not None:
        conn.close()


def init_db():
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cursor:
        cursor.execute(CREATE_TABLE_SQL)
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
            with conn.cursor() as cursor:
                cursor.execute(
                    '''INSERT INTO products (
                        product_name, cost, profit_pct, country, is_service,
                        iva_rate, profit_amount, base_price, iva_amount,
                        final_price, currency_code, currency_symbol, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
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
                        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    ),
                )
            conn.commit()
        except ValueError:
            result = {'error': 'Por favor ingresa valores numéricos válidos para costo y porcentaje.'}

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
        products = cursor.fetchall()
    return render_template('index.html', result=result, iva_rates=IVA_RATES, products=products)


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
