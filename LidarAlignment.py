# The University of Texas at Austin, Bureau of Economic Geology
#
# Aaron Averett - May, 2023
#
# This code demonstrates the method used for aligning Chiroptera and IceSAT2 point cloud data by virtually reversing the drift of the sea ice that occurred between
# and during the overflights by the sensor platforms.

#Import some libs
import math
from pickle import NONE

#Define some constants
LASERTYPE_NIR=0
LASERTYPE_GREEN=1

#Input file path
inputDataPath = r"exampleChiropteraData.txt"
outputDataPath = r"exampleOutput.txt"

#Drift speed in meters per minute - this is converted to m/s later
driftMetersPerMinute = 2.11
driftBearing = 197

#An extra arbitrary adjustment in the drift bearing direction (in m), to allow adjustment for the limitations in accuracy of this approach.
#We can get in the ballpark by mathematically reversing the drift, but 
extraDrift = 6

atl07T0 = -1
atl07T1 = -1

#This indicates whether the overflights were conducted in the same or opposing direction
sameDirection = False

#This is used to account for slightly different data formats 
laserType=LASERTYPE_GREEN 
#ATL07 pass parameters for line 1

#Beginning and end time of IceSAT2 overflight of this area (in GPS seconds)
atl07T0 = 232571.1
atl07T1 = 232566.3

chiropteraT0 = -1
chiropteraT1 = -1
chiropteraTotalTime = -1

#Compute total duration of IceSAT2 pass
atl07TotalTime = atl07T1 - atl07T0

#Convert our drift speed to meters per second
driftMetersPerSecond = driftMetersPerMinute / 60.0

#Convert our drift bearing to radians, relative to due east.
driftPolarDir = 360 + (90.0 - driftBearing)

driftPolarDirRad = math.radians(driftPolarDir)

#Calculate the X and Y components of our drift velocity vector
driftXVel = math.cos(driftPolarDirRad) * driftMetersPerSecond
driftYVel = math.sin(driftPolarDirRad) * driftMetersPerSecond

#Calculate the X and Y components of our extra 
extraDriftX = math.cos(driftPolarDirRad) * extraDrift
extraDriftY = math.sin(driftPolarDirRad) * extraDrift

#Open up the input file and read the first and last lines
with open(inputDataPath, "r") as fh:

    lines = fh.readlines()

    firstLine = lines[0]

    lastLine = lines[len(lines) - 1]

    #Get the time from the first and last lines
    firstLineParts = firstLine.split(" ")
    chiropteraT0 = float(firstLineParts[1])
    
    lastLineParts = lastLine.split(" ")
    chiropteraT1 = float(lastLineParts[1])

    #Calculate total time.
    chiropteraTotalTime = chiropteraT1 - chiropteraT0
    
    #Open a write handle on our output path.
    with open(outputDataPath, "w") as ofh:

        #For each line in our INPUT path...
        for linecontent in lines:
        
            #Parse the line out into its components.
            c=None
            t=None
            x=None
            y=None
            z=None

            lineParts = linecontent.split(" ")

            if laserType == LASERTYPE_NIR:
                t = float(lineParts[0])
                x = float(lineParts[1])
                y = float(lineParts[2])
                z = float(lineParts[3])
            elif laserType == LASERTYPE_GREEN:
                c = int(lineParts[0])
                t = float(lineParts[1])
                x = float(lineParts[2])
                y = float(lineParts[3])
                z = float(lineParts[4])

            #The time, as a fraction of the total duration of the Chiroptera overflight, at which this point was measured.
            chiropteraTimeFraction = (t - chiropteraT0) / chiropteraTotalTime

            atl07TimeFraction = 0

            #If we're going the same direction, we use the same time fraction for IceSAT2.  If we're going opposite directions, we do 1 - time fraction.
            if sameDirection:
                atl07TimeFraction = chiropteraTimeFraction
            else:
                atl07TimeFraction = 1 - chiropteraTimeFraction

            atl07TimeOnTarget = atl07T0 + (atl07TotalTime * atl07TimeFraction)

            #Delta T is the time difference between Chiroptera actually hitting this spot and the ATL07 "hypothetically" hitting it.
            deltaT = t - atl07TimeOnTarget

            #Compute X and Y components of our ice drift vector
            chiropteraDeltaX = deltaT * driftXVel + extraDriftX
            chiropteraDeltaY = deltaT * driftYVel + extraDriftY

            #Compute the final X and Y position of our point, adjusted for reversal of the sea ice drift.           
            finalX = x - chiropteraDeltaX
            finalY = y - chiropteraDeltaY

            #Compute a time that represents when IceSAT2 would have hit this point, if it had a Chiroptera installed on it.
            tFinal = t + deltaT

            outLine = ""

            #Compose output data file line
            if laserType == LASERTYPE_NIR:
                outLine = "{0} {1} {2} {3}\n".format(str(tFinal), str(finalX), str(finalY), str(z))
            elif laserType == LASERTYPE_GREEN:
                outLine = "{0} {1} {2} {3} {4}\n".format(str(c), str(tFinal), str(finalX), str(finalY), str(z))

            #write our new line of data to the output file.
            ofh.write(outLine)
