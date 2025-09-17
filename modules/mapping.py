# modules/mapping.py
# Placeholder mapping functions for Sprint-1.
# In Sprint-2 we'll replace / extend these to return Folium maps or GeoJSON.

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
