import glob
import pandas as pd
from metpy import io
import os
from rasterio.plot import show
import rasterio
from matplotlib import pyplot
import matplotlib.pyplot as plt
import numpy as np
#import gdal
from osgeo import gdal,gdal_array, gdalnumeric, ogr, osr
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
from geopandas import points_from_xy
import time

#Function for Generate TB
def generateTB(x, v):
    #Variable to E
    s = -0.160156
    i = 159.088867

    #calculate E
    e = x*s+i

    #variable to TB
    c2 = 1.438833
    c1 = (1.1910659)*(10**-5)

    #Cek sama atau ngga, kalau tidak sama nanti di visualisasi dihilangkan saja yg temperature

    #calculate Tb
    tb = (c2 * v) / (np.log(1+(c1*(v**3)/e)))

    #convert Kelvin to Celcius
    tb = tb - 273

    return tb
    
def predict_process(l1bfile, callback):
    callback("Prediction process started for " + l1bfile)
    # Parsing tanggal dan waktu dari nama file l1bfile
    filename_parts = l1bfile.split()  # Memisahkan berdasarkan spasi
    date_part = filename_parts[0]  # Mengambil bagian tanggal "02-01-2021"
    time_part = filename_parts[1]  # Mengambil bagian waktu "0619"
    
    # Mengubah format time_part menjadi HH:MM:SS
    time_part = f"{time_part[:2]}:{time_part[2:]}:00"  # Mengubah "0619" menjadi "06:19:00"
    
    # Gabungkan tanggal dan waktu ke dalam format yang diinginkan
    new_datetime = f"{date_part} {time_part}"  # Format menjadi "02-01-2021 06:19:00"
    folder_l1b = [l1bfile]

    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)

    first_data = True
    missing_file = []
    length_sat_image = len(folder_l1b)
    checked_sat_image = 0

    for foldernya in folder_l1b:
        ## Get It Metar File
        metarnya = foldernya + "/metarnya.txt"
        is_metar_ada = os.path.isfile(metarnya)
        if is_metar_ada == False:
            print(foldernya)
            print("File Metar Tidak Ditemukan")
            missing_file.append(metarnya)
            continue
        print(foldernya)
        databaru = io.parse_metar_file(metarnya)
        
        print(":: Checking for Layer File ::")
        length_station = len(databaru.index)
        checked_station = 0
        gaining_data_1 = pd.DataFrame(columns=['band_0', 'band_1', 'band_2', 'band_3', 'band_4'])
        for index, station_ in databaru.iterrows():
            tmp_layer = []
            layer_pixel_max = [0, 0, 0, 0, 0]
            for layer in range(0, 5):
                layernya = foldernya + "/" + str(station_["station_id"]) + "_" + str(layer + 1) + ".gpkg"
                is_file_ada = os.path.isfile(layernya)
                if is_file_ada == False:
                    print(foldernya)
                    missing_file.append(layernya)
                    ## Create missing Pixels in dataframe
                    layer_pixel_max[layer] = None
                    continue
                else:
                    print("-- Processing ", str(station_["station_id"]) + "_" + str(layer + 1) + ".gpkg")
                    try:
                        df_shp_station = gpd.read_file(layernya)
                    except:
                        continue
                    jumlah_pixel = len(df_shp_station)
                    largest_pixel = 0
                    no_data_pixel = 0
                    if jumlah_pixel == 1:
                        ## Uncovered Detected
                        layer_pixel_max[layer] = None
                        continue
                    else:
                        layer_pixel_max[layer] = df_shp_station['DN'].max()
            gaining_data_1.loc[index] = layer_pixel_max
            checked_station = checked_station + 1
            print("Checked Station : ", checked_station, "/", length_station)

        databaru[['band_0', 'band_1', 'band_2', 'band_3', 'band_4']] = gaining_data_1

        if first_data:
            huge_csv = databaru
            first_data = False
        else:
            huge_csv = pd.concat([huge_csv, databaru], axis=0)

        print('Banyak Station ', len(databaru.index))
        print('Banyak gaining ', len(gaining_data_1.index))

        checked_sat_image = checked_sat_image + 1
        print("Checked Sat Image : ", checked_sat_image, "/", length_sat_image)
        print(foldernya, " is Done ")

    for missing_filenya in missing_file:
        print(missing_filenya)

    huge_csv.to_csv('hugecsv.csv')


    # metar_file = io.parse_metar_file('/content/metar.txt')
    metar_file = pd.read_csv("hugecsv.csv")
    metar_file = metar_file.set_index(["station_id"], drop=True)
    metar_file = metar_file.fillna("")
    metar_file = metar_file[metar_file.latitude != ""]
    metar_file = metar_file[metar_file.band_0 != ""]
    metar_file = metar_file.fillna(0)
    metar_file = metar_file[metar_file.band_0 != 0]
    # metar_file = metar_file.fillna(0)
    # metar_file = metar_file.fillna(0)


    # metar_file = metar_file[metar_file.longitude != np.nan]
    metar_file
    cloudtype_columns = ["station_id", "cloud_type", "predicted_CB"]
    cloudtype_data = []

    metar_file['band_0'] = pd.to_numeric(metar_file['band_0'], errors='coerce')
    metar_file['band_1'] = pd.to_numeric(metar_file['band_1'], errors='coerce')
    metar_file['band_2'] = pd.to_numeric(metar_file['band_2'], errors='coerce')

    for index, row in metar_file.iterrows():
        predicted_CB_t = ""
        predicted_CB = (row["band_0"] + row["band_1"] + row["band_2"] + row["band_1"]) / 4
        if predicted_CB > 500:
            predicted_CB_t = "CB"
        else:
            predicted_CB_t = "NonCB"

        if str(row["remarks"]).__contains__("CB"):
            cloudtype_data.append([index, "CB", predicted_CB_t])
        else:
            cloudtype_data.append([index, "NonCB", predicted_CB_t])

    cloudtype = pd.DataFrame(cloudtype_data, columns=cloudtype_columns)
    cloudtype = cloudtype.set_index(["station_id"], drop=True)

    print(cloudtype)

    metar_file["cloud_type"] = cloudtype["cloud_type"]
    metar_file["predicted"] = cloudtype["predicted_CB"]

    # metar_file
    gdf = gpd.GeoDataFrame(
        metar_file, geometry=gpd.points_from_xy(metar_file.longitude, metar_file.latitude)
    )
    gdf.plot()
    gdf[gdf["cloud_type"] == "CB"]
    
    metar_file.to_csv("data_input/DataFinal.csv")
    df = pd.read_csv("data_input/DataFinal.csv")

    # Mengubah format kolom 'date_time' menggunakan nilai new_datetime
    df['date_time'] = pd.to_datetime(new_datetime, format='%d-%m-%Y %H:%M:%S')

    # Memformat 'date_time' menjadi DD/MM/YYYY HH:MM:SS
    df['date_time'] = df['date_time'].dt.strftime('%d/%m/%Y %H:%M:%S')

    # Simpan kembali file CSV dengan perubahan yang sesuai
    df.to_csv("data_input/DataFinal.csv", index=False)
    for col in metar_file.columns:
        print(col)
    # Generate TB with choose NOAAA for param
    noaa15 = 925.4075
    noaa18 = 928.146
    noaa19 = 928.9

    list_tb = []

    for band3 in metar_file['band_3']:
        if "NOAA19" in l1bfile:
            tb = generateTB(band3, noaa19)
        elif "NOAA18" in l1bfile:
            tb = generateTB(band3, noaa18)
        else:
            tb = generateTB(band3, noaa15)
        list_tb.append(format(tb, '.2f'))

    print(list_tb)

    metar_file["tbc"] = list_tb

    #Tb Kelvin
    list_tbk = []
    for tbc in metar_file['tbc']:
        tbc = float(tbc)
        tbc += 273
        list_tbk.append(format(tbc, '.2f'))

    metar_file["tbk"] = list_tbk

    list_color = []

    for predicted, cloudType in zip(metar_file['predicted'], metar_file['cloud_type']):
        if (predicted == "NonCB") & (cloudType == "NonCB"):
            list_color.append("blue")
        elif (predicted == "CB") & (cloudType == "CB"):
            list_color.append("red")
        elif (predicted == "CB") & (cloudType == "NonCB"):
            list_color.append("orange")
        elif (predicted == "NonCB") & (cloudType == "CB"):
            list_color.append("green")

    metar_file["color"] = list_color

    # open dataset
    ds = gdal.Open('OUTPUT_2.tif')
    print(":: GeoTransform ::")
    print(ds.GetGeoTransform())
    # print(":: GCPS ::")
    # display(ds.GetGCPs())
    print(":: GetGCPProjection ::")
    print(ds.GetGCPProjection())
    print(":: GetProjection ::")
    print(ds.GetProjection())
    # print(":: GetSpatialRef ::")
    # display(ds.GetSpatialRef())

    # # ds_1 = gdal_array.DatasetReadAsArray(ds)
    ds_1 = ds.ReadAsArray()
    print(ds_1[0])

    ### ALGORITMA THRESHOLD ###
    ocb = np.logical_and( ((ds_1[0] + ds_1[1] + ds_1[2] + ds_1[3])/4)  > 500,True )
    ocb  = ocb.astype(float)

    # temp_ = ocb * ds_1[3]
    temp_ = ocb * (159.088867 - 0.160156*(0.2989 * ds_1[0]+0.5879*ds_1[1]+0.1140*ds_1[2]))
    temp_ = ocb * (159.088867 - 0.160156*(0.2989 * ds_1[0]+0.5879*ds_1[1]+0.1140*ds_1[2]))
    
    #Rumus ini disesuaikan dengan fungsi generateTB
    # Inputnya disesuaikan noaa berapa
    c2 = 1.438833
    if "NOAA19" in l1bfile:
        v = noaa19
    elif "NOAA18" in l1bfile:
        v = noaa18
    else:
        v = noaa15
    c1 = 1.191*0.00001
    temp_ = 1 + ((c1*v*v*v)/temp_)
    temp_ = np.log(temp_)
    temp_=(c2*v)/temp_
    temp_ = temp_.astype('uint16')
    ocb = ocb * 100
    ocb = ocb.astype('uint16')


    # com = np.logical_and( ds_1[0]  <= 500,ds_1[0]  > 300)
    # com  = com.astype(float)
    # com = com * 50
    # com  = com .astype('uint16')
    # ocb = ocb+com
    print(ocb)
    print(temp_)

    with open('img.txt', 'w') as f:
        for x in ds_1[0]:
            for y in x:
                f.write(str(y)+ "\t")
            f.write("\n")
    with open('ocb.txt', 'w') as f:
        for x in ocb:
            for y in x:
                f.write(str(y)+ "\t")
            f.write("\n")
    with open('temperature.txt', 'w') as f:
        for x in temp_:
            for y in x:
                f.write(str(y) + "\t")
            f.write("\n")

    newRasterfn = 'test_22.tif'
    newRasterfn_temp = 'test_22_temp.tif'

    cols = ocb.shape[1]
    rows = ocb.shape[0]
    # originX = rasterOrigin[0]
    # originY = rasterOrigin[1]

    ## Generate CB CLoud Detection
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Byte)
    outRaster.SetGeoTransform(gdal.GCPsToGeoTransform(ds.GetGCPs()))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(ocb)
    outband.SetNoDataValue = np.nan
    # outRaster.SetProjection('')
    outband.FlushCache()
    outband = None
    outRaster=None

    ## Generate Channel 4 Band
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    outRaster = driver.Create(newRasterfn_temp, cols, rows, 1, gdal.GDT_UInt16)
    outRaster.SetGeoTransform(gdal.GCPsToGeoTransform(ds.GetGCPs()))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(temp_)
    outband.SetNoDataValue = np.nan
    # outRaster.SetProjection('')
    outband.FlushCache()
    outband = None
    outRaster=None

    src_1 = rasterio.open("OUTPUT_2.tif")
    src = rasterio.open("test_22.tif")
    src_temp = rasterio.open("test_22_temp.tif")

    # fig, (axsrc,axcb, axtemp) = plt.subplots(1,3, figsize=(210,70))
    fig, (axsrc,axcb, axtemp) = plt.subplots(1,3, figsize=(42,14))

    show(src_1, ax=axsrc, title='Citra Satelit')
    show((src, 1), ax=axcb, cmap='Blues', title='Posisi Awan CB')
    show((src_temp, 1), ax=axtemp, cmap='Reds', title='Channel 4 Temperatur AWAN CB')
    plt.savefig("data_input/satellite_images.png")  # Save the combined image
    plt.close(fig)

    # Input raster and output GeoPackage paths
    input_raster = "test_22.tif"
    output_gpkg = "test_22.gpkg"
    # Open the input raster dataset
    src_ds = gdal.Open(input_raster)
    # Create an output vector dataset
    driver = ogr.GetDriverByName("GPKG")
    dst_ds = driver.CreateDataSource(output_gpkg)
    # Get the first band of the raster
    band = src_ds.GetRasterBand(1)
    # Create a layer in the output GeoPackage
    layer_name = "OUTPUT"
    srs = None  # You can specify the spatial reference system if needed
    layer = dst_ds.CreateLayer(layer_name, srs=srs, geom_type=ogr.wkbPolygon)
    # Add a field for the DN values
    field_defn = ogr.FieldDefn("DN", ogr.OFTInteger)
    layer.CreateField(field_defn)
    # Perform polygonization
    options = ["8CONNECTED=8", "COMPUTE_STATS=NO", "NO_MASK=NO", "ADD_GEOJSON=NO"]  # Adjust options as needed
    output = gdal.Polygonize(band, None, layer, 0, options=options)
    # Close datasets
    src_ds = None
    dst_ds = None

    vektornya = gpd.read_file('test_22.gpkg')
    # vektornya_3 = gpd.read_file('/content/test_22.gpkg')
    batas = gpd.read_file('data_input/1_ProjectSatteliteData/Batas_Kab_Indonesia-2020/Batas_Kab_Indonesia_2020.shp')
    # batas.plot()
    # vektornya.plot()

    vektornya_2 = vektornya.loc[vektornya["DN"] != 0]
    # vektornya_2.plot()

    fig, (ax1) = plt.subplots(1, 1, figsize=(60, 40))
    batas.boundary.plot(ax=ax1, color="green")
    vektornya_2.plot(ax=ax1, color="purple")
    gdf.plot(ax=ax1,color="blue")
    ax1.set_title("Posisi Awan CB", fontsize=20)
    ax1.set_axis_off()
    plt.savefig("data_input/posisi_cb.png")  # Save the combined image
    plt.close(fig)


    m = folium.Map(tiles='CartoDB positron')

    
    taxi_gdf = gpd.GeoDataFrame(
        metar_file, crs="EPSG:4326",
        geometry=points_from_xy(
            metar_file["longitude"], metar_file["latitude"]
        ),
    )
    # taxi_gdf.drop(columns=taxi_gdf.columns[31], axis=1, inplace=True)
    taxi_gdf.fillna("")
    taxi_gdf.drop(columns=taxi_gdf.columns[4], axis=1, inplace=True)
    taxi_gdf.drop(columns=taxi_gdf.columns[0], axis=1, inplace=True)

    for _, r in metar_file.iterrows():
        lat = r['latitude']
        lon = r['longitude']
        folium.Marker(location=[lat, lon],popup=
                        'ICAO: {}<br>Cloud Type: {}<br>Long: {}<br>Lat: {}<br>Band_0: {}<br>Band_1: {}<br>Band_2: {}<br>Band_3: {}<br>Band_4: {}<br>Predicted: {} <br>Tb(Celcius): {} <br>Tb(Kelvin): {}'
                        .format(_,
                                r['cloud_type'],
                                r['longitude'],
                                r['latitude'],
                                #r['latitude'],
                                r['band_0'],
                                r['band_1'],
                                r['band_2'],
                                r['band_3'],
                                r['band_4'],
                                r['predicted'],
                                r['tbc'],
                                r['tbk']
                                #r['temperature']
                                ),
                        icon=folium.Icon(color=r['color'])
                        ).add_to(m)

    m.save("data_input/folium_map.html")
    m.save("main/templates/data_input/folium_map.html")
    callback("Prediction process completed.")

#predict_process("02-01-2021 0619 NOAA19_L1B")
