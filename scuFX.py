# Import modules
import arcpy
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os, sys, datetime, traceback

# Set overwrite option so that existing data may be overwritten
arcpy.env.overwriteOutput = True

def printMsg(msg):
   arcpy.AddMessage(msg)
   print msg

def printWrng(msg):
   arcpy.AddWarning(msg)
   print 'Warning: ' + msg

def printErr(msg):
   arcpy.AddError(msg)
   print 'Error: ' + msg

def multiMeasure(meas, multi):
   '''Given a measurement string such as "100 METERS" and a multiplier, multiplies the number by the specified multiplier, and returns a new measurement string along with its individual components'''
   parseMeas = meas.split(" ") # parse number and units
   num = float(parseMeas[0]) # convert string to number
   units = parseMeas[1]
   num = num * multi
   newMeas = str(num) + " " + units
   measTuple = (num, units, newMeas)
   return measTuple

def delineatePolyCatchments(in_Feats, fld_ID, in_FlowDir, out_Catch, maxDist = '500 METERS', out_Scratch = 'in_memory'):
   """Delineates catchments individually for each polygon in feature class or layer, out to a maximum distance"""
   # Get cell size and output spatial reference from in_FlowDir
   cellSize = (arcpy.GetRasterProperties_management(in_FlowDir, "CELLSIZEX")).getOutput(0)
   srRast = arcpy.Describe(in_FlowDir).spatialReference
   linUnit = srRast.linearUnitName
   printMsg('Cell size of flow direction raster is %s %ss' %(cellSize, linUnit))
   printMsg('Catchment delineation is strongly dependent on cell size.')

   # Set environment setting and other variables
   arcpy.env.snapRaster = in_FlowDir
   dist, units, procDist = multiMeasure(maxDist, 3)

   # Check if input features and input flow direction have same spatial reference.
   # If so, just make a copy. If not, reproject features to match raster.
   srFeats = arcpy.Describe(in_Feats).spatialReference
   if srFeats.Name == srRast.Name:
      printMsg('Coordinate systems for features and raster are the same. Copying...')
      arcpy.CopyFeatures_management (in_Feats, out_Catch)
   else:
      printMsg('Reprojecting features to match raster...')
      # Check if geographic transformation is needed, and handle accordingly.
      if srFeats.GCS.Name == srRast.GCS.Name:
         geoTrans = ""
         printMsg('No geographic transformation needed...')
      else:
         transList = arcpy.ListTransformations(srFeats,srRast)
         geoTrans = transList[0]
      arcpy.Project_management (in_Feats, out_Catch, srRast, geoTrans)

   # Create an empty list to store IDs of features that fail to get processed
   myFailList = []

   # Set up processing cursor and loop
   cursor = arcpy.da.UpdateCursor(out_Catch, [fld_ID, "SHAPE@"])
   for row in cursor:
      try:
         # Extract the unique ID and geometry object
         myID = row[0]
         myShape = row[1]

         printMsg('Working on feature %s' %str(myID))

         # Process:  Select (Analysis)
         # Create a temporary feature class including only the current feature
         selQry = "%s = %s" % (fld_ID, str(myID))
         tmpFeat = out_Scratch + os.sep + 'tmpFeat'
         arcpy.Select_analysis (out_Catch, tmpFeat, selQry)

         # Convert feature to raster
         printMsg('Converting feature to raster...')
         srcRast = out_Scratch + os.sep + 'srcRast'
         arcpy.PolygonToRaster_conversion (tmpFeat, fld_ID, srcRast, "MAXIMUM_COMBINED_AREA", fld_ID, cellSize)

         # Restrict processing area to avoid ridiculous processing time
         procBuff = out_Scratch + os.sep + 'procBuff'
         printMsg('Buffering feature to set maximum processing distance')
         arcpy.Buffer_analysis (tmpFeat, procBuff, procDist, "", "", "ALL", "")
         myExtent = str(arcpy.Describe(procBuff).extent).replace(" NaN", "")
         printMsg('Extent: %s' %myExtent)
         clp_FlowDir = out_Scratch + os.sep + 'clp_FlowDir'
         printMsg('Clipping flow direction raster to processing buffer')
         arcpy.Clip_management (in_FlowDir, myExtent, clp_FlowDir, procBuff, "", "ClippingGeometry")
         arcpy.env.extent = clp_FlowDir

         # Create catchment
         printMsg('Delineating catchment...')
         catchRast = Watershed (clp_FlowDir, srcRast)
         catchRast.save(out_Scratch + os.sep + 'catchRast')

         # Convert catchment to polygon
         printMsg('Converting catchment to polygon...')
         catchPoly = out_Scratch + os.sep + 'catchPoly'
         arcpy.RasterToPolygon_conversion (catchRast, catchPoly, "NO_SIMPLIFY")

         # Clip the catchment to the maximum distance buffer
         clipBuff = out_Scratch + os.sep + 'clipBuff'
         printMsg('Clipping catchment to maximum distance...')
         arcpy.Buffer_analysis (tmpFeat, clipBuff, maxDist, "", "", "ALL", "")
         clipCatch = out_Scratch + os.sep + 'clipCatch'
         arcpy.Clip_analysis (catchPoly, clipBuff, clipCatch)

         # Use the catchment geometry as the final shape
         myFinalShape = arcpy.SearchCursor(clipCatch).next().Shape

         # Update the feature with its final shape
         row[1] = myFinalShape
         cursor.updateRow(row)

         printMsg('Finished processing feature %s' %str(myID))
         
         # Reset extent, because Arc is stupid.
         arcpy.env.extent = "MAXOF"

      except:
         # Add failure message and append failed feature ID to list
         printMsg("\nFailed to fully process feature " + str(myID))
         myFailList.append(myID)

         # Error handling code swiped from "A Python Primer for ArcGIS"
         tb = sys.exc_info()[2]
         tbinfo = traceback.format_tb(tb)[0]
         pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n " + str(sys.exc_info()[1])
         msgs = "ARCPY ERRORS:\n" + arcpy.GetMessages(2) + "\n"

         printWrng(msgs)
         printWrng(pymsg)
         printMsg(arcpy.GetMessages(1))

         # Add status message
         printMsg("\nMoving on to the next feature.  Note that the output will be incomplete.")
   return out_Catch


# Use the main function to run the catchment function directly from Python IDE with hard-coded variables
def main():
   # Set up your variables here
   in_Feats = r'C:\Users\xch43889\Documents\Working\SCU_prioritization\SCUs20170724.shp\dk_1500912213976.shp'
   fld_ID = 'lngID'
   in_FlowDir = r'H:\Backups\DCR_Work_DellD\GIS_Data_VA_proc\Finalized\NHDPlus_Virginia.gdb\fdir_VA'
   out_Catch = r'C:\Users\xch43889\Documents\Working\SCU_prioritization\SCU_work.gdb\scuCatch'
   maxDist = '1000 METERS'
   out_Scratch = 'in_memory'
   # End of user input

   delineatePolyCatchments(in_Feats, fld_ID, in_FlowDir, out_Catch, maxDist, out_Scratch)

if __name__ == '__main__':
   main()