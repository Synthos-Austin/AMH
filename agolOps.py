"""This class is designed for a series of short cut methods utilizing the ArcGIS API for Python. Dependancies are imported just below
these module comments consistent with PEP 8. This class also requires user crednetials and these fields have end-line comments to notate
where user input is required before use. Please refer to the associated readme.txt for further information on using this module."""
#dependencies
import pandas as pd
from arcgis.gis import GIS
from arcgis import features
from arcgis.features import GeoAccessor, GeoSeriesAccessor
import string
import random

class arcOps:
    def __init__(self, layerID, subType= 'layer', subPos = 0, updateType=None, data=None): #set default to grab sublayer 0 with no defined update data
        __url = 'https://EXAMPLE.maps.arcgis.com' #must define agol portal url
        __un = 'ExampleUN' #must define account username for agol portal
        __pw = 'ExamplePW!' #must define account pw for agol portal
        print('---Attempting to connect to AGOL portal and create arcOps instance---')
        self.gis = GIS(__url, __un, __pw)
        gis= self.gis
        if gis.content.search(query=layerID):
            self.layerID = layerID
            self.obj = gis.content.search(layerID)[0]
            print("---Connected to AGOL portal & layer is valid---")
            print(gis.content.search(layerID)[0])
        else:
            raise Exception('Layer does not exist or you do not have permission to access this layer')
        
        upTypes = ['CSV', 'DataFrame', None]
        if updateType == 'CSV':
            if data[-4:] == ".csv":
                print('Layer is staged for updates using the defined CSV: ' + data)
            else:
                raise Exception("Data does not contain a valid '.csv' extension")
        elif updateType == "DataFrame":
            print('Layer is staged for updates using the defined DataFrame\n' + data.head())
        elif updateType == None:
            print('An update type has not been defined for this layer, you can still perform other operations')
        else:
            raise Exception("This class only supports update types of 'CSV' or 'DataFrame")
        self.updateType = updateType
        self.data = data
        gen = ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
        self.upKey = gen
        obj = self.obj
        if subType == 'layer':
            subObj = obj.layers[subPos]
            print(subObj)
        elif subType == 'table':
            subObj == obj.tables[subPos]
            print(subObj)
        else:
            raise Exception("Defined sublayer type must be 'layer' or 'table'")
        self.subObj = subObj
    

    def uploadData(self, locType = None, x_col= "LONGITUDE", y_col = "LATITUDE", field_map= None):
        gis = self.gis
        subObj = self.subObj
        name = subObj.properties.name
        if self.updateType == 'CSV':
            csv = self.data
            upKey = self.upKey
            upProps = {
                "title": upKey + "_" + csv[:-4],
                "description": "Temp update file for " + name,
                "type": "CSV"
            }
            print('---Attempting to upload data to AGOL---')
            upItem = gis.content.add(upProps, csv)
            print('---Data uploaded to AGOL---')
            if locType == 'xy':
                print('---Attempting to publish as spatially enabled service---')
                if field_map != None:
                    publish_parameters = {
                        "type": "csv",
                        "name": upKey + "_" + csv[:-4] + "HFL",
                        "locationType": "coordinates",
                        "latitudeFieldName": y_col,
                        "longitudeFieldName": x_col,
                        "layerInfo": {"fields": field_map},
                        "maxRecordCount": 2500,
                        "columnDelimiter": ",",
                        "sourceSR": {
                            "wkid": 4326,
                            "latestwkid": 4326
                        },
                        "targetSR": {
                            "wkid": 4326,
                            "latestwkid": 4326
                        },
                        "dateFieldsTimeReference": "Pacific Standard Time"
                    }
                    result = upItem.publish(publish_parameters)
                    print("---CSV is published as a spatial feature service and is ready for append operations---")
                    return result
                elif field_map == None:
                    print("WARNING: field map has not been defined for your spatial data set - the service will publish with default datatypes")
                    result = upItem.publish()
                    print("---CSV is published as a spatial feature service and is ready for append operations---")
                    return result
                else:
                    raise Exception("Unknown Erorr Occured - Please Review Inputs")
            elif locType == None:
                print("---CSV is uploaded and ready for append operations---")
                return upItem
            else:
                raise Exception("Error: arcOps object does not support '" + locType + "' location types")
        if self.updateType == 'DataFrame':
            if locType == None:
                raise Exception("Error: DataFrame objects are not supported without XY data")
            elif locType == 'xy':
                print("---Attempting to publish spatially enabled service---")
                df = self.data
                upKey = self.upKey
                sedf = pd.DataFrame.spatial.from_xy(df=df, x_column=x_col, y_column=y_col, sr=4326)
                result = sedf.spatial.to_featurelayer(upKey + "_TempUpdateFor_" + name)
                print("---Spatial feature service is published and ready for append operations---")
                return result
            else:
                raise Exception("Error: arcOps object does not support '" + locType + "' location types")
    def getPublishedFieldMap(self):
        subObj = self.subObj
        gis = self.gis

        result = subObj.properties.fields
        return result
    
    def createUploadFieldMap(self):
        updateType = self.updateType
        data = self.data
        print('---Getting Published Field Map to use as template---')
        hfields = self.getPublishedFieldMap()
        hdf = pd.DataFrame(hfields).set_index('name').T
        hset = set(hdf.columns)

        print("---Producing field map for upload---")
        if updateType == 'CSV':
            ldf = pd.read_csv(data)
            lset = set(ldf.columns)
        elif updateType == 'DataFrame':
            ldf = data
            lset = set(ldf.columns)

        diff = hset.difference(lset)
        hdfDrop = hdf.drop(columns=diff)
        hdfOrg = hdfDrop[ldf.columns]
        result = hdfOrg.to_dict('records')
        print("---Field Map for up load created---")
        return result

# new = arcOps('a97ba784634849abb8244b985615e838')
# new2 = arcOps('4363fe0733e54bd2980a1f87bc58b35f')
# print(new.upKey)
# print(new2.upKey)

