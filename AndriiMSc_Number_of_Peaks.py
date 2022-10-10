from sqlite3 import connect
import pandas as pd
import os

from calculations import *
from scipy.signal import find_peaks
from scipy.signal import savgol_filter
from matplotlib import pyplot as plt

import gui

def main(sensorLocation, files = []):

    plt.rcParams["figure.figsize"] = [30,15]
    plt.rcParams['xtick.direction'] = 'out'

    #specify path to the directory with files (same folder as this script by default)
    NR_OF_FILES_TO_ANALYZE = len(files)
    i = 0
    acceleration = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    new_acceleration = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    time = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    peaks_array_higher = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    peaks_array_lower = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    peaks_array_filtered = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    new_peaks = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    new_peaks_29 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    indx_array = [1,1,1,1,1]
    profile_match_array = [1,1,1,1,1]
    acceleration_29 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    new_acceleration_29 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]

    location = sensorLocation

    if location == "Ankle":
        y = 14
    elif location == "Shank":
        y = 13
    elif location == "Foot":
        y = 16

    b = y

    def Plot(i):
        plt.plot(acceleration[i], label = str(location) +' '+str(i))
        plt.plot(acceleration[i][peaks_array_lower[i]], '.', markersize = 20)
        plt.grid(True, 'both')
        plt.suptitle(str(location) + " " + str(i), fontsize='30')
        plt.legend()
        plt.show()

    def SavGol_39 (i):
        #applying the Sav_Gol filter
        ACC_filtered = savgol_filter(df.averagea, 39, 3)
        #the filtered signal is stored into an array
        acceleration_29[i] = ACC_filtered
        #time[i] = df.time
        return acceleration_29[i]

    #uploading the files    
    for file in files:
        
        df = pd.read_csv(file)
        df.columns = ['stamp','battery', 'pressure','temperature','ax','ay','az','gx','gy','gz','mx','my','mz']
            
        #Calculate magnitudes
        magnitudes = []
        for idx,x in enumerate( df['ax']):
            y = df['ay'][idx]
            z = df['az'][idx]
            magnitudes.append(calculateMagnitude(x,y,z))
        #Add averagea column with the calculated data
        df.insert(len(df.columns),"averagea" ,magnitudes)
            
        #Calculate timestamps
        beginTime = df['stamp'][0]
        timestamps = []
        for idx,stamp in enumerate(df['stamp']):
            timestamps.append(timeStampToSeconds(stamp,beginTime))
        #Insert the calculated times
        df.insert(0,'time',timestamps)
        acceleration[i] = df.averagea
        time[i] = df.time
        acceleration_29[i] = SavGol_39(i)
        i += 1
        gui.confirmSave(df)
            

    #find the peaks in raw data (HSs)
    i = 0
    for i in range(0,NR_OF_FILES_TO_ANALYZE):
        peaks,_ = find_peaks(acceleration[i], height=30)
        peaks_array_higher[i]=peaks
        i += 1
    #find the peaks in raw data
    i = 0
    for i in range(0,NR_OF_FILES_TO_ANALYZE):
        peaks,_ = find_peaks(acceleration[i], height=y)
        peaks_array_lower[i]=peaks
        i += 1
    #find all peaks in the filtered data    
    i = 0
    for i in range (0,NR_OF_FILES_TO_ANALYZE):
        peaks,_ = find_peaks(acceleration_29[i], height=y)
        peaks_array_filtered[i]=peaks
        i += 1

    #chopping out the most similar dataset
    def DefineArray(i):
        print (peaks_array_higher[i])
        print (peaks_array_lower[i])
        plt.plot(acceleration[i])
        plt.axhline(y=16, color = 'r')
        plt.axhline(y=35, color = 'r')
        plt.suptitle('Acceleration ' + str(i), fontsize='30')
        plt.grid(True, 'both')
        plt.show()

    #plot filtered and raa data and print identified peaks
    def Peaks(i): 
        print (peaks_array_lower[i])
        print("Number of peaks in Raw data: " + str(len(peaks_array_lower[i])))
        print (peaks_array_filtered[i])
        print("Number of peaks in Filtered data: " + str(len(peaks_array_filtered[i])))
        plt.plot(acceleration[i])
        plt.plot(acceleration_29[i], linewidth = '2')
        plt.axhline(y=b, linewidth = '3', color = 'r')
        plt.suptitle('Acceleration ' + str(i), fontsize='30')
        plt.grid(True, 'both')
        plt.show()

    #identify region of interest
    def Cut(i,start,end):
        new_acceleration[i] = acceleration[i][start:end]
        new_acceleration_29[i] = acceleration_29[i][start:end]
        return NewPeaks(i)
    #plot identfied region (raw and filtered data) and show number of peaks in this region
    def NewPeaks(i):
        new_peaks_acc,_ = find_peaks(new_acceleration[i], height = y)
        new_peaks_acc_29,_ = find_peaks(new_acceleration_29[i], height = y)
        new_peaks[i] = new_peaks_acc
        new_peaks_29[i] = new_peaks_acc_29
        plt.plot(new_acceleration[i])
        plt.plot(new_acceleration_29[i], linewidth = '2')
        plt.axhline(y=b, linewidth = '3', color = 'r')
        plt.suptitle('Acceleration ' + str(i), fontsize='30')
        plt.grid(True, 'both')
        plt.show()
        return print("Number of peaks in raw data: ", len(new_peaks_acc)), new_peaks[i], print("Number of peaks in fitlered data: ", len(new_peaks_acc_29)), new_peaks_29[i]
        
    def ActualLength(i,start,end):
        peaks,_ = find_peaks(acceleration[i][start-3:end+3], height=16)
        print("Number of peaks in Raw data: " + str(len(peaks)))
        peaks,_ = find_peaks(acceleration_29[i][start-3:end+3], height=16)
        print("Number of peaks in Filtered data: " + str(len(peaks)))

    Peaks(0)
    
# this won't be run when imported
if __name__ == "__main__":
    main()
    