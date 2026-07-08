import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, g

app = Flask(__name__)

try:
    import pymysql
    from pymysql.cursors import DictCursor
    MYSQL_AVAILABLE = True
except ImportError:
    pymysql = None
    DictCursor = None
    MYSQL_AVAILABLE = False

DB_CONFIG = {
    'host': 'sql5.freesqldatabase.com',
    'user': 'sql5832072',
    'password': 'A4k3Ls28x1',
    'db': 'sql5832072',
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': DictCursor,
}



DB_USE_MYSQL = MYSQL_AVAILABLE
DB_PATH = os.path.join(os.path.dirname(__file__), 'products.db')


def encrypt_text(value):
    return None if value is None else str(value)


def decrypt_text(value):
    return value


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

def get_create_table_sql(use_mysql):
    return '''
CREATE TABLE IF NOT EXISTS products (
    id {id_column},
    product_name TEXT NOT NULL,
    cost TEXT NOT NULL,
    profit_pct TEXT NOT NULL,
    country TEXT NOT NULL,
    is_service INTEGER NOT NULL DEFAULT 0,
    iva_rate TEXT NOT NULL,
    profit_amount TEXT NOT NULL,
    base_price TEXT NOT NULL,
    iva_amount TEXT NOT NULL,
    final_price TEXT NOT NULL,
    currency_code TEXT NOT NULL,
    currency_symbol TEXT NOT NULL,
    created_at TEXT NOT NULL
){table_options}
'''.format(
        id_column='INT AUTO_INCREMENT PRIMARY KEY' if use_mysql else 'INTEGER PRIMARY KEY AUTOINCREMENT',
        table_options=' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4' if use_mysql else ''
    )


def format_sql(sql):
    return sql if DB_USE_MYSQL else sql.replace('%s', '?')


def execute_sql(sql, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(format_sql(sql), params)
        if commit:
            conn.commit()
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
    finally:
        cursor.close()


def fallback_to_sqlite():
    global DB_USE_MYSQL
    DB_USE_MYSQL = False


def get_db_connection():
    conn = getattr(g, '_database', None)
    if conn is None:
        if DB_USE_MYSQL:
            try:
                conn = pymysql.connect(**DB_CONFIG)
            except Exception:
                fallback_to_sqlite()
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
        else:
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
    if DB_USE_MYSQL:
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            try:
                cursor.execute(get_create_table_sql(True))
                conn.commit()
            finally:
                cursor.close()
                conn.close()
        except Exception:
            fallback_to_sqlite()
            conn = sqlite3.connect(DB_PATH)
            conn.execute(get_create_table_sql(False))
            conn.commit()
            conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(get_create_table_sql(False))
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

            execute_sql(
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
                commit=True,
            )
        except ValueError:
            result = {'error': 'Por favor ingresa valores numéricos válidos para costo y porcentaje.'}

    conn = get_db_connection()
    return render_template('index.html', result=result, iva_rates=IVA_RATES)

@app.route('/products', methods=['GET', 'POST'])
def products():
    message = None
    search = request.args.get('search', '').strip()
    edit_id = request.args.get('edit_id')
    edit_product = None

    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        search = request.form.get('search', '').strip()
        product_id = request.form.get('product_id')

        if action == 'delete' and product_id:
            execute_sql('DELETE FROM products WHERE id = %s', (product_id,), commit=True)
            message = 'Producto eliminado correctamente.'
        elif action == 'update' and product_id:
            try:
                product_name = request.form.get('product_name', '').strip() or 'Producto'
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

                execute_sql(
                    '''UPDATE products SET
                        product_name=%s,
                        cost=%s,
                        profit_pct=%s,
                        country=%s,
                        is_service=%s,
                        iva_rate=%s,
                        profit_amount=%s,
                        base_price=%s,
                        iva_amount=%s,
                        final_price=%s,
                        currency_code=%s,
                        currency_symbol=%s
                    WHERE id=%s''',
                    (
                        product_name,
                        cost,
                        profit_pct,
                        country,
                        int(is_service),
                        iva_rate,
                        profit_amount,
                        base_price,
                        iva_amount,
                        final_price,
                        currency['code'],
                        currency['symbol'],
                        product_id,
                    ),
                    commit=True,
                )
                message = 'Producto actualizado correctamente.'
                edit_id = None
            except ValueError:
                message = 'Por favor ingresa datos numéricos válidos.'
                edit_id = product_id

    if edit_id:
        edit_product = execute_sql('SELECT * FROM products WHERE id = %s', (edit_id,), fetchone=True)
        if edit_product:
            edit_product = {
                'id': edit_product['id'],
                'product_name': edit_product['product_name'],
                'cost': edit_product['cost'],
                'profit_pct': edit_product['profit_pct'],
                'country': edit_product['country'],
                'is_service': bool(edit_product['is_service']),
            }

    rows = execute_sql('SELECT * FROM products ORDER BY created_at DESC', fetchall=True)

    products_list = []
    for row in rows:
        decrypted = {
            'id': row['id'],
            'product_name': row['product_name'],
            'cost': float(row['cost']) if row['cost'] else 0.0,
            'profit_pct': float(row['profit_pct']) if row['profit_pct'] else 0.0,
            'country': row['country'],
            'is_service': bool(row['is_service']),
            'iva_rate': float(row['iva_rate']) if row['iva_rate'] else 0.0,
            'profit_amount': float(row['profit_amount']) if row['profit_amount'] else 0.0,
            'base_price': float(row['base_price']) if row['base_price'] else 0.0,
            'iva_amount': float(row['iva_amount']) if row['iva_amount'] else 0.0,
            'final_price': float(row['final_price']) if row['final_price'] else 0.0,
            'currency_code': row['currency_code'],
            'currency_symbol': row['currency_symbol'],
            'created_at': row['created_at'],
        }
        products_list.append(decrypted)

    if search:
        search_lower = search.lower()
        products_list = [p for p in products_list if search_lower in p['product_name'].lower() or search_lower in p['country'].lower()]

    return render_template(
        'products.html',
        products=products_list,
        search=search,
        message=message,
        edit_product=edit_product,
        iva_rates=IVA_RATES,
    )


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
