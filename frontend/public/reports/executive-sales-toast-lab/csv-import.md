# CSV import (student M)

1. **Home → Transform data → Manage Parameters → New** → name `DataFolder` (Text) → your extracted `data` folder path.
2. For each table below: **New Source → Blank Query**, paste M, rename query to **load name**, enable load.
3. Author Excel M in `power-query.json` is reference-only.

## Sales (`Sales.csv`)

```powerquery
let
    Source = Csv.Document(
        File.Contents(DataFolder & "\Sales.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
            {"Sales Date", type date},
            {"Order qty", Int64.Type},
            {"unit price", type number},
            {"unit cost", type number},
            {"Productindex", Int64.Type},
            {"Storeindex", Int64.Type},
            {"Salesteamindex", Int64.Type},
            {"Sales_Index", Int64.Type},
            {"Order Number", type text},
            {"Sales Channel", type text}
        })
in
    #"Changed Type"
```

## Date Table (`Date_Table.csv`)

```powerquery
let
    Source = Csv.Document(
        File.Contents(DataFolder & "\Date_Table.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
            {"Date", type date},
            {"Year", Int64.Type},
            {"QuarterOfYear", Int64.Type},
            {"Quarter & Year", type text},
            {"QuarternYear", Int64.Type},
            {"MonthOfYear", Int64.Type},
            {"Month & Year", type text},
            {"MonthnYear", Int64.Type},
            {"Month Short", type text},
            {"DayOfMonth", Int64.Type},
            {"ISO Weeknumber", Int64.Type},
            {"Week & Year", type text},
            {"WeeknYear", Int64.Type},
            {"DayOfWeekNum", Int64.Type},
            {"DayOfWeek", type text},
            {"DayOfWeek Initial", type text},
            {"Day Type", type text}
        })
in
    #"Changed Type"
```

## Products_Data (`Products_Data.csv`)

```powerquery
let
    Source = Csv.Document(
        File.Contents(DataFolder & "\Products_Data.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
            {"Productindex", Int64.Type},
            {"Product Name", type text}
        })
in
    #"Changed Type"
```

## storelocations (`storelocations.csv`)

```powerquery
let
    Source = Csv.Document(
        File.Contents(DataFolder & "\storelocations.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
            {"Storeindex", Int64.Type},
            {"name", type text}
        })
in
    #"Changed Type"
```

## Salesteams (`Salesteams.csv`)

```powerquery
let
    Source = Csv.Document(
        File.Contents(DataFolder & "\Salesteams.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
            {"Salesteamindex", Int64.Type},
            {"Sales Team", type text}
        })
in
    #"Changed Type"
```

## Higher Percentile (`Higher_Percentile.csv`)

```powerquery
let
    Source = Csv.Document(
        File.Contents(DataFolder & "\Higher_Percentile.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
            {"Higher Percentile", type number}
        })
in
    #"Changed Type"
```

## Lower Percentile (`Lower_Percentile.csv`)

```powerquery
let
    Source = Csv.Document(
        File.Contents(DataFolder & "\Lower_Percentile.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
            {"Lower Percentile", type number}
        })
in
    #"Changed Type"
```

## Date M-W-D (`Date_M-W-D.csv`)
_Helper lookup only — recreate the real Fields parameter in Desktop (see workshop date-03)._

```powerquery
let
    Source = Csv.Document(
        File.Contents(DataFolder & "\Date_M-W-D.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
            {"Date M-W-D", type text},
            {"Date M-W-D Order", Int64.Type}
        })
in
    #"Changed Type"
```
