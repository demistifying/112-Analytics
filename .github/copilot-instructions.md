# Copilot Instructions for 112-Analytics

## Project Overview
This project analyzes emergency call data (CSV in `data/112_calls_synthetic.csv`) for Goa Police, focusing on geospatial and categorical analysis of incidents (crime, medical, accident, women_safety, etc.). The main code is in `app.py` and the `modules/` directory.

## Architecture & Data Flow
- **Data Loading:**
  - Use `modules/data_loader.py` to load and preprocess CSV data.
- **Analysis:**
  - `modules/analysis.py` contains analytical routines (e.g., aggregations, trends).
- **Mapping & Visualization:**
  - `modules/mapping.py` provides Pydeck-based map visualizations: scatter, heatmap, and 3D hexbin (HexagonLayer) for spatial hotspot analysis.
  - The 3D hexbin map uses latitude/longitude and incident category to show call density as extruded towers.

## Key Patterns & Conventions
- **DataFrame Columns:**
  - Latitude: `caller_lat`, Longitude: `caller_lon`, Category: `category`, Jurisdiction: `jurisdiction`.
- **Visualization:**
  - Use `clean_df_for_pydeck()` to prepare data for mapping.
  - For 3D hexbin, use `pydeck_hexbin_map()`. Adjust `radius` and `elevation_scale` for tower sharpness/height.
  - Color and tooltip customization is handled in the Pydeck layer config.
- **Adding New Map Types:**
  - Add new functions to `modules/mapping.py` following the pattern of existing map functions.

## Developer Workflows
- **Run the app:**
  - Main entry is likely `app.py` (check for Streamlit or Flask usage).
- **Dependencies:**
  - Install with `pip install -r requirements.txt`.
- **Data:**
  - Place new data files in `data/` and update loader logic if schema changes.

## Integration Points
- **Pydeck** is used for all mapping. No Folium/GeoJSON output yet (planned for Sprint-2).
- **Data is expected as Pandas DataFrames** throughout modules.

## Example: Creating a 3D Hexbin Map
```python
from modules import mapping
import pandas as pd

df = pd.read_csv('data/112_calls_synthetic.csv')
deck = mapping.pydeck_hexbin_map(df)
deck.show()
```

## Troubleshooting
- If 3D towers are not sharp or meaningful, tune `radius` and `elevation_scale` in `pydeck_hexbin_map()`.
- Ensure latitude/longitude columns are floats and not NaN.

---
For more details, see `modules/mapping.py` and the project abstract PDF.
