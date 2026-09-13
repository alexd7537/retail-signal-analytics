-- Dialecto: SQLite. Abrir analysis/retail.sqlite.
-- Importe base entero en milésimas GBP: división explícita entre 1000.0.

-- 1. Indicadores principales. No se eliminan posibles duplicados.
SELECT
    SUM(CASE WHEN TransactionType='Venta' THEN AmountMilliGBP ELSE 0 END)/1000.0 AS gross_gbp,
    -SUM(CASE WHEN TransactionType='Abono' THEN AmountMilliGBP ELSE 0 END)/1000.0 AS credits_gbp,
    SUM(AmountMilliGBP)/1000.0 AS net_gbp,
    COUNT(DISTINCT CASE WHEN TransactionType='Venta' THEN InvoiceNo END) AS orders,
    COUNT(DISTINCT CASE WHEN TransactionType='Venta' AND CustomerID<>'UNKNOWN' THEN CustomerID END) AS customers
FROM FactTransactions;

-- 2. Serie mensual. Diciembre 2011 es parcial.
SELECT substr(Date,1,7) AS month,
    SUM(AmountMilliGBP)/1000.0 AS net_gbp,
    COUNT(DISTINCT CASE WHEN TransactionType='Venta' THEN InvoiceNo END) AS orders,
    CASE WHEN substr(Date,1,7)='2011-12' THEN 'Parcial 1-9' ELSE 'Completo' END AS coverage
FROM FactTransactions GROUP BY substr(Date,1,7) ORDER BY month;

-- 3. Productos más vendidos por neto.
SELECT StockCode, SUM(AmountMilliGBP)/1000.0 AS net_gbp,
    SUM(CASE WHEN TransactionType='Venta' THEN Quantity ELSE 0 END) AS units,
    COUNT(DISTINCT CASE WHEN TransactionType='Venta' THEN InvoiceNo END) AS orders
FROM FactTransactions GROUP BY StockCode ORDER BY net_gbp DESC LIMIT 10;

-- 4. Países fuera del Reino Unido.
SELECT Country, SUM(AmountMilliGBP)/1000.0 AS net_gbp,
    COUNT(DISTINCT CASE WHEN TransactionType='Venta' AND CustomerID<>'UNKNOWN' THEN CustomerID END) AS customers
FROM FactTransactions WHERE Country<>'United Kingdom'
GROUP BY Country ORDER BY net_gbp DESC;

-- 5. Una compra vs recurrentes. No es retención de cohortes.
WITH buyers AS (
 SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS orders
 FROM FactTransactions WHERE TransactionType='Venta' AND CustomerID<>'UNKNOWN'
 GROUP BY CustomerID
)
SELECT CASE WHEN orders>=2 THEN 'Recurrente' ELSE 'Una compra' END AS segment,
 COUNT(*) AS customers FROM buyers GROUP BY segment;

-- 6. Sensibilidad de los posibles duplicados de líneas de productos.
SELECT SUM(AmountMilliGBP)/1000.0 AS original_net,
 SUM(CASE WHEN DuplicateCandidate=0 THEN AmountMilliGBP ELSE 0 END)/1000.0 AS deduplicated_net,
 SUM(CASE WHEN DuplicateCandidate=1 THEN AmountMilliGBP ELSE 0 END)/1000.0 AS difference
FROM FactTransactions;

-- 7. Candidatos a pares compensados. No prueba causa ni factura original.
SELECT CustomerID,StockCode,Date,ABS(AmountMilliGBP)/1000.0 AS absolute_gbp,
 COUNT(*) AS lines,SUM(AmountMilliGBP)/1000.0 AS net_gbp
FROM FactTransactions WHERE ABS(AmountMilliGBP)>=50000000
GROUP BY CustomerID,StockCode,Date,ABS(AmountMilliGBP)
HAVING SUM(AmountMilliGBP)=0;

-- 8. El filtro que se probó también en Excel.
SELECT SUM(AmountMilliGBP)/1000.0 AS net_gbp,
 COUNT(DISTINCT CASE WHEN TransactionType='Venta' THEN InvoiceNo END) AS orders
FROM FactTransactions WHERE Country='Germany' AND Date>='2011-11-01' AND Date<'2011-12-01';
