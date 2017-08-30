# ----------------------------------------------------------------------------------------
# SCU-Prioritization.py
# Version:  ArcGIS 10.3.1 / Python 2.7.8
# Creation Date: 2017-08-29
# Last Edit: 2017-08-29
# Creator(s):  Kirsten R. Hazler

# Summary:
# A script for prioritizing Stream Conservation Units (SCUs) for conservation.

# Usage Tips:
# Prior to running this script, need to delineate catchments (or truncated catchments) for each SCU.

# Dependencies:
# 

# Syntax:  
# 
# ----------------------------------------------------------------------------------------

# Import modules
import arcpy
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os, sys, datetime, traceback

# Data inputs
fc_SCU = r'C:\Users\xch43889\Documents\Working\SCU_prioritization\SCU_work.gdb\scu_albers'
# feature class delineating SCUs

fc_SCU-catch = # feature class with (truncated) catchments delineated for each SCU 

fld_ID = 'CONSERVATI'
# field containing SCU ID
# Will need to create new field converting this to long integer

fld_BRANK = 'BIODIV_SIG'
# field containing SCU biodiversity rank

lo_BRANK = 'B2'
# lowest biodiversity rank to include in prioritization 
# make this a drop-down with 5 options

rd_wmInteg = # raster dataset representing watershed integrity from Watershed Model
lo_Integ = 75 # lowest watershed integrity value to include in prioritization
rd_wmConsPrior = # raster dataset representing conservation priority from Watershed Model
rd_vmVuln = # raster dataset representing vulnerability from Development Vulnerability Model

# Step 1: First cut based on BRANK: Create subset of SCUs ranked lo_BRANK or better
# Process: Select

# Step 2: For each SCU catchment corresponding to SCUs in subset, get zonal stats of Watershed Integrity, Conservation Priority and Vulnerability
# Process: Add fields (WtrshdInteg, ConsPrior, and Vuln)
# Set up cursor for loop
for s in SCUs:
   # Process: Select (catchment)
   # Process: Zonal statistics by table (Watershed Integrity)
   # Get mean value and update ConsPrior field
   # Process: Zonal statistics by table (Conservation Priority)
   # Get mean value and update ConsPrior field
   # Process: Zonal statistics by table (Vulnerability)
   # Get mean value and update Vuln field

# Step 3: Score catchments based on BRANK, Watershed Integrity, Conservation Priority, and Vulnerability, then rank



