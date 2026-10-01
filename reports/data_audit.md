# Data audit

{
  "crop_raw": {
    "rows": 2200,
    "columns": [
      "N",
      "P",
      "K",
      "temperature",
      "humidity",
      "ph",
      "rainfall",
      "label"
    ],
    "missing": {
      "N": 0,
      "P": 0,
      "K": 0,
      "temperature": 0,
      "humidity": 0,
      "ph": 0,
      "rainfall": 0,
      "label": 0
    },
    "duplicates": 0,
    "dtypes": {
      "N": "int64",
      "P": "int64",
      "K": "int64",
      "temperature": "float64",
      "humidity": "float64",
      "ph": "float64",
      "rainfall": "float64",
      "label": "str"
    }
  },
  "production_raw": {
    "rows": 175628,
    "columns": [
      "state",
      "district",
      "crop",
      "year",
      "season",
      "area",
      "production",
      "yield"
    ],
    "missing": {
      "state": 0,
      "district": 0,
      "crop": 0,
      "year": 1,
      "season": 0,
      "area": 4,
      "production": 2559,
      "yield": 2559
    },
    "duplicates": 0,
    "dtypes": {
      "state": "str",
      "district": "str",
      "crop": "str",
      "year": "str",
      "season": "str",
      "area": "float64",
      "production": "float64",
      "yield": "float64"
    }
  },
  "ambiguous_key_rows_excluded": 0,
  "crop_clean": {
    "rows": 2200,
    "columns": [
      "N",
      "P",
      "K",
      "temperature",
      "humidity",
      "ph",
      "rainfall",
      "label"
    ],
    "missing": {
      "N": 0,
      "P": 0,
      "K": 0,
      "temperature": 0,
      "humidity": 0,
      "ph": 0,
      "rainfall": 0,
      "label": 0
    },
    "duplicates": 0,
    "dtypes": {
      "N": "int64",
      "P": "int64",
      "K": "int64",
      "temperature": "float64",
      "humidity": "float64",
      "ph": "float64",
      "rainfall": "float64",
      "label": "str"
    }
  },
  "production_clean": {
    "rows": 51679,
    "columns": [
      "state",
      "district",
      "crop",
      "year",
      "season",
      "area",
      "production",
      "yield"
    ],
    "missing": {
      "state": 0,
      "district": 0,
      "crop": 0,
      "year": 0,
      "season": 0,
      "area": 0,
      "production": 0,
      "yield": 0
    },
    "duplicates": 0,
    "dtypes": {
      "state": "string",
      "district": "string",
      "crop": "string",
      "year": "int64",
      "season": "string",
      "area": "float64",
      "production": "float64",
      "yield": "float64"
    }
  },
  "excluded_units": [
    "cotton (bales)",
    "jute (bales)",
    "coconut (nuts)"
  ],
  "crop_counts": {
    "rice": 100,
    "maize": 100,
    "chickpea": 100,
    "kidneybeans": 100,
    "pigeonpeas": 100,
    "mothbeans": 100,
    "mungbean": 100,
    "blackgram": 100,
    "lentil": 100,
    "pomegranate": 100,
    "banana": 100,
    "mango": 100,
    "grapes": 100,
    "watermelon": 100,
    "muskmelon": 100,
    "apple": 100,
    "orange": 100,
    "papaya": 100,
    "coconut": 100,
    "cotton": 100,
    "jute": 100,
    "coffee": 100
  },
  "regional_crop_counts": {
    "rice": 11018,
    "maize": 9851,
    "moong": 7154,
    "urad": 6683,
    "gram": 5539,
    "arhar (tur)": 5460,
    "masoor": 2930,
    "banana": 2295,
    "moth": 749
  },
  "years": [
    1998,
    2012
  ],
  "cleaning": "Exact duplicates removed; conflicting keys excluded, never summed; plausible yield extremes retained."
}

Regional source is a pre-cleaned community copy attributed to the Government of India. Raw means unchanged downloaded snapshot, not original government records. Units for retained crops follow publisher documentation. Historical boundaries are not harmonised. Existing source yield was ignored and recomputed. No statistical clipping or synthetic rows.
