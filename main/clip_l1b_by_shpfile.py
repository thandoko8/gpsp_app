import os
import rasterio
from matplotlib import pyplot
from osgeo import gdal

def clip_l1b_by_shpfile(filename, shpfile, output_tiff, display_process=True, need_reprojection=True, tmp_clip_dir='test/'):
    tmp_tiff = tmp_clip_dir + "raster.tif"

    if not os.path.exists(tmp_clip_dir):
        os.makedirs(tmp_clip_dir)

    if need_reprojection:
        tmp_str_cmd_tiff = 'gdal_translate -a_srs EPSG:4326 -of GTiff "{l1b_name}" {target_name}'
        target_cmd_tiff = tmp_str_cmd_tiff.format(l1b_name=filename, target_name=tmp_tiff)
        print(target_cmd_tiff)
        if display_process:
            print("Command OS with:", target_cmd_tiff)
        output_file = tmp_tiff

        src_ds = gdal.Open(filename)

        # Specify options
        options = gdal.TranslateOptions(
            format="GTiff",
            outputType=gdal.GDT_Float32,  # Change the output data type as needed  # Specify the bounding box
            projWinSRS="EPSG:4326",  # Specify the projection of the bounding box
            noData=0  # Set nodata value
        )

        # Perform translation
        output = gdal.Translate(output_file, src_ds, options=options)

        # Close the dataset
        src_ds = None
        filename = tmp_tiff
        # if output != 0:
        #     if display_process:
        #         print("Command OS failed")
        #     return
        # else:
        #     if display_process:
        #         print("Command OS successful")
        #     filename = tmp_tiff

    tmp_str_cmd_clip_tiff = 'gdalwarp -overwrite -of GTiff -cutline "{source_shp_path}"  -crop_to_cutline  "{source_raster_path}" "{output_raster_path}"'
    target_str_cmd_clip_tiff = tmp_str_cmd_clip_tiff.format(source_shp_path=shpfile, source_raster_path=filename, output_raster_path=output_tiff)
    if display_process:
        print("Command OS with:", target_str_cmd_clip_tiff)
    source_shp_path = shpfile
    source_raster_path = filename
    output_raster_path = output_tiff

    # Open the source raster dataset
    src_ds = gdal.Open(source_raster_path)

    # Define options
    options = gdal.WarpOptions(
        format="GTiff",                # Output format
        cutlineDSName=source_shp_path, # Path to the shapefile defining the cutline
        cropToCutline=True,            # Crop the output to the cutline extent
        dstSRS="EPSG:4326"              # Overwrite existing output file if it exists
    )

    # Perform the warp operation
    output = gdal.Warp(output_raster_path, src_ds, options=options)

    # Close the source dataset
    src_ds = None
    if output != 0:
        if display_process:
            print("Command OS failed")
        return
    else:
        if display_process:
            print("Command OS successful")
    if display_process:
        src = rasterio.open(output_tiff)
        pyplot.imshow(src.read(1))
        pyplot.show()
