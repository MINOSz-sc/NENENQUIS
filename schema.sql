-- Estructura de la base de datos para la tabla de productos
-- Esta definición está en formato MySQL compatible.

CREATE TABLE products (
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
);
