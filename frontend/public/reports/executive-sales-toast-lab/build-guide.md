# Executive Sales Report — Toast Notification — build guide

Content version: 1.0.1

## Learning outcomes
- Import CSV star-schema data with Power Query
- Model relationships and a marked date table
- Author DAX for KPIs, targets, and toast alerts
- Recreate the reference dashboard layout in Power BI Desktop

## Prerequisites
- Basic Power BI Desktop familiarity

Tested Desktop: Power BI Desktop 2024–2025 (HTML Content 1.2.1.17)

# Stage 1: Setup

Tools, downloads, blank PBIX

## 1. Know the target report

**Objective:** Recognize the finished executive sales page you will rebuild from a blank PBIX.

### Actions
1. Open the JobReady **Finished preview** (static PNG — interactions happen in Power BI Desktop).
1. Note canvas size 1280×780 and the KPI + trend + toast layout.

**Expected:** You can describe where slicers, KPIs, bars, trend, settings, and toast sit on the page.

**Checklist:**
- [ ] Preview image loads
- [ ] You understand this is a reference only

## 2. Install tools

**Objective:** Use a Power BI Desktop build that supports HTML Content custom visuals.

**Prerequisites:** setup-01

### Actions
1. Install **Power BI Desktop** (tested with recent 2024–2025 builds).
1. From AppSource in Desktop, add custom visual **HTML Content** (package id htmlContent443BE3AD55E043BF878BED274D3A6855, version 1.2.1.17 in the reference file).
1. Create an empty folder for lab data, e.g. `C:\JobReady\executive-sales-data\`.

**Expected:** Desktop opens, HTML Content visual is available in the visualizations pane.

## 3. Download the student kit

**Objective:** Get CSVs and guides from JobReady.

**Prerequisites:** setup-02

### Actions
1. Download **All datasets (.zip)** and extract into your data folder.
1. Optional: download the reference `.pbix` only to compare — do not start from it for the graded rebuild.

**Expected:** Eight CSV files present (3–20000 rows).

**Checklist:**
- [ ] datasets.zip extracts without errors
- [ ] data folder path has no spaces issues in M

## 4. Create a blank report

**Objective:** Start from File → New to mirror the workshop path.

**Prerequisites:** setup-03

### Actions
1. File → New → Blank report.
1. Save as `Executive-Sales-Toast.pbix` in your lab folder.

**Expected:** Empty report with one blank page.

# Stage 2: Import data

CSV imports with exact table names

## 5. Create DataFolder parameter

**Objective:** One path drives all CSV imports.

**Prerequisites:** setup-04

### Actions
1. Home → Transform data → Manage Parameters → New.
1. Name: **DataFolder**, type Text, current value = folder containing the eight CSV files (trailing backslash optional).

**Expected:** Parameter DataFolder appears under Parameters.

**Checklist:**
- [ ] Path opens without privacy errors on refresh

## 6. Import Sales

**Objective:** Load `Sales.csv` as table **Sales** with explicit types.

**Prerequisites:** import-00

### Actions
1. Home → Transform data → New Source → Blank Query.
1. Paste the M below (uses `DataFolder` parameter).
1. Rename query to **Sales** and ensure it loads to the model with table name **Sales**.
1. Close && Apply.

**Expected:** Table **Sales** appears in the Fields pane.

**Checklist:**
- [ ] Table name is exactly `Sales`
- [ ] Refresh preview succeeds

## 7. Import Date Table

**Objective:** Load `Date_Table.csv` as table **Date Table** with explicit types.

**Prerequisites:** import-01

### Actions
1. Home → Transform data → New Source → Blank Query.
1. Paste the M below (uses `DataFolder` parameter).
1. Rename query to **Date Table** and ensure it loads to the model with table name **Date Table**.
1. Close && Apply.

**Expected:** Table **Date Table** appears in the Fields pane.

**Checklist:**
- [ ] Table name is exactly `Date Table`
- [ ] Refresh preview succeeds

## 8. Import Products_Data

**Objective:** Load `Products_Data.csv` as table **Products_Data** with explicit types.

**Prerequisites:** import-02

### Actions
1. Home → Transform data → New Source → Blank Query.
1. Paste the M below (uses `DataFolder` parameter).
1. Rename query to **Products_Data** and ensure it loads to the model with table name **Products_Data**.
1. Close && Apply.

**Expected:** Table **Products_Data** appears in the Fields pane.

**Checklist:**
- [ ] Table name is exactly `Products_Data`
- [ ] Refresh preview succeeds

## 9. Import storelocations

**Objective:** Load `storelocations.csv` as table **storelocations** with explicit types.

**Prerequisites:** import-03

### Actions
1. Home → Transform data → New Source → Blank Query.
1. Paste the M below (uses `DataFolder` parameter).
1. Rename query to **storelocations** and ensure it loads to the model with table name **storelocations**.
1. Close && Apply.

**Expected:** Table **storelocations** appears in the Fields pane.

**Checklist:**
- [ ] Table name is exactly `storelocations`
- [ ] Refresh preview succeeds

## 10. Import Salesteams

**Objective:** Load `Salesteams.csv` as table **Salesteams** with explicit types.

**Prerequisites:** import-04

### Actions
1. Home → Transform data → New Source → Blank Query.
1. Paste the M below (uses `DataFolder` parameter).
1. Rename query to **Salesteams** and ensure it loads to the model with table name **Salesteams**.
1. Close && Apply.

**Expected:** Table **Salesteams** appears in the Fields pane.

**Checklist:**
- [ ] Table name is exactly `Salesteams`
- [ ] Refresh preview succeeds

## 11. Import Higher Percentile

**Objective:** Load `Higher_Percentile.csv` as table **Higher Percentile** with explicit types.

**Prerequisites:** import-05

### Actions
1. Home → Transform data → New Source → Blank Query.
1. Paste the M below (uses `DataFolder` parameter).
1. Rename query to **Higher Percentile** and ensure it loads to the model with table name **Higher Percentile**.
1. Close && Apply.

**Expected:** Table **Higher Percentile** appears in the Fields pane.

**Checklist:**
- [ ] Table name is exactly `Higher Percentile`
- [ ] Refresh preview succeeds

## 12. Import Lower Percentile

**Objective:** Load `Lower_Percentile.csv` as table **Lower Percentile** with explicit types.

**Prerequisites:** import-06

### Actions
1. Home → Transform data → New Source → Blank Query.
1. Paste the M below (uses `DataFolder` parameter).
1. Rename query to **Lower Percentile** and ensure it loads to the model with table name **Lower Percentile**.
1. Close && Apply.

**Expected:** Table **Lower Percentile** appears in the Fields pane.

**Checklist:**
- [ ] Table name is exactly `Lower Percentile`
- [ ] Refresh preview succeeds

## 13. Import Date M-W-D

**Objective:** Load `Date_M-W-D.csv` as table **Date M-W-D** with explicit types.

**Prerequisites:** import-07

### Actions
1. Home → Transform data → New Source → Blank Query.
1. Paste the M below (uses `DataFolder` parameter).
1. Rename query to **Date M-W-D** and ensure it loads to the model with table name **Date M-W-D**.
1. Close && Apply.

**Expected:** Table **Date M-W-D** appears in the Fields pane.

**Checklist:**
- [ ] Table name is exactly `Date M-W-D`
- [ ] Refresh preview succeeds

# Stage 3: Validate data

Counts, keys, dates

## 14. Row counts

**Objective:** Confirm CSV loads match the packaged data.

**Prerequisites:** import-08

### Actions
1. Model view → select each table → verify row counts against the data dictionary.

**Expected:** Sales 20,000 rows; Date Table 152; Products 47; stores 367; teams 28; percentile tables 10 each; Date M-W-D 3.

**Checklist:**
- [ ] Counts match manifest.json

## 15. Sales keys

**Objective:** Ensure foreign keys exist in dimensions.

**Prerequisites:** validate-01

### Actions
1. In Power Query or DAX, verify every Sales[Productindex] exists in Products_Data[Productindex].
1. Repeat for Storeindex → storelocations and Salesteamindex → Salesteams.

**Expected:** No unmatched keys (0 orphan rows).

## 16. Date coverage

**Objective:** Understand the sample period.

**Prerequisites:** validate-02

### Actions
1. Date Table covers 2020-01-01 through 2020-05-31 (152 days).
1. Sales dates should fall inside this range.

**Expected:** min(Sales[Sales Date]) ≥ 2020-01-01 and max ≤ 2020-05-31.

## 17. Unmatched sales check

**Objective:** Document blank keys.

**Prerequisites:** validate-03

### Actions
1. Sort Sales columns for null Productindex/Storeindex/Salesteamindex — expect none.

**Expected:** No blank foreign keys in Sales.

# Stage 4: Model relationships

Four active M:1 relationships

## 18. Sales.Salesteamindex → Salesteams.Salesteamindex

**Objective:** Create one active many-to-one relationship with single-direction filter from dimension to Sales.

**Prerequisites:** validate-04

### Actions
1. Model view → drag from Sales foreign key to dimension primary key.
1. From: **Sales**[Salesteamindex]
1. To: **Salesteams**[Salesteamindex]
1. Cardinality: Many-to-one (*:1).
1. Cross-filter direction: Single (dimension filters Sales).
1. Leave relationship **active**.

**Expected:** Relationship line shows 1 on dimension side, * on Sales.

**Checklist:**
- [ ] Active
- [ ] Single direction from dimension

## 19. Sales.Storeindex → storelocations.Storeindex

**Objective:** Create one active many-to-one relationship with single-direction filter from dimension to Sales.

**Prerequisites:** rel-01

### Actions
1. Model view → drag from Sales foreign key to dimension primary key.
1. From: **Sales**[Storeindex]
1. To: **storelocations**[Storeindex]
1. Cardinality: Many-to-one (*:1).
1. Cross-filter direction: Single (dimension filters Sales).
1. Leave relationship **active**.

**Expected:** Relationship line shows 1 on dimension side, * on Sales.

**Checklist:**
- [ ] Active
- [ ] Single direction from dimension

## 20. Sales.Productindex → Products_Data.Productindex

**Objective:** Create one active many-to-one relationship with single-direction filter from dimension to Sales.

**Prerequisites:** rel-02

### Actions
1. Model view → drag from Sales foreign key to dimension primary key.
1. From: **Sales**[Productindex]
1. To: **Products_Data**[Productindex]
1. Cardinality: Many-to-one (*:1).
1. Cross-filter direction: Single (dimension filters Sales).
1. Leave relationship **active**.

**Expected:** Relationship line shows 1 on dimension side, * on Sales.

**Checklist:**
- [ ] Active
- [ ] Single direction from dimension

## 21. Sales.Sales Date → Date Table.Date

**Objective:** Create one active many-to-one relationship with single-direction filter from dimension to Sales.

**Prerequisites:** rel-03

### Actions
1. Model view → drag from Sales foreign key to dimension primary key.
1. From: **Sales**[Sales Date]
1. To: **Date Table**[Date]
1. Cardinality: Many-to-one (*:1).
1. Cross-filter direction: Single (dimension filters Sales).
1. Leave relationship **active**.

**Expected:** Relationship line shows 1 on dimension side, * on Sales.

**Checklist:**
- [ ] Active
- [ ] Single direction from dimension

# Stage 5: Date controls

Date table, sort, D/W/M parameter

## 22. Mark the date table

**Objective:** Enable time intelligence on Date Table.

**Prerequisites:** rel-04

### Actions
1. Select **Date Table** in the Fields pane.
1. Table tools → Mark as date table → choose column **Date**.

**Expected:** Date Table shows date table icon.

## 23. Sort month labels

**Objective:** Chronological month order on visuals.

**Prerequisites:** date-01

### Actions
1. Select Date Table[Month Short].
1. Column tools → Sort by column → **Month Number**.
1. Repeat: Week label columns sorted by WeeknYear if used on axis.

**Expected:** Months order Jan–May, not alphabetically.

## 24. Create D/W/M field parameter

**Objective:** Match the reference slicer that drives axis grain.

**Prerequisites:** date-02

### Actions
1. Modeling → New parameter → Fields.
1. Add fields: Date Table[Date] (Day), Date Table[WeeknYear] (Week), Date Table[Month Short] (Month).
1. Name the parameter **Date M-W-D** (rename display column to `Date M-W-D` and order column `Date M-W-D Order`).
1. Do **not** import Date_M-W-D.csv expecting parameter metadata — that CSV is only a helper lookup.

**Expected:** Slicer parameter with three values orders Day < Week < Month.

## 25. Hide helper columns

**Objective:** Reduce clutter.

**Prerequisites:** date-03

### Actions
1. Hide technical columns on Date Table used only for sorting (Month Number, etc.) except those needed on visuals.

**Expected:** Students can still sort months correctly.

# Stage 6: Measures

DAX in dependency order

## 26. Measures: Total Sales, Average Daily Sales, Average Monthly Saeles…

**Objective:** Create DAX measures in dependency order.

**Prerequisites:** date-03

### Actions
1. Modeling → New table → name it `# Measures` (hide later).
1. New measure for each formula below (home table `# Measures` unless noted).
1. Set format strings where specified in checklist.

### DAX
```dax
Total Sales =
SUMX(
    Sales, 
    Sales[Order qty] * Sales[unit price] 
    )
```

```dax
Average Daily Sales =
VAR _table = ALLSELECTED('Date Table')
VAR _Result = AVERAGEX( _table , [Total Sales] )
RETURN _Result
```

```dax
Average Monthly Saeles =
VAR _table = VALUES('Date Table'[Month Short] )
VAR _Result = AVERAGEX( _table , [Total Sales] )
RETURN _Result
```

```dax
Average Weekly Saeles =
VAR _table = VALUES( 'Date Table'[WeeknYear] )
VAR _Result = AVERAGEX( _table , [Total Sales] )
RETURN _Result
```

```dax
Higher Percentile Value =
SELECTEDVALUE('Higher Percentile'[Higher Percentile], 0.75)
```

```dax
Higher Percentile of Dates =
VAR _highPth = 'Higher Percentile'[Higher Percentile Value]
VAR _Result =
    SWITCH (
        TRUE (),
        ISINSCOPE ( 'Date Table'[Date] ), PERCENTILEX.EXC ( ALL( 'Date Table'[Date] ), [Total Sales], _highPth ),
        ISINSCOPE ( 'Date Table'[Month Short] ),
            PERCENTILEX.EXC (
                ALL( 'Date Table'[Month Short] ),
                [Total Sales],
                _highPth
            ),
        ISINSCOPE ( 'Date Table'[WeeknYear] ),
            PERCENTILEX.EXC (
                ALL( 'Date Table'[WeeknYear] ),
                [Total Sales],
                _highPth
            )
    )
RETURN
    _Result
```

**Expected:** Measures compile without errors.

**Checklist:**
- [ ] `Total Sales` returns values
- [ ] `Average Daily Sales` returns values
- [ ] `Average Monthly Saeles` returns values
- [ ] `Average Weekly Saeles` returns values
- [ ] `Higher Percentile Value` returns values
- [ ] `Higher Percentile of Dates` returns values

## 27. Measures: Lower Percentile Value, Lower Percentile of Dates, Color Formatting Line Chart…

**Objective:** Create DAX measures in dependency order.

**Prerequisites:** measure-01

### Actions
1. Modeling → New table → name it `# Measures` (hide later).
1. New measure for each formula below (home table `# Measures` unless noted).
1. Set format strings where specified in checklist.

### DAX
```dax
Lower Percentile Value =
SELECTEDVALUE('Lower Percentile'[Lower Percentile], 0.25)
```

```dax
Lower Percentile of Dates =
VAR _LowerPth = 'Lower Percentile'[Lower Percentile Value]
VAR _Result =
    SWITCH (
        TRUE (),
        ISINSCOPE ( 'Date Table'[Date] ), PERCENTILEX.EXC ( ALL( 'Date Table'[Date] ), [Total Sales], _LowerPth ),
        ISINSCOPE ( 'Date Table'[Month Short] ),
            PERCENTILEX.EXC (
                ALL( 'Date Table'[Month Short] ),
                [Total Sales],
                _LowerPth
            ),
        ISINSCOPE ( 'Date Table'[WeeknYear] ),
            PERCENTILEX.EXC (
                ALL( 'Date Table'[WeeknYear] ),
                [Total Sales],
                _LowerPth
            )
    )
RETURN
    _Result
```

```dax
Color Formatting Line Chart =
VAR _BottumColors = "#FA0C27" 
VAR _TopColors = "#1800ED"
VAR _MiddleColor = "#B6B1AF"
VAR _Result = 
SWITCH(
    TRUE(),
    [Total Sales] > [Higher Percentile of Dates], _TopColors,
    [Total Sales] < [Lower Percentile of Dates], _BottumColors,
    _MiddleColor
    )
RETURN _Result
```

```dax
TS PM Current =
VAR _datetable =
 DATESINPERIOD( 
    'Date Table'[Date], MAX(Sales[Sales Date]), -1, MONTH )
VAR _result =
CALCULATE(
    [Total Sales],
    _datetable
    )
RETURN _result
```

```dax
TS PM Previous =
VAR _datetable =
 DATESINPERIOD( 
    'Date Table'[Date], MAX(Sales[Sales Date]), -1, MONTH )
VAR _result =
CALCULATE(
    [Total Sales],
    PREVIOUSMONTH(_datetable)
    )
RETURN _result
```

```dax
TS MOM diff % =
DIVIDE(
    ([TS PM Current] - [TS PM Previous]),
    [TS PM Previous]
    )
```

**Expected:** Measures compile without errors.

**Checklist:**
- [ ] `Lower Percentile Value` returns values
- [ ] `Lower Percentile of Dates` returns values
- [ ] `Color Formatting Line Chart` returns values
- [ ] `TS PM Current` returns values
- [ ] `TS PM Previous` returns values
- [ ] `TS MOM diff %` returns values

## 28. Measures: Formatted KPI % MOM, Total Sales Current Week, Total Sales Previous Week…

**Objective:** Create DAX measures in dependency order.

**Prerequisites:** measure-02

### Actions
1. Modeling → New table → name it `# Measures` (hide later).
1. New measure for each formula below (home table `# Measures` unless noted).
1. Set format strings where specified in checklist.

### DAX
```dax
Formatted KPI % MOM =
VAR _Result =
SWITCH( 
    TRUE(),
    [TS MOM diff %] >= 0 , "▲",
    [TS MOM diff %] < 0 , "▼",
    BLANK()
)
Return _Result
```

```dax
Total Sales Current Week =
CALCULATE(
    [Total Sales],
    KEEPFILTERS('Date Table'[WeeknYear] = MAX('Date Table'[WeeknYear]) )
)
```

```dax
Total Sales Previous Week =
CALCULATE(
    [Total Sales],
    KEEPFILTERS('Date Table'[WeeknYear] = MAX('Date Table'[WeeknYear]) - 1 )
)
```

```dax
WOW diff % =
DIVIDE(
    ([Total Sales Current Week] - [Total Sales Previous Week]),
    [Total Sales Previous Week]
)
```

```dax
Formatted KPI % WoW =
VAR _Result =
SWITCH( 
    TRUE(),
    [WOW diff %] >= 0 , "▲",
    [WOW diff %] < 0 , "▼"
)
Return _Result
```

```dax
max date =
MAX( Sales[Sales Date] )
```

**Expected:** Measures compile without errors.

**Checklist:**
- [ ] `Formatted KPI % MOM` returns values
- [ ] `Total Sales Current Week` returns values
- [ ] `Total Sales Previous Week` returns values
- [ ] `WOW diff %` returns values
- [ ] `Formatted KPI % WoW` returns values
- [ ] `max date` returns values

## 29. Measures: Median of Dates, Total Orders, Orders Current Week…

**Objective:** Create DAX measures in dependency order.

**Prerequisites:** measure-03

### Actions
1. Modeling → New table → name it `# Measures` (hide later).
1. New measure for each formula below (home table `# Measures` unless noted).
1. Set format strings where specified in checklist.

### DAX
```dax
Median of Dates =
VAR _table = FILTER( ALLSELECTED('Date Table'), 'Date Table'[Date] <= [max date] )
VAR _Result = MEDIANX( _table , [Total Sales] )
RETURN _Result
```

```dax
Total Orders =
SUM( Sales[Order qty] )
```

```dax
Orders Current Week =
CALCULATE(
    [Total Orders],
    KEEPFILTERS('Date Table'[WeeknYear] = MAX('Date Table'[WeeknYear]) )
)
```

```dax
Orders Current month =
VAR _datetable =
 DATESINPERIOD( 
    'Date Table'[Date], MAX(Sales[Sales Date]), -1, MONTH )
VAR _result =
CALCULATE(
    [Total Orders],
    _datetable
    )
RETURN _result
```

```dax
Orders Previous month =
VAR _datetable =
 DATESINPERIOD( 
    'Date Table'[Date], MAX(Sales[Sales Date]), -1, MONTH )
VAR _result =
CALCULATE(
    [Total Orders],
    PREVIOUSMONTH(_datetable)
    )
RETURN _result
```

```dax
Orders MOM diff % =
DIVIDE(
    ([Orders Current month] - [Orders Previous month]),
    [Orders Previous month]
)
```

**Expected:** Measures compile without errors.

**Checklist:**
- [ ] `Median of Dates` returns values
- [ ] `Total Orders` returns values
- [ ] `Orders Current Week` returns values
- [ ] `Orders Current month` returns values
- [ ] `Orders Previous month` returns values
- [ ] `Orders MOM diff %` returns values

## 30. Measures: Orders KPI % MOM, Orders Previous Week, Orders WOW diff %…

**Objective:** Create DAX measures in dependency order.

**Prerequisites:** measure-04

### Actions
1. Modeling → New table → name it `# Measures` (hide later).
1. New measure for each formula below (home table `# Measures` unless noted).
1. Set format strings where specified in checklist.

### DAX
```dax
Orders KPI % MOM =
VAR _Result =
SWITCH( 
    TRUE(),
    [Orders MOM diff %] >= 0 , "▲",
    [Orders MOM diff %] < 0 , "▼"
)
Return _Result
```

```dax
Orders Previous Week =
CALCULATE(
    [Total Orders],
    KEEPFILTERS('Date Table'[WeeknYear] = MAX('Date Table'[WeeknYear]) - 1 )
)
```

```dax
Orders WOW diff % =
DIVIDE(
    ([Orders Current Week] - [Orders Previous Week]),
    [Orders Previous Week]
)
```

```dax
Orders KPI % WoW =
VAR _Result =
SWITCH( 
    TRUE(),
    [Orders WOW diff %] >= 0 , "▲",
    [Orders WOW diff %] < 0 , "▼"
)
Return _Result
```

```dax
Total Cost =
SUMX(
    Sales,
    Sales[Order qty] * Sales[unit cost] 
)
```

```dax
Total Profit =
[Total Sales] - [Total Cost]
```

**Expected:** Measures compile without errors.

**Checklist:**
- [ ] `Orders KPI % MOM` returns values
- [ ] `Orders Previous Week` returns values
- [ ] `Orders WOW diff %` returns values
- [ ] `Orders KPI % WoW` returns values
- [ ] `Total Cost` returns values
- [ ] `Total Profit` returns values

## 31. Measures: Profit Margin %, Target +0.2 of Previous month, Target vs Previous month…

**Objective:** Create DAX measures in dependency order.

**Prerequisites:** measure-05

### Actions
1. Modeling → New table → name it `# Measures` (hide later).
1. New measure for each formula below (home table `# Measures` unless noted).
1. Set format strings where specified in checklist.

### DAX
```dax
Profit Margin % =
DIVIDE(
    [Total Profit],
    [Total Sales]
    )
```

```dax
Target +0.2 of Previous month =
([TS PM Previous] + ([TS PM Previous] * 0.2 ) )
```

```dax
Target vs Previous month =
DIVIDE( [TS PM Current],
      [Target +0.2 of Previous month] )
```

```dax
Target Diff =
IF( [Target +0.2 of Previous month] >= [TS PM Current] ,
    1 - [Target vs Previous month],
    0
    )
```

```dax
Target Format =
FORMAT( [Target +0.2 of Previous month] / 1000000 , "$#.00M")
```

```dax
This Month Sales =
FORMAT( [TS PM Current] / 1000000 , "$#.00M")
```

**Expected:** Measures compile without errors.

**Checklist:**
- [ ] `Profit Margin %` returns values
- [ ] `Target +0.2 of Previous month` returns values
- [ ] `Target vs Previous month` returns values
- [ ] `Target Diff` returns values
- [ ] `Target Format` returns values
- [ ] `This Month Sales` returns values

## 32. Measures: Title dynamic, Toast CSS, Toast Notification…

**Objective:** Create DAX measures in dependency order.

**Prerequisites:** measure-06

### Actions
1. Modeling → New table → name it `# Measures` (hide later).
1. New measure for each formula below (home table `# Measures` unless noted).
1. Set format strings where specified in checklist.

### DAX
```dax
Title dynamic =
VAR _selected = SELECTEDVALUE( 'Date M-W-D'[Date M-W-D Order] )
VAR _result =
SWITCH(
    TRUE(),
    _selected = 0, "day",
    _selected = 1, "week",
    _selected = 2, "month",
    "day"
)
RETURN _result
```

```dax
Toast CSS =
"
#toastBox {
  display: flex;
  align-items: center;
  position: fixed;
  top: 0;              /* stick to the very top */
  left: 0;             /* align left edge */
  bottom: 0;             /* align left edge */
  width: 100vw;        /* full viewport width */
  padding: 16px 16px;
  background-color: #484848;
  border: 1px solid grey;
  border-radius: 8px 0px 0px 8px;
  box-shadow: 0px 4px 8px 0px rgba(0, 0, 0, 0.2),
  font-family: sans-serif;
  font-size: 16px;
  z-index: 9999;       /* sits on top of nearly everything */
  opacity: 0;
  animation: slideInOut 3.5s ease forwards;
}

.Category p {
  margin: 0;
  line-height: 1.4;
  color: #fff;
  font-weight: bold;
}

.textInfo {
   font-size: 13px;
   color: rgba(255, 255, 255, 0.75);
   font-style: normal;
}

/* Slide from right → stay → slide to left */
@keyframes slideInOut {
  0% {
    opacity: 0;
    transform: translateX(100%);
  }
  10% {
    opacity: 1;
    transform: translateX(0);
  }
  90% {
    opacity: 1;
    transform: translateX(0);
  }
  100% {
    opacity: 0;
    transform: translateX(-100%);
  }
}

"
```

```dax
Toast Notification =
VAR _Filter =
SWITCH(
    TRUE(),
    ISFILTERED(Products_Data) && COUNTX( VALUES(Products_Data[Product Name]),1)>1, "Products:" ,
    ISFILTERED(Products_Data) && COUNTX( VALUES(Products_Data[Product Name]),1)=1, "Product:" , //product
    ISFILTERED(storelocations) && COUNTX( VALUES( storelocations[name]),1)=1, "Store:",
    ISFILTERED(storelocations) && COUNTX( VALUES( storelocations[name]),1)>1, "Stores:", // store
    ISFILTERED(Salesteams)  && COUNTX( VALUES(Salesteams[Sales Team]),1)>1, "Sales Teams:",
    ISFILTERED(Salesteams)  && COUNTX( VALUES(Salesteams[Sales Team]),1)=1, "Sales Team:" // sales team
)

VAR _Value =
SWITCH(
    TRUE(),
    ISFILTERED(Products_Data), CONCATENATEX(Products_Data, Products_Data[Product Name], " - ", Products_Data[Product Name],ASC ),
    ISFILTERED(storelocations), CONCATENATEX( storelocations, storelocations[name], " - ", storelocations[name],ASC ),
    ISFILTERED(Salesteams), CONCATENATEX( Salesteams, Salesteams[Sales Team], " - ", Salesteams[Sales Team],ASC )
)

RETURN
IF( 
    NOT ISBLANK( _Filter) ,
    "<div id='toastBox'>
        <div class='Category'> 
            <p> <span class='textInfo'>Dashboard is filtered! &ensp; "&_Filter&"</span> "&_Value&" </p>
        </div>
    </div>"
)
```

```dax
Total profit fx =
[Total Profit]
```

```dax
another approach _ Total Sales PM =
IF( 
    [Total Sales] = BLANK(),
    BLANK(),
    CALCULATE(
        [Total Sales],
        PARALLELPERIOD('Date Table'[Date], -1, MONTH ) 
        )
)
```

```dax
avg monthly format =
FORMAT( [Average Monthly Saeles] / 1000000 , "$#.000M")
```

**Expected:** Measures compile without errors.

**Checklist:**
- [ ] `Title dynamic` returns values
- [ ] `Toast CSS` returns values
- [ ] `Toast Notification` returns values
- [ ] `Total profit fx` returns values
- [ ] `another approach _ Total Sales PM` returns values
- [ ] `avg monthly format` returns values

## 33. Measures: avg weekly format, blank, cost formatted…

**Objective:** Create DAX measures in dependency order.

**Prerequisites:** measure-07

### Actions
1. Modeling → New table → name it `# Measures` (hide later).
1. New measure for each formula below (home table `# Measures` unless noted).
1. Set format strings where specified in checklist.

### DAX
```dax
avg weekly format =
FORMAT( [Average Weekly Saeles] / 1000000 , "$#.000M")
```

```dax
blank =
BLANK()
```

```dax
cost formatted =
FORMAT( [Total Cost]/1000000, "$###.00M" )
```

```dax
profit formatted =
FORMAT( [Total Profit]/1000000, "$###.00M" )
```

```dax
rows_in_sales =
COUNTROWS(Sales)
```

**Expected:** Measures compile without errors.

**Checklist:**
- [ ] `avg weekly format` returns values
- [ ] `blank` returns values
- [ ] `cost formatted` returns values
- [ ] `profit formatted` returns values
- [ ] `rows_in_sales` returns values

# Stage 7: Page and slicers

Canvas and filters

## 34. Page size and header

**Objective:** Match 1280×780 canvas.

**Prerequisites:** measure-08

### Actions
1. View → Page view → 16:9.
1. Format page → Page size → Custom 1280×780.
1. Add title text box: Executive Sales.

**Expected:** Match 1280×780 canvas.

## 35. Store slicer

**Objective:** Filter by store name.

**Prerequisites:** page-01

### Actions
1. Insert → Slicer → Field **storelocations[name]**.
1. Rename header Stores; slicer style dropdown; position top-right.

### Visual (slicer)
Fields: storelocations[name]

**Expected:** Filter by store name.

## 36. Sales Team slicer

**Objective:** Filter by team.

**Prerequisites:** page-02

### Actions
1. Slicer on **Salesteams[Sales Team]**.
1. Place beside Stores slicer.

### Visual (slicer)
Fields: Salesteams[Sales Team]

**Expected:** Filter by team.

## 37. Product slicer

**Objective:** Filter products.

**Prerequisites:** page-03

### Actions
1. Slicer on **Products_Data[Product Name]**.

### Visual (slicer)
Fields: Products_Data[Product Name]

**Expected:** Filter products.

# Stage 8: KPI cards and bars

KPIs, cost/profit and target bars

## 38. Total Sales card

**Objective:** Primary revenue KPI.

**Prerequisites:** page-04

### Actions
1. Card visual → Field **Total Sales**.
1. Add adjacent card or callout with **Formatted KPI % WoW** for arrow comparison.

### Visual (card)
Fields: Total Sales, Formatted KPI % WoW

**Expected:** Primary revenue KPI.

## 39. Profit Margin % card

**Objective:** Margin KPI with comparisons.

**Prerequisites:** kpi-01

### Actions
1. Card → **Profit Margin %**.
1. Format as percentage.

### Visual (card)
Fields: Profit Margin %

**Expected:** Margin KPI with comparisons.

## 40. Units Sold card (measure: Total Orders)

**Objective:** Show units sold; reference PBIX titles this Total Orders.

**Prerequisites:** kpi-02

### Actions
1. Create measure **Total Orders** = `SUM(Sales[Order qty])` (already in measure steps).
1. Card → **Total Orders**; set visual title to **Units Sold** for clarity.
1. Reference report keeps the Total Orders label — both refer to the same units-sold logic.

### Visual (card)
Fields: Total Orders

**Expected:** Show units sold; reference PBIX titles this Total Orders.

## 41. Target achievement card

**Objective:** Monthly target %.

**Prerequisites:** kpi-03

### Actions
1. Card → **Target vs Previous month**; format as percentage.
1. Target basis: prior-month sales + 20% (see Target +0.2 of Previous month).

### Visual (card)
Fields: Target vs Previous month

**Expected:** Monthly target %.

## 42. Cost vs profit bar

**Objective:** 100% stacked composition bar.

**Prerequisites:** kpi-04

### Actions
1. Insert → 100% stacked bar chart.
1. Values: **Total Cost**, **Total Profit**.
1. Data labels: **cost formatted**, **profit formatted**.

### Visual (hundredPercentStackedBarChart)
Fields: Total Cost, Total Profit

**Expected:** 100% stacked composition bar.

## 43. Target remainder bar

**Objective:** Achievement vs gap bar (not cost/profit).

**Prerequisites:** kpi-05

### Actions
1. Use **Target vs Previous month** and **Target Diff** in a separate bar visual.
1. Format colors to match reference achievement/remainder story.

### Visual (clusteredColumnChart)
Fields: Target vs Previous month, Target Diff

**Expected:** Achievement vs gap bar (not cost/profit).

# Stage 9: Trend and settings

Trend line and percentile controls

## 44. Sales trend line

**Objective:** Line chart with conditional color.

**Prerequisites:** kpi-06

### Actions
1. Line chart → Axis: **Date M-W-D** parameter.
1. Values: **Total Sales**.
1. Line color → fx → **Color Formatting Line Chart**.

### Visual (lineChart)
Fields: Total Sales, Color Formatting Line Chart

**Expected:** Line chart with conditional color.

## 45. Percentile slicers

**Objective:** Trend band thresholds.

**Prerequisites:** trend-01

### Actions
1. Slicers on **Higher Percentile[Higher Percentile]** and **Lower Percentile[Lower Percentile]**.

### Visual (slicer)
Fields: Higher Percentile, Lower Percentile

**Expected:** Trend band thresholds.

# Stage 10: Toast

HTML Content notification

## 46. Add HTML Content visual

**Objective:** Toast host visual.

**Prerequisites:** trend-02

### Actions
1. Insert → HTML Content.
1. Place full width near top; send to front.

### Visual (htmlContent443BE3AD55E043BF878BED274D3A6855)
Fields: —

**Expected:** Toast host visual.

## 47. Bind toast measures

**Objective:** HTML content + stylesheet.

**Prerequisites:** toast-01

### Actions
1. Values well → **Toast Notification**.
1. Format → Stylesheet → **Toast CSS** (fix box-shadow closing parenthesis).

### Visual (htmlContent443BE3AD55E043BF878BED274D3A6855)
Fields: Toast Notification, Toast CSS

**Expected:** HTML content + stylesheet.

## 48. Filter trigger tests

**Objective:** Toast follows slicers, not targets.

**Prerequisites:** toast-02

### Actions
1. No filters → no toast.
1. Single product / store / team → singular label.
1. Multiple values → plural label; products take priority over store/team in _Filter DAX.
1. Replay animation by changing filters after toast hides (~3.5s).

**Expected:** Toast follows slicers, not targets.

# Stage 11: Interactions

Bookmarks and buttons

## 49. Bookmarks and buttons

**Objective:** Panel states for settings/calendar/trend.

**Prerequisites:** toast-03

### Actions
1. View → Bookmarks → add bookmarks with these **display names** (reference PBIX):
1. **Top Selected**, **Bottom Selected**, **Show date**, **Hide date**, **--Show settings**, **--Hide settings**, **( pag2 show calender**, **( page2 close calende**.
1. For each bookmark, update **Data** → uncheck Data and capture **Selected visuals** visibility only where needed.
1. Assign action buttons (settings / calendar / trend PNG assets) to **Bookmark** actions pointing to the matching bookmark.

**Expected:** Panel states for settings/calendar/trend.

# Stage 12: Final checks

Validate, save, export

## 50. Unfiltered KPI baseline

**Objective:** Match documented aggregates.

**Prerequisites:** interact-01

### Actions
1. Clear slicers.
1. Compare measures to `expected-results.json` → `displayCurrency` (2dp, reconciled profit).

**Expected:** See expected-results.json displayCurrency block.

**Checklist:**
- [ ] Measures compile
- [ ] Refresh succeeds
- [ ] Profit = Sales − Cost at display precision

## 51. Save and reopen

**Objective:** Persistence check.

**Prerequisites:** final-01

### Actions
1. Save PBIX, close Desktop, reopen and refresh.

**Expected:** Persistence check.
