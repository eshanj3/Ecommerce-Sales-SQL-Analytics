CREATE DATABASE IF NOT EXISTS ecommerce_analytics;
USE ecommerce_analytics;
 
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id     INT             NOT NULL AUTO_INCREMENT,
    first_name      VARCHAR(50)     NOT NULL,
    last_name       VARCHAR(50)     NOT NULL,
    email           VARCHAR(100)    NOT NULL,
    country         VARCHAR(50)     NOT NULL,
    signup_date     DATE            NOT NULL,
    PRIMARY KEY (customer_id),
    CONSTRAINT uq_customers_email UNIQUE (email)
);
CREATE TABLE products (
    product_id      INT             NOT NULL AUTO_INCREMENT,
    product_name    VARCHAR(100)    NOT NULL,
    category        VARCHAR(50)     NOT NULL,
    unit_price      DECIMAL(10,2)   NOT NULL,
    PRIMARY KEY (product_id)
);
CREATE TABLE orders (
    order_item_id           INT             NOT NULL AUTO_INCREMENT,
    order_id                INT             NOT NULL,
    customer_id             INT             NOT NULL,
    product_id              INT             NOT NULL,
    quantity                INT             NOT NULL,
    unit_price_at_order     DECIMAL(10,2)   NOT NULL,
    order_date              DATE            NOT NULL,
    PRIMARY KEY (order_item_id),
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    CONSTRAINT fk_orders_product
        FOREIGN KEY (product_id) REFERENCES products (product_id)
);