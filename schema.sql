-- Estructura de la base de datos para la tabla de productos
-- Esta definición está en formato MySQL compatible.

CREATE TABLE products (
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
);
