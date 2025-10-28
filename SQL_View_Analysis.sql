-- View Tổng Hợp Giá Chứng Khoán
CREATE OR REPLACE VIEW vw_StockPriceSummary AS
SELECT 
    "StockSymbol",
    "CompanyName",
    "Industry",
    "Year",
    "Quarter",
    "Month",
    "AvgClosePrice",
    "MinPrice",
    "MaxPrice",
    "TotalVolume",
    "MonthStartPrice",
    "MonthEndPrice",
    ROUND(
        ("MonthEndPrice" - "MonthStartPrice") / NULLIF("MonthStartPrice", 0) * 100, 
        2
    ) AS "MonthlyChangePercent"
FROM (
    SELECT 
        ds."StockSymbol",
        ds."CompanyName",
        ds."Industry",
        dt."Year",
        dt."Quarter",
        dt."Month",
        ROUND(AVG(fs."Close"), 2) AS "AvgClosePrice",
        ROUND(MIN(fs."Low"), 2) AS "MinPrice",
        ROUND(MAX(fs."High"), 2) AS "MaxPrice",
        SUM(fs."Volume") AS "TotalVolume",
        FIRST_VALUE(fs."Close") OVER (
            PARTITION BY ds."StockKey", dt."Year", dt."Month" 
            ORDER BY dt."Date"
        ) AS "MonthStartPrice",
        LAST_VALUE(fs."Close") OVER (
            PARTITION BY ds."StockKey", dt."Year", dt."Month" 
            ORDER BY dt."Date"
            RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS "MonthEndPrice"
    FROM 
        "Fact_StockPrice" fs
    JOIN 
        "Dim_Company" ds ON fs."StockKey" = ds."StockKey"
    JOIN 
        "Dim_Time" dt ON fs."TimeKey" = dt."TimeKey"
    GROUP BY 
        ds."StockSymbol", ds."CompanyName", ds."Industry", 
        dt."Year", dt."Quarter", dt."Month", 
        ds."StockKey", dt."Date", fs."Close"
) subquery
GROUP BY 
    "StockSymbol", "CompanyName", "Industry", "Year", "Quarter", "Month", 
    "AvgClosePrice", "MinPrice", "MaxPrice", "TotalVolume", 
    "MonthStartPrice", "MonthEndPrice";

----------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------

-- View Chỉ số tài chính theo Quý
CREATE OR REPLACE VIEW vw_QuarterlyFinancialRatios AS
SELECT 
    ds."StockSymbol",
    ds."CompanyName",
    dt."Year",
    dt."Quarter",
    dr."RatioName",
    dr."Unit",
    dr."RatioType",
    ROUND(AVG(fr."Value"), 2) AS "RatioValue"
FROM 
    "Fact_FinancialRatios" fr
JOIN 
    "Dim_Company" ds ON fr."StockKey" = ds."StockKey"
JOIN 
    "Dim_Time" dt ON fr."TimeKey" = dt."TimeKey"
JOIN 
    "Dim_Ratio" dr ON fr."RatioKey" = dr."RatioKey"
GROUP BY 
    ds."StockSymbol",
    ds."CompanyName",
    dt."Year",
    dt."Quarter",
    dr."RatioName",
    dr."Unit",
    dr."RatioType";
	
----------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------

-- View Phân Tích Biến Động Giá
CREATE OR REPLACE VIEW vw_StockPriceMovement AS
WITH DailyChanges AS (
    SELECT 
        fs."TimeKey",
        fs."StockKey",
        fs."Close",
        LAG(fs."Close") OVER (
            PARTITION BY fs."StockKey" 
            ORDER BY dt."Date"
        ) AS "PrevClose",
        dt."Year",
        dt."Month",
        dt."Date"
    FROM 
        "Fact_StockPrice" fs
    JOIN 
        "Dim_Time" dt ON fs."TimeKey" = dt."TimeKey"
)
SELECT 
    ds."StockSymbol",
    ds."CompanyName",
    dc."Year",
    dc."Month",
    dc."Date",
    dc."Close" AS "CurrentPrice",
    dc."PrevClose",
    ROUND(
        (dc."Close" - dc."PrevClose") / NULLIF(dc."PrevClose", 0) * 100, 
        2
    ) AS "DailyChangePercent",
    ROUND(
        AVG((dc."Close" - dc."PrevClose") / NULLIF(dc."PrevClose", 0) * 100) 
        OVER (
            PARTITION BY dc."StockKey" 
            ORDER BY dc."Date" 
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS "FiveDayAvgChange",
    ROUND(
        AVG((dc."Close" - dc."PrevClose") / NULLIF(dc."PrevClose", 0) * 100) 
        OVER (
            PARTITION BY dc."StockKey" 
            ORDER BY dc."Date" 
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS "TwentyDayAvgChange"
FROM 
    DailyChanges dc
JOIN 
    "Dim_Company" ds ON dc."StockKey" = ds."StockKey"
WHERE 
    dc."PrevClose" IS NOT NULL;
	
----------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------

-- View VN30 Performance
CREATE OR REPLACE VIEW vw_VN30Performance AS
SELECT 
    dt."Date",
    dt."Year",
    dt."Quarter",
    dt."Month",
    ds."StockSymbol",
    ds."Industry",
    fs."Close",
    fs."Volume",
    ROUND(
        (fs."Close" - LAG(fs."Close") OVER stock_daily) / 
        NULLIF(LAG(fs."Close") OVER stock_daily, 0) * 100, 
        2
    ) AS "DailyReturn",
    ROUND(
        (fs."Close" / FIRST_VALUE(fs."Close") OVER ytd_window - 1) * 100, 
        2
    ) AS "YTDReturn",
    ROUND(
        AVG(fs."Close") OVER (
            PARTITION BY fs."StockKey" 
            ORDER BY dt."Date" 
            ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS "MA10",
    ROUND(
        AVG(fs."Close") OVER (
            PARTITION BY fs."StockKey" 
            ORDER BY dt."Date" 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS "MA30"
FROM 
    "Fact_StockPrice" fs
JOIN 
    "Dim_Company" ds ON fs."StockKey" = ds."StockKey"
JOIN 
    "Dim_Time" dt ON fs."TimeKey" = dt."TimeKey"
WHERE 
    ds."StockSymbol" IN (
        'VNM', 'VIC', 'VHM', 'VCB', 'GAS', 'SAB', 'BID', 'MSN', 'TCB', 'HPG',
        'MWG', 'VRE', 'VJC', 'PLX', 'VPB', 'FPT', 'POW', 'BVH', 'NVL', 'STB',
        'HDB', 'TPB', 'PNJ', 'REE', 'SSI', 'CTG', 'KDH', 'GVR', 'PDR', 'ACB'
    )
WINDOW 
    stock_daily AS (PARTITION BY fs."StockKey" ORDER BY dt."Date"),
    ytd_window AS (PARTITION BY fs."StockKey", dt."Year" ORDER BY dt."Date");