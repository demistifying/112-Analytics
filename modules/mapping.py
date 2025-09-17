# modules/mapping.py
# Placeholder mapping functions for Sprint-1.
# In Sprint-2 we'll replace / extend these to return Folium maps or GeoJSON.
import folium
from folium.plugins import HeatMap
import pandas as pd

def create_point_geojson(df, lat_col="caller_lat", lon_col="caller_lon", properties=None):
    """
    Create a simple GeoJSON FeatureCollection (dict) of points.
    properties: list of columns to include as properties for each feature
    """
    features = []
    if properties is None:
        properties = []

    for _, row in df.iterrows():
        lat = row.get(lat_col)
        lon = row.get(lon_col)
        if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
            continue
        props = {p: (row.get(p) if p in row else None) for p in properties}
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
            "properties": props
        }
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}


def generate_base_map(center=(15.5, 74.0), zoom_start=9):
    return folium.Map(location=center, zoom_start=zoom_start, tiles="cartodbpositron")

def plot_points_on_map(df, lat_col="caller_lat", lon_col="caller_lon"):
    m = generate_base_map()
    for _, row in df.iterrows():
        if pd.notna(row[lat_col]) and pd.notna(row[lon_col]):
            try:
                folium.CircleMarker(
                    location=[float(row[lat_col]), float(row[lon_col])],
                    radius=3,
                    color="blue",
                    fill=True,
                    fill_opacity=0.6,
                    popup=f"Category: {row.get('category','')} | Jurisdiction: {row.get('jurisdiction','')}"
                ).add_to(m)
            except Exception:
                continue
    return m

def plot_heatmap(df, lat_col="caller_lat", lon_col="caller_lon"):
    m = generate_base_map()
    # Drop NA and ensure float
    df_coords = df[[lat_col, lon_col]].dropna()
    df_coords[lat_col] = pd.to_numeric(df_coords[lat_col], errors="coerce")
    df_coords[lon_col] = pd.to_numeric(df_coords[lon_col], errors="coerce")
    df_coords = df_coords.dropna()

    heat_data = df_coords[[lat_col, lon_col]].values.tolist()
    if len(heat_data) > 0:
        HeatMap(heat_data, radius=12, blur=15, max_zoom=13).add_to(m)
    else:
        folium.Marker(
            location=(15.5, 74.0),
            popup="No valid coordinates for current filters"
        ).add_to(m)
    return m
