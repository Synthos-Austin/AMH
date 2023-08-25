def initializeUpdateValidation():
    from arcgis.gis import GIS
    print("---Attempting to connect to GIS Portal---")
    gis = GIS('https://ah4r.maps.arcgis.com/', 'mraghfar_admin', 'Esri_AH4R_2022!') #connects to GIS using your credentials
    print('---Connected---')
    print
    assetid = 'f9d8e4bb87cf4ce19cc62fb2eef99a0f' #hosted container ID for asset layer
    assetparent = gis.content.get(assetid) #retrieves hosted container through GET request
    afl = assetparent.layers[0] #retrieves layer of interest from container
    zipid = '71acc9d03d154b5ca595b6a00bb644e1' #hoster container ID for zip layer
    zipparent = gis.content.get(zipid) #retrieves container through GET request
    ztab = zipparent.tables[0] #retrieves specific table of interest
    return gis, afl, ztab #returns values for use in remaining module functions
    
def checkAssets(gis, afl, assetCSV):
    #importing dependencies for funcion scope
    import pandas as pd
    from arcgis.gis import GIS
    from arcgis import features
    from arcgis.features import GeoAccessor, GeoSeriesAccessor

    print("---attempting to query hosted layers and create dataframes---")
    hdf = afl.query().df #creates dataframe from hosted asset layer (hdf = hosted dataframe)
    hset = set(hdf) #creates set from hosted asset layer (hset = hosted set)
    print("---hosted layer converted to DF---")
    ldf = pd.read_csv(assetCSV) #creates dataframe from downloaded asset CSV (ldf = local data frame)
    lset = set(ldf) #creates set from downloaded asset CSV (lset = local set)

    hdf2 = hdf.drop(columns=[a for a in hset.difference(lset)]) #drops extra AGOL columns from the hosted dataframe
    ldf2 = ldf.astype(hdf2.dtypes.to_dict()) #converts datatypes in local datarfame to match hosted data frame for comparison
    print("---stored CSV converted to DF---")
    
    print("---Checking for matched and unmatched values in Assets---")
    rlst = [] #opens empty list to store inidvidual column comparison results
    for col in ldf.columns: #iterate over columns
        test = ldf2[col].isin(hdf2[col]).value_counts() #iterate over  values in columns and return matches as test[True} and unmatched as test[False] - does not handle NaN/<null> values well
        try:
            if type(test[False]) == numpy.int64: #if there were any unmatched records perform this action - includes NaN and <null> values
                result = "\n" + str(col) + ":" "\n---At Least One Record Did Not Match - INSPECT TABLE--- \nMatched: " + str(test[True]) + "\nUnmatched: " + str(test[False])
                rlst.extend(result) #appends result string to list
        except KeyError: #if no unmatched results returned - KeyError is raised - all records matched - perform this action
            result = "\n" + str(col) + ":" "\n---All Record Matched--- \nMatched: " + str(test[True]) + "\nUnmatched: 0"
            rlst.extend(result) #appends result to list
    print("---Check Complete---")
    print("---Creating Compared Table View---")
    ldf3 = ldf2[hdf2.columns] #reorders local data frame columns to match hosted dataframe
    ldf4 = ldf3.set_index('PROPERTY').sort_index() #defines unique value column as index and sorts descending alphabetically in local dataframe
    hdf3 = hdf2.set_index('PROPERTY').sort_index() #defines unique value column as index and sorts descending alphabetically in hosted dataframe

    assetCompTable = ldf4.compare(hdf3)#sotres comparison table for review of unmatched records as dataframe object
    assetCheckLog = ''.join(rlst) #stores result log as plain text in variable
    return assetCheckLog, assetCompTable #returns variables to be used in storeResults() function

def checkZip(gis, ztab, zipCSV):
    #import dependencies for function scope
    import pandas as pd
    from arcgis.gis import GIS
    from arcgis import features
    from arcgis.features import GeoAccessor, GeoSeriesAccessor

    print("---attempting to query hosted layers and create dataframes---")
    hdf = ztab.query().df #creates dataframe from hosted zip table (hdf = hosted data frame)
    hset = set(hdf) #creates set from hosted zip table (hset = hosted set)
    print("---hosted layer converted to DF---")
    ldf = pd.read_csv(zipCSV) #creates dataframe from locally stored zip CSV (ldf = local dataframe)
    lset = set(ldf) #creates set from locally stored zip CSV (lset - local set)

    hdf2 = hdf.drop(columns=[a for a in hset.difference(lset)]) #drops extra AGOL columns from hosted dataframe
    ldf2 = ldf.astype(hdf2.dtypes.to_dict()) #converts data types in local data frame to match hoster dataframe
    print("---stored CSV converted to DF---")
    
    print("---Checking for matched and unmatched values in Assets---")
    rlst = [] #opens list object to store restuls of column checks
    for col in ldf.columns: #iterate over columns in local data frame
        test = ldf2[col].isin(hdf2[col]).value_counts() #iterate over  values in columns and return matches as test[True} and unmatched as test[False] - does not handle NaN/<null> values well
        try:
            if type(test[False]) == numpy.int64: #if there were any unmatched records perform this action - includes NaN and <null> values
                result = "\n" + str(col) + ":" "\n---At Least One Record Did Not Match - INSPECT TABLE--- \nMatched: " + str(test[True]) + "\nUnmatched: " + str(test[False])
                rlst.extend(result) # store result of column comparison in list
        except KeyError: #if no unmatched results returned - KeyError is raised - all records matched - perform this action
            result = "\n" + str(col) + ":" "\n---All Record Matched--- \nMatched: " + str(test[True]) + "\nUnmatched: 0"
            rlst.extend(result) #stores result of column comparison in list
    print("---Check Complete---")
    print("---Creating Compared Table View---")
    ldf3 = ldf2[hdf2.columns] #reorders local dataframe columns to match hosted dataframe
    ldf4 = ldf3.set_index('AFFGEOID10').sort_index() #defines unique value column as index and sorts descending alphabetically in local dataframe
    hdf3 = hdf2.set_index('AFFGEOID10').sort_index() #defines unique value column as index and sorts descending alphabetically in in hosted dataframe

    zipCompTable = ldf4.compare(hdf3) #stores comparison table of local and hosted records as dataframe object
    zipCheckLog = ''.join(rlst) #stores log result of individual column comparison as plain text (str)
    return zipCheckLog, zipCompTable # returns results for use in storeResults() function

def storeResults(assetCheckLog, assetCompTable, zipCheckLog, zipCompTable):
    #import dependencies for function scope
    import pandas as pd
    import datetime
    from datetime import datetime

    now = datetime.now() #define date string for use in filenames
    stamp = now.strftime("%d-%m-%Y")

    print("---Attempting to store Results---")
    asset_log = open(r"C:\Users\Austin\OneDrive\Documents\SynthosGIS\american_home_rentals\test_bin\testASSET" + stamp + ".txt", "w+") #stores asset plain text log in new text files 

    with asset_log as f:
        f.write(assetCheckLog)
    asset_log.close()

    assetsCompCSV = assetCompTable.to_csv(r"C:\Users\Austin\OneDrive\Documents\SynthosGIS\american_home_rentals\test_bin\testASSET" + stamp + ".csv") #stores asset comparison table as CSV

    zip_log = open(r"C:\Users\Austin\OneDrive\Documents\SynthosGIS\american_home_rentals\test_bin\testZIP" + stamp + ".txt", "w+") #store zip plain text log in new text file

    with zip_log as f:
        f.write(zipCheckLog)
    zip_log.close()
    zipCompCSV = zipCompTable.to_csv(r"C:\Users\Austin\OneDrive\Documents\SynthosGIS\american_home_rentals\test_bin\testZIP" + stamp + ".csv")#stores zip comparison table as CSV
    print("---All Results Stored Successfully---")
    print("---All Results Stored Successfully---")

    return asset_log, assetCompCSV, zip_log, zipCompCSV #returns files as variables to be used for attaching to email thorugh smtplib or similar
            
from arcgis.gis import GIS               
        
assetCSV = r"C:\Users\Austin\Downloads\Zip_Level_Data_DateRange_2022-07-01_2023-06-30_RunDate_2023-08-07\Assets_Level_Data_DateRange_2022-07-01_2023-06-30_RunDate_2023-08-07.csv"#define path to csv
zipCSV = r"C:\Users\Austin\Downloads\Zip_Level_Data_DateRange_2022-07-01_2023-06-30_RunDate_2023-08-07\Zip_Level_Data_DateRange_2022-07-01_2023-06-30_RunDate_2023-08-07.csv" #define path to csv

gis, afl, ztab = initializeUpdateValidation()

assetCheckLog, assetCompTable = checkAssets(gis, afl, assetCSV)

zipCheckLog, zipCompTable = checkZip(gis, ztab, zipCSV)

storeResults(assetCheckLog, assetCompTable, zipCheckLog, zipCompTable)


