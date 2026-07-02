import os
from datetime import datetime
from flask import Flask, render_template, request, g
import pymysql
from cryptography.fernet import Fernet, InvalidToken

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

KEY_PATH = os.path.join(os.path.dirname(__file__), 'secret.key')


def load_or_create_key():
    env_key = os.environ.get('ENCRYPTION_KEY')
    if env_key:
        return env_key.encode('utf-8')

    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, 'rb') as file:
            return file.read()

    key = Fernet.generate_key()
    with open(KEY_PATH, 'wb') as file:
        file.write(key)
    return key


FERNET = Fernet(load_or_create_key())


def encrypt_text(value):
    if value is None:
        return None
    text = str(value).encode('utf-8')
    return FERNET.encrypt(text).decode('utf-8')


def decrypt_text(value):
    if value is None:
        return None
    try:
        return FERNET.decrypt(value.encode('utf-8')).decode('utf-8')
    except (InvalidToken, TypeError, ValueError):
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

CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name TEXT NOT NULL,
    cost TEXT NOT NULL,
    profit_pct TEXT NOT NULL,
    country TEXT NOT NULL,
    is_service TINYINT(1) NOT NULL DEFAULT 0,
    iva_rate TEXT NOT NULL,
    profit_amount TEXT NOT NULL,
    base_price TEXT NOT NULL,
    iva_amount TEXT NOT NULL,
    final_price TEXT NOT NULL,
    currency_code TEXT NOT NULL,
    currency_symbol TEXT NOT NULL,
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
        cursor.execute("ALTER TABLE products MODIFY COLUMN product_name TEXT NOT NULL")
        cursor.execute("ALTER TABLE products MODIFY COLUMN cost TEXT NOT NULL")
        cursor.execute("ALTER TABLE products MODIFY COLUMN profit_pct TEXT NOT NULL")
        cursor.execute("ALTER TABLE products MODIFY COLUMN country TEXT NOT NULL")
        cursor.execute("ALTER TABLE products MODIFY COLUMN iva_rate TEXT NOT NULL")
        cursor.execute("ALTER TABLE products MODIFY COLUMN profit_amount TEXT NOT NULL")
        cursor.execute("ALTER TABLE products MODIFY COLUMN base_price TEXT NOT NULL")
        cursor.execute("ALTER TABLE products MODIFY COLUMN iva_amount TEXT NOT NULL")
        cursor.execute("ALTER TABLE products MODIFY COLUMN final_price TEXT NOT NULL")
        cursor.execute("ALTER TABLE products MODIFY COLUMN currency_code TEXT NOT NULL")
        cursor.execute("ALTER TABLE products MODIFY COLUMN currency_symbol TEXT NOT NULL")
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
                        encrypt_text(result['product_name']),
                        encrypt_text(result['cost']),
                        encrypt_text(result['profit_pct']),
                        encrypt_text(result['country']),
                        int(is_service),
                        encrypt_text(iva_rate),
                        encrypt_text(result['profit_amount']),
                        encrypt_text(result['base_price']),
                        encrypt_text(result['iva_amount']),
                        encrypt_text(result['final_price']),
                        encrypt_text(result['currency_code']),
                        encrypt_text(result['currency_symbol']),
                        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    ),
                )
            conn.commit()
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
            with conn.cursor() as cursor:
                cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
            conn.commit()
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

                with conn.cursor() as cursor:
                    cursor.execute(
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
                            encrypt_text(product_name),
                            encrypt_text(cost),
                            encrypt_text(profit_pct),
                            encrypt_text(country),
                            int(is_service),
                            encrypt_text(iva_rate),
                            encrypt_text(profit_amount),
                            encrypt_text(base_price),
                            encrypt_text(iva_amount),
                            encrypt_text(final_price),
                            encrypt_text(currency['code']),
                            encrypt_text(currency['symbol']),
                            product_id,
                        ),
                    )
                conn.commit()
                message = 'Producto actualizado correctamente.'
                edit_id = None
            except ValueError:
                message = 'Por favor ingresa datos numéricos válidos.'
                edit_id = product_id

    if edit_id:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM products WHERE id = %s', (edit_id,))
            edit_product = cursor.fetchone()
            if edit_product:
                edit_product = {
                    'id': edit_product['id'],
                    'product_name': decrypt_text(edit_product['product_name']),
                    'cost': decrypt_text(edit_product['cost']),
                    'profit_pct': decrypt_text(edit_product['profit_pct']),
                    'country': decrypt_text(edit_product['country']),
                    'is_service': bool(edit_product['is_service']),
                }

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
        rows = cursor.fetchall()

    products_list = []
    for row in rows:
        decrypted = {
            'id': row['id'],
            'product_name': decrypt_text(row['product_name']),
            'cost': float(decrypt_text(row['cost'])) if row['cost'] else 0.0,
            'profit_pct': float(decrypt_text(row['profit_pct'])) if row['profit_pct'] else 0.0,
            'country': decrypt_text(row['country']),
            'is_service': bool(row['is_service']),
            'iva_rate': float(decrypt_text(row['iva_rate'])) if row['iva_rate'] else 0.0,
            'profit_amount': float(decrypt_text(row['profit_amount'])) if row['profit_amount'] else 0.0,
            'base_price': float(decrypt_text(row['base_price'])) if row['base_price'] else 0.0,
            'iva_amount': float(decrypt_text(row['iva_amount'])) if row['iva_amount'] else 0.0,
            'final_price': float(decrypt_text(row['final_price'])) if row['final_price'] else 0.0,
            'currency_code': decrypt_text(row['currency_code']),
            'currency_symbol': decrypt_text(row['currency_symbol']),
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
