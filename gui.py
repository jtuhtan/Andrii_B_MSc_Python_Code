from datetime import datetime
from msilib.schema import File
from posixpath import split
from sqlite3 import DatabaseError
import tkinter as tk
from tkinter import CENTER, W, filedialog, Button, ttk
from turtle import position
from numpy import pad
import time
import math
import win32file
from USB import getUSBDrive

from pandas import DataFrame
from pyparsing import col
import AndriiMSc_Number_of_Peaks as peaks
import os
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database import connect, additionalDataTable, editAdditionalDataTable, deleteAllSelectedData, createPeaks, returnPeaks,  insertPeaks
from dataHandler import getFilteredData, readFileIntoDF, getPeaks,getGaitCycles
from baselineFinder import getBaseline
from calculations import addCols
from matplotlib.backend_bases import key_press_handler
import  numpy as np
import matplotlib.patches as mpatches
from matplotlib.patches import Patch

sensorIdFileName = "sensorname.txt" # Put the name of the sensor ID file here if it changes
colorList = ["blue", "red", "green", "brown", "black"]

class UI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Gait Analysis")
        self.geometry("1800x950")
        self.config(bg="white")
        self.df = None #the dataframe currently loaded into the window
        #Set the resizable property False
        self.resizable(False, False)

        global lastButton 
        global selectedItems
        global peaks
        
        secondFrame = None
        secondPeaks = None      


        def insertData(event):
            """ 
            User chooses which file to save data from
           
            """

            tk.messagebox.showinfo("Gait analysis",  "Choose file to save")
            global dFrame, fileDate
            file = filedialog.askopenfilename()
            df = pd.read_csv(file)
            df.columns = ['stamp','battery', 'pressure','temperature','ax','ay','az','gx','gy','gz','mx','my','mz']
            
            dFrame = df
            fileDate = dateAndTime(file)
            additionalData(0)
            self.df = df
            

        def getTables():
            """
            Method returns all table names from sqlite database, that dont have _data in their name

            :return: list of table names

            """

            tablesList = []
            tablesFiltered = []
            conn = connect("oldData.db")
            res = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            for name in res.fetchall():
                tablesList.append(name[0])
            conn.close()
            for table in tablesList:
                if "_data" not in table:
                    tablesFiltered.append(table)


            return tablesFiltered

       
       
        def getDataTables():
            """
            Method returns all table names from sqlite database, that have _data in their name

            :return: list of table names

            """

            tablesList = []
            tablesFiltered = []
            conn = connect("oldData.db")
            res = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            for name in res.fetchall():
                tablesList.append(name[0])
            conn.close()
            for table in tablesList:
                if "_data" in table:
                    tablesFiltered.append(table)


            return tablesFiltered


        def dateAndTime(file):
            date = os.path.getctime(file)
            date2 = datetime.fromtimestamp(date)
            return date2
        
        # Inserts raw and calculated data from sensor into database
        # Ideally this function would be in 'database.py', but because of an error it is here for now
        def toSQL(df: DataFrame, tableName):
            dataBox.destroy()
            fName = tableName
            conn = connect("oldData.db")
            df.to_sql(name=fName, con=conn, if_exists='replace', index=False)
            conn.close()

            refreshTree()

        def refreshTree():
            """ 
            Refreshes items in tree widget by deleting everything and loading new items from database
           
            """

            tree.delete(*tree.get_children())
            itemsList = getData()
            
            for i in range(0,len(itemsList),6):
                tree.insert('', 'end', values=(itemsList[i], itemsList[i+1], itemsList[i+2], itemsList[i+3], itemsList[i+4], itemsList[i+5]))

        def additionalData(event):
            global dataBox
            save = 0
            if (event == 0):
                save = 1
                dictionary = ["","","","","",""]
            else:
                saveID = tree.focus()
                saveDict = tree.item(saveID)
                dictionary = [] * 6
                for i in range(0,len(saveDict)):
                    dictionary.append(saveDict['values'][i])
                originalName = dictionary[0]
            
            dataBox = tk.Tk()
            dataBox.title("Additional data")
            dataBox.geometry("300x425+800+400")
            dataBox.config(bg="lightgray")

            lblTableName = tk.Label(dataBox, text="Save name:")
            lblTableName.grid(row=1,column=1,padx=25,pady=25)
            txtTableName = tk.Text(dataBox, height=1, width=20)
            txtTableName.insert(1.0,dictionary[0])
            txtTableName.grid(row=1,column=2)

            lblSensorID = tk.Label(dataBox, text="Sensor ID:")
            lblSensorID.grid(row=2,column=1)
            txtSensorID = tk.Text(dataBox, height=1, width=20)
            if (save == 1):
                sensorId = getSensorId()
            else:
                sensorId = dictionary[1]
            txtSensorID.insert(1.0,sensorId)
            txtSensorID.grid(row=2,column=2)

            lblSubjectName = tk.Label(dataBox, text="Subject name:")
            lblSubjectName.grid(row=3,column=1,padx=25,pady=25)
            txtSubjectName = tk.Text(dataBox, height=1, width=20)
            txtSubjectName.insert(1.0,dictionary[2])
            txtSubjectName.grid(row=3,column=2)

            lblSensorLoc = tk.Label(dataBox, text="Sensor location:")
            lblSensorLoc.grid(row=4,column=1)

            sensorLoc = tk.StringVar(dataBox, "")
            rdSL1 = tk.Radiobutton(dataBox, text="Ankle", variable=sensorLoc, value="Ankle", tristatevalue="x")
            rdSL1.grid(row=4,column=2)
            rdSL2 = tk.Radiobutton(dataBox, text="Foot", variable=sensorLoc, value="Foot", tristatevalue="x")
            rdSL2.grid(row=5,column=2, pady=25)
            rdSL3 = tk.Radiobutton(dataBox, text="Shank", variable=sensorLoc, value="Shank", tristatevalue="x")
            rdSL3.grid(row=6,column=2)
            sensorLoc.set(dictionary[3])

            lblSensorCon = tk.Label(dataBox, text="Sensor condition:")
            lblSensorCon.grid(row=7, column=1, pady=25)
            txtSensorCon = tk.Text(dataBox, height=1, width=20)
            txtSensorCon.grid(row=7, column=2)
            txtSensorCon.insert(1.0,dictionary[4])

            if(save == 1):
                btn_save = Button(dataBox, text="SAVE", command=lambda: 
                [   
                    additionalDataTable(txtSensorID.get("1.0", "end-1c"), txtTableName.get("1.0", "end-1c"), txtSubjectName.get("1.0", "end-1c"), sensorLoc.get(), txtSensorCon.get("1.0", "end-1c"), fileDate),
                    toSQL(dFrame, txtTableName.get("1.0", "end-1c"))
                ])
                btn_save.grid(row=8,column=2, pady=25)
            else:
                btn_edit = Button(dataBox, text="EDIT", command=lambda: 
                [
                    editAdditionalDataTable(txtSensorID.get("1.0", "end-1c"), txtTableName.get("1.0", "end-1c"), txtSubjectName.get("1.0", "end-1c"), sensorLoc.get(), txtSensorCon.get("1.0", "end-1c"), originalName),
                    refreshTree(),
                    dataBox.destroy()
                ])
                btn_delete = Button(dataBox, text="DELETE DATA", fg="red", command=lambda: 
                [
                    deleteAllSelectedData(originalName),
                    refreshTree(),
                    dataBox.destroy()
                ])
                btn_delete.grid(row=8,column=2, pady=25)
                btn_edit.grid(row=8,column=1, pady=25)

        def getLocation(table):
            """
            Method for getting saved sensor location from database
            
            :return: Integer depending on the location, 14, 13 or 16
            
            """


            conn = connect("oldData.db")
            tableName = table + "_data"
            res = conn.execute("SELECT \"Sensor location\" FROM \"{}\";".format(tableName))
            location = res.fetchone()
            conn.close()
          
            if "Ankle" in location:
                return 14
            elif "Shank" in location: 
                return 13
            else:
                return 16

        def getData():
            conn = connect("oldData.db")
            dataList = []
            tableList = getDataTables()
            for table in tableList:
                res = conn.execute("SELECT * FROM \"{}\";".format(table))
                for data in res.fetchall():
                    dataList.append(table.replace('_data', ''))
                    dataList.append(data[0])
                    dataList.append(data[1])
                    dataList.append(data[2])
                    dataList.append(data[3])
                    dataList.append(data[4])
            
        
            conn.close()
            return dataList

        def selectedSave(a):
            """ 
            Get name of selected item in tree widget and change lbl_selected text into the name
           
            """
            global selectedItems

            tree.selection_toggle(tree.focus())
            saveID = tree.selection()
            saveText = []
            itemNames = ''
            for i in saveID:
                saveText.append(tree.item(i)['values'][0])
            
            if len(saveText) > 1:
                count = 1
                for i in saveText:
                    itemNames += str(i)
                    if count < len(saveText):
                        itemNames += ' & '
                    count += 1
            else:
                itemNames = saveText
            selectedItems = saveText

            lbl_selected.config(text = itemNames)

        def findPeaks():
            """
            Method for plotting out the graph with analysed data from peaks.main function
            
            """
            global lastButton
            if self.df is None:
                print("No data loaded in") #throw some sort of dialogbox or smth
                self.df = readFileIntoDF(lbl_selected['text'])
            elif self.df.empty == True:
                print("Couldnt read selected data file (DataFrame was empty")
                return
            
            df = readFileIntoDF(lbl_selected['text'])
            axes.set_title(lbl_selected['text'])
            self.df = df
            unfiltered_acc = df.averagea
            filtered_acc = getFilteredData(df, int(lbl_filter_value['text']))

             # This adds the time parameter
            df.insert(len(df.columns), "filtered_acc", filtered_acc)
            filtered_acc = df.filtered_acc

             # Get peaks in filtered data
            peaks = getPeaks(filtered_acc,getLocation(lbl_selected['text']))
            filtered_acc = df.filtered_acc

            axes.clear()
            line, = axes.plot(filtered_acc)
            axes.plot(unfiltered_acc)
            dots, = axes.plot(filtered_acc[peaks].to_frame(),
                    ".", markersize=20, picker=False)

            axes.grid(True, 'both')
            axes.set_xlabel("time [cs]")
            axes.set_ylabel("Acceleration [ms^2]")

            figure_canvas.draw()
            lastButton = "findPeaks"


        def compareData():
            
            global dots, filtered_acc, line, peaks, lastButton, selectedItems
            axes.clear()
            df = readFileIntoDF(selectedItems[0])
            axes.set_title(lbl_selected['text'])
            self.df = df
            filtered_acc = getFilteredData(df, int(lbl_filter_value['text']))

             # This adds the time parameter
            df.insert(len(df.columns), "filtered_acc", filtered_acc)
            filtered_acc = df.filtered_acc

             # Get peaks in filtered data
            peaks = getPeaks(filtered_acc,getLocation(selectedItems[0]))
            filtered_acc = df.filtered_acc

            line, = axes.plot(filtered_acc)
            dots, = axes.plot(filtered_acc[peaks].to_frame(),
                    ".", markersize=20, picker=True)

            axes.grid(True, 'both')
            axes.set_xlabel("time [cs]")
            axes.set_ylabel("Acceleration [ms^2]")

            figure_canvas.draw()
            lastButton = "compareData"

        def generateData(i):
            global filtered_acc, selectedItems
            df = readFileIntoDF(selectedItems[i])
            self.df = df
            filtered_acc = getFilteredData(df, int(lbl_filter_value['text']))

             # This adds the time parameter
            df.insert(len(df.columns), "filtered_acc", filtered_acc)
            filtered_acc = df.filtered_acc

        
        def compareGaits():

            global filtered_acc, lastButton

            axes.clear()
            axes.set_title(lbl_selected['text'])
            
            count = 0
            
            
            for item in selectedItems:


                generateData(count)

                # # peaks = peaks[peaks != 0]  # filter all the 0s aka stuff user just removed
                peaksList = returnPeaks(item)
                
                gaitCycles = getGaitCycles(peaksList, self.df)
                
                for cycle in gaitCycles:
                    axes.plot(cycle.time,cycle.filtered_acc, colorList[count])
                


            
                axes.grid(True, 'both')
                axes.set_xlabel("time [cs]")
                axes.set_ylabel("Acceleration [ms^2]")
                figure_canvas.draw()
                count += 1

            # where some data has already been plotted to ax
            handles, labels = axes.get_legend_handles_labels()
            
            for i in range(0, count):
                

                
                legendText = mpatches.Patch(color=colorList[i], label=selectedItems[i])
                
                handles.append(legendText)

            axes.legend(handles=handles)
            figure_canvas.draw()

            lastButton = "compareGaits"



        def handlePick(event):
            
            global peaks
            global filtered_acc
            ind = event.ind
            # event index might be an array if 2 peaks are overlapping
            # for i in ind:
            #     peaks[i] = 0
            peaks = np.delete(peaks,ind)
            df = self.df

             # This adds the time parameter
            filtered_acc = df.filtered_acc

             # Get peaks in filtered data
            axes.clear()
            axes.plot(filtered_acc)
            axes.plot(filtered_acc[peaks].to_frame(),
                    ".", markersize=20, picker=True)

            axes.grid(True, 'both')
            axes.set_xlabel("time [cs]")
            axes.set_ylabel("Acceleration [ms^2]")

            
            figure_canvas.draw()

        

        def getSensorId():
            tester = getUSBDrive(sensorIdFileName)
            if (tester != None):
                sensorId = tester
            else:
                sensorId = "Unknown"
            return sensorId

        def savePeaks():
            global peaks, selectedItems
            createPeaks(selectedItems[0])
            print(peaks)
            for peak in peaks:
                insertPeaks(selectedItems[0], peak)


  
        
        btn_insertData = tk.Button(
            text="Save new data",
            bg="blue",
            fg="yellow",
            command=lambda: insertData(0)

        )



        btn_Peaks = tk.Button(
            text="Show data",
            bg="blue",
            fg="yellow",
            command=findPeaks

        )

        lbl_selection = tk.Label(
            text= "Selected:",
            bg="white",
            font=("Arial", 15)
        )

        lbl_selected = tk.Label(
            text= "None",
            bg="white",
            font=("Arial", 15),
            anchor=W
        )

        
        btn_compareData = tk.Button(
            text="Show filtered peaks",
            bg="blue",
            fg="yellow",
            command=compareData

        )

        btn_compareGait = tk.Button(
            text="CompareGait",
            bg="blue",
            fg="yellow",
            command=compareGaits

        )
        
        lbl_filter = tk.Label(
            text= "Filter value",
            bg="white",
            font=("Arial", 13)
        )

        lbl_filter_value = tk.Label(
            text= "39",
            bg="white",
            font=("Arial", 15)
        )

        btn_savePeaks = tk.Button(
            text="Save peaks",
            bg="blue",
            fg="yellow",
            command=savePeaks

        )

        def slider_changed(val):
            """ 
            Check if any button was pressed before and update lbl_filter to new slider value
           
            """

            global lastButton
            lbl_filter_value.config(text = (math.floor(slider_filter.get())))
            
            if(lastButton == "compareGaits"):
                return
            match lastButton:
                case 'findPeaks':
                    findPeaks()
                case 'compareData':
                    compareData()
                case 'compareGaits':
                    compareGaits()

        
        current_value = tk.IntVar()

        slider_filter = ttk.Scale(
            from_=0,
            to=100,
            orient='horizontal',
            command=slider_changed,
            variable=current_value
        )


        slider_filter.set(39)

        frame = tk.Frame(self)

        # create a figure
        figure = plt.Figure(figsize=(14, 10), dpi=100)


        # create axes
        axes = figure.add_subplot()


        # create FigureCanvasTkAgg object
        figure_canvas = FigureCanvasTkAgg(figure, master=frame)

        figure_canvas.draw()
        figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        figure_canvas.mpl_connect("pick_event", handlePick)
        figure_canvas.mpl_connect("key_press_event", key_press_handler)

        #tree
        tree = ttk.Treeview(self, columns=("tableName", "sensorId", "patientName", "sensor_location", "situation", "date"), selectmode="none")
        
        tree.heading('tableName', text="Saved name", anchor=W)
        tree.heading('sensorId', text="Sensor ID", anchor=W)
        tree.heading('patientName', text="Patient", anchor=W)
        tree.heading('sensor_location', text="Sensor location", anchor=W)
        tree.heading('situation', text="Situation", anchor=W)
        tree.heading('date', text="Date", anchor=W)

        tree.column('#0', minwidth=0, width=0)
        tree.column('#1', minwidth=85, width=85)
        tree.column('#2', minwidth=60, width=60)
        tree.column('#3', minwidth=130, width=130)
        tree.column('#4', minwidth=75, width=75)
        tree.column('#5', minwidth=80, width=80)
        tree.column('#6', minwidth=130, width=130)

        #tree.bind('<Motion>', 'break')
        tree.bind('<ButtonRelease-1>', selectedSave)
        tree.bind('<Double-Button-1>', additionalData)

        #Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        

        itemsList = getData()
        for i in range(0,len(itemsList),6):

            tree.insert('', 'end', values=(itemsList[i], itemsList[i+1], itemsList[i+2], itemsList[i+3], itemsList[i+4], itemsList[i+5]))

        # Placing the elements
        btn_insertData.place(x=230,y=130,width=120,height=40)
        frame.place(x=450,y=0)
        btn_Peaks.place(x=230,y=220,width=120,height=40)
        scrollbar.place(x=570,y=650, height=227)
        tree.place(x=10,y=650)
        
        lbl_selection.place(x=5,y=620)
        lbl_selected.place(x=90,y=620)
        
        btn_compareData.place(x=230,y=280,width=120,height=40)
        btn_compareGait.place(x=230,y=340,width=120,height=40)
       
        slider_filter.place(x=190,y=585,width=200,height=25)
        lbl_filter.place(x=250,y=555)
        lbl_filter_value.place(x=390,y=583)

        btn_savePeaks.place(x=230,y=440,width=120,height=40)




if __name__ == '__main__':
    GUI = UI()
    GUI.mainloop()