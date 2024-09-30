import os
import geopandas as gpd
from osgeo import gdal
from metpy import io
from .clip_l1b_by_shpfile import clip_l1b_by_shpfile
from .convert_raster_to_shp import convert_raster_to_shp
from .get_metar_l1bfile import get_metar_l1bfile

def scraping_from_l1b(l1bfile):
    output_file = "OUTPUT_2.tif"
    # Open the input file
    src_ds = gdal.Open(l1bfile)
    # Specify options
    options = gdal.TranslateOptions(
        format="GTiff",
        outputType=gdal.GDT_Float32,  # Change the output data type as needed  # Specify the bounding box
        projWinSRS="EPSG:4326",  # Specify the projection of the bounding box
        noData=0  # Set nodata value
    )
    # Perform translation
    output = gdal.Translate(output_file, src_ds, options=options)
    if output != 0:
        print("Command OS failed")
    else:
        print("Command OS successful")

    station_shp_df = gpd.read_file("data_input/1_ProjectSatteliteData/dataset_station/batas_bandara.gpkg")

    print("Processing ", l1bfile)

    # Extract date from the filename
    filename = l1bfile.split('/')[-1]
    date_str = filename[0:10]
    date_arr = date_str.split('-')
    filename = filename.replace('.', '_')

    dataset_dir = filename + "/"
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)

    metarfile = dataset_dir + 'metarnya.txt'
    sat_image = l1bfile

    print("Processing ", sat_image)
    get_metar_l1bfile(sat_image, dataoutput=metarfile)

    # Parse METAR file
    metar_df = io.parse_metar_file(metarfile)

    # Loop through METAR data
    for index, met_row in metar_df.iterrows():
        print("Processing station:", met_row['station_id'])
        polygonnya = station_shp_df[station_shp_df['ICAO'] == met_row['station_id']]
        shp_path = dataset_dir + "tmp_station.gpkg"
        polygonnya.to_file(shp_path, layer='batas_kab', driver="GPKG")

        # Clip raster by shapefile
        tmp_kab_raster_path = dataset_dir + str(index) + ".tif"
        clip_l1b_by_shpfile(sat_image, shp_path, tmp_kab_raster_path, display_process=True, need_reprojection=True, tmp_clip_dir='test/')

        target_shp_raster = dataset_dir + str(index)

        # Convert raster to shapefile
        try:
            convert_raster_to_shp(tmp_kab_raster_path, target_shp=target_shp_raster, display_process=False)
            print("Processing station:", met_row['station_id'], "successful")
            polygonnya = station_shp_df[station_shp_df['ICAO'] == met_row['station_id']]
            polygonnya.to_file(shp_path, layer='batas_kab', driver="GPKG")
            tmp_kab_raster_path = dataset_dir + str(index) + ".tif"
            clip_l1b_by_shpfile(sat_image, shp_path, tmp_kab_raster_path, display_process=False, need_reprojection=True, tmp_clip_dir='test/')
            target_shp_raster = dataset_dir + str(index)
        except Exception as e:
            print("Error processing station:", met_row['station_id'], e)
            continue
