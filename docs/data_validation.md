# Data validation and panel diagnostics

## Table schemas

`TableSchema` and `ColumnRule` declare required columns, expected kinds, nullability, numeric
ranges, allowed values, unique keys, and whether undeclared columns are permitted.
`validate_schema` returns all detected issues in one report rather than failing at the first bad
cell. It does not coerce data silently.

```python
schema = TableSchema(
    "city_panel",
    columns=(
        ColumnRule("city", "string"),
        ColumnRule("year", "integer", minimum=2000, maximum=2100),
        ColumnRule("outcome", "numeric"),
        ColumnRule("treated", "integer", allowed=(0, 1)),
    ),
    unique_keys=(("city", "year"),),
    allow_extra_columns=False,
)
schema_report = validate_schema(data, schema)
```

`DataValidationReport` combines a schema result with optional merge and panel diagnostics and
exports machine-readable JSON plus CSV issue, coverage, variation, and unmatched-key tables.
The report is evidence about structural data quality; it does not decide whether missingness,
sample selection, measurement, or treatment assignment is substantively valid.

## Validated merges

Every merge should declare its expected key relationship: `one_to_one`, `one_to_many`,
`many_to_one`, or `many_to_many`. `merge_validated` rejects violated cardinality and missing
keys, reports unmatched rows on both sides, and can require complete matching from either
input. Many-to-many merges are permitted only when explicitly requested because they can
multiply observations.

```python
merged = merge_validated(
    outcomes,
    city_attributes,
    on="city_id",
    relationship="many_to_one",
    require_all_left=True,
)
```

The returned `MergeResult` contains both the merged frame and a `MergeReport`. Store the
report with analysis outputs rather than relying on a console-only merge message.

## Panel diagnostics

`diagnose_panel` reports duplicate and missing keys, balance, coverage, observations per
entity, singleton entities, time coverage, and variance decompositions for declared numeric
variables. Variables with zero within-entity variation are flagged as absorbed by entity
fixed effects; variables with zero within-time variation are flagged as absorbed by time
fixed effects.

The variance decomposition is diagnostic rather than a hypothesis test. Very small within
variation deserves substantive inspection even when it is not exactly zero. A balanced
panel is not automatically preferable: deleting observations solely to force balance can
change the target population and induce selection.

## 中文说明

Schema 用于事先声明列名、类型、是否允许缺失、取值范围、允许集合和唯一键；验证时一次报告全部问题，不自动修改原数据。`DataValidationReport` 可把 schema、合并和面板检查统一导出为 JSON/CSV。结构通过不等于数据在研究含义上可靠，缺失机制、样本选择、测量误差和处理分配仍需单独论证。
