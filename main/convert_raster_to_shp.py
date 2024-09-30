import os
import rasterio
import geopandas as gpd
from osgeo import gdal, ogr

def convert_raster_to_shp(raster_path, target_shp='shp_test', display_process=True):
    rasternya = rasterio.open(raster_path)
    band_num = rasternya.profile['count']

    tmp_cmd = 'gdal_polygonize.py "{input_raster}" -b {band_num} -f "GPKG" "{output_raster}" OUTPUT DN'
    
    # Looping to convert every band
    for band_index in range(1, band_num + 1):
        shp_name = f"{target_shp}_{band_index}.gpkg"
        target_cmd = tmp_cmd.format(input_raster=raster_path, band_num=band_index, output_raster=shp_name)
        if display_process:
            print("Command OS with:", target_cmd)

        # Open the input raster dataset
        src_ds = gdal.Open(raster_path)

        # Get the specified band
        band = src_ds.GetRasterBand(band_index)

        # Create an in-memory output vector dataset
        driver = ogr.GetDriverByName("GPKG")
        dst_ds = driver.CreateDataSource(shp_name)

        # Create a new layer in the output dataset
        layer_name = "OUTPUT"
        srs = None  # You can specify the spatial reference system if needed
        layer = dst_ds.CreateLayer(layer_name, srs=srs, geom_type=ogr.wkbPolygon)

        # Create the field for storing the DN values
        field_defn = ogr.FieldDefn("DN", ogr.OFTInteger)
        layer.CreateField(field_defn)

        # Perform polygonization
        options = ["8CONNECTED=8", "COMPUTE_STATS=NO", "NO_MASK=NO", "ADD_GEOJSON=NO"]  # You can adjust options as needed
        output = gdal.Polygonize(band, None, layer, 0, options=options)

        # Close datasets
        src_ds = None
        dst_ds = None

        if output != 0:
            if display_process:
                print("Command OS failed")
            continue
        else:
            if display_process:
                print("Command OS successful")
            if display_process:
                region = gpd.read_file(shp_name)
                region.plot()
