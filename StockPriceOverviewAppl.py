#%%
import tkinter as tk

from tkinter import ttk
from tkinter import LEFT, RIGHT, BOTH, RAISED

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from datetime import date
from datetime import datetime
from datetime import timedelta
import calendar

from googlefinance import getQuotes

from pandas import DataFrame
from pandas import read_json
from pandas import read_csv
from pandas.errors import EmptyDataError
from pandas_datareader.data import DataReader
from pandas_datareader._utils import RemoteDataError

from json import dumps

from requests.exceptions import ConnectionError
from urllib.error import URLError
from urllib.error import HTTPError

from traceback import format_exc

"""
Prerequirements: 
    - requires connection to Internet

When entering new stock, it might be easier to get correct/intended stock back if 
entering globally distinctive name, that is in format: "stock exchange":"stock symbol"
(examples: ETR:BMW; FRA:DAI).
If enter short, "stock symbol" only (examples: BMW; DAI), then might not
get back stock intended. For more, see NOTE1.

#!!# see end of file, for errors/issues unsolved, good-to-haves, or other TODOs #!!# 

"""
#Have tested application to work with:
    #FRA:DAI, ETR:DAI, BA, NYSE:LMT, F, TSLA, ETR:TL0, STO:VOLV-A, 
    #FRA:AMZ, NYSE:LMT, ETR:BMW, NYSE:TM, TYO:7203, STO:STLO
    #
    #All other possibilities, have not been tested.
#
#NOTE1:
    #Please note! Sometimes, when entering only stock symbol
    #without specifying stock exchange part, you might get
    #successfully new stock added to list (stock found back); 
    #for example, AMZN or TSLA or F, you will get NASDAQ:AMZN, 
    #NASDAQ:TSLA, NYSE:F.
    #But, when doing so, unfortunately the results of what 
    #stock (of what stock exchange) you actually get back 
    #might not be the one you intended to ask:
    #for example, when inserting BMW, you get
    #CVE:BMW (but you might have planned for ETR:BMW).
    #
    #Because of mentioned, it is better to add always globally
    #distinctive and correct name (you might have planned the ETR:BMW):
    #for example, enter ETR:BMW not BMW.

"""Contains GUI related components and their interactions.
Does not contain state storing/reading logic (this responsibility is 
delegated to another object)."""
class StockPriceOverviewAppl(tk.Frame):
    
    feedbackNoteStr = ""
    
    FEEDBACK_STR_NO_FEEDBACK = ''
    FEEDBACK_STR_ALREADY_LISTED = 'already listed'
    FEEDBACK_STR_NO_INTERNET = 'no Internet connection'
    FEEDBACK_STR_QUOTE_NOT_FOUND = 'quote not found'
    FEEDBACK_STR_NO_HISTORICAL_DATA_FOUND = 'no historical data found'
    FEEDBACK_STR_NO_STOCK_SELECTED = 'no stock selected'
    FEEDBACK_STR_FEEDBACK = 'refreshed'
    
    def __init__(self, master=None):
        
        try:
            tk.Frame.__init__(self)
            
            #state storing/reading logic
            self.memManager = SPOAMemoryManager()
            
            self.master.title('Stock prices overview')
            self.createWidgets()
            
            #this will disallow manual resize of window
            root.wm_resizable(0,0)
            
            #TODO review: this is not working
            #self.location(150,150)
           
            #root.configure(background='grey')
            
            self.pack()

            #for "react on window resize" debugging only-->
            #self.bind("<Configure>", self.onceSizeReady)
            #<--
            
        except Exception as e:
            print('error', 'during init:', e, "\n", format_exc())
    
    #for "react on window resize" debugging only-->
#     def onceSizeReady(self, event):
#         w, h = self.winfo_reqwidth(), self.winfo_reqheight()
#         print(w,h)
#         #gives current window size
    #<--
      
    def createWidgets(self):
        
        self.createMenu()
        self.createInputsAtUp()
        self.createControlsAtUp()
        self.createOutpuAreaTable()
        self.createInputLineAtDownForPlot()
        self.createFeedbackLabelAtDown()
        self.createPopupMenu()
        self.createPlotArea()
       
    def createPopupMenu(self):
        #popup menu will be usually hidden;
        #it will appear only when mouse right click
        #on output area (tree view)
        
        self.popupmenu = tk.Menu(root, tearoff=0)
        self.popupmenu.add_command(label="remove", 
                                   command=self.removeLineFromOutputAreaTable)
        self.popupmenu.add_command(label="copy", 
                                   command=self.copyStockSymbolOfSelectedLineOfOutputAreaTable)
        self.outpAreaTree.bind("<Button-2>", self.openPopupMenu)

    def openPopupMenu(self, event):
        
        #allow open popup only if anything selected
        if len(self.outpAreaTree.selection()) == 1:
            self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_FEEDBACK)
            self.popupmenu.post(event.x_root, event.y_root)
    
    def copyStockSymbolOfSelectedLineOfOutputAreaTable(self):
        
        self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_FEEDBACK)
        for i in self.outpAreaTree.selection():
            stockSymbolOfSelectedRow = self.outpAreaTree.item(i)["values"][0]
            
            providedSymbolGlobal = stockSymbolOfSelectedRow
            
            #make use of pandas dataframe function to store
            #text to clipboard
            df = DataFrame([providedSymbolGlobal])
            df.to_clipboard(index=False, header=False)
            
    def removeLineFromOutputAreaTable(self):
        
        self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_FEEDBACK)
        
        for i in self.outpAreaTree.selection():
            stockSymbolOfSelectedRowGlobalForm = self.outpAreaTree.item(i)["values"][0]
            self.memManager.removeStockSymbolFromMemory(stockSymbolOfSelectedRowGlobalForm)

        #because of change in memory must trigger update on output area table
        self.refreshOutputAreaTable()
            
    def createMenu(self):
        
        self.menubar = tk.Menu(root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_command(label="Exit", command=root.destroy)
        root.config(menu=self.menubar)

    def createInputsAtUp(self):
        
        self.frame1 = tk.Frame(self, relief=RAISED, borderwidth=1)
        self.frame1.pack(fill=BOTH, expand=True)
        
        #print(self.frame1.config("bg"))
        self.entryStockSymbolLabel = tk.Label(self.frame1,
                              text='Add stock symbol',
                              justify="left",
                              font="Verdana 13")
        self.entryStockSymbolLabel.pack(side=LEFT, padx=10, pady=10)
        
        self.entryStockSymbolField = tk.Entry(self.frame1)
        self.entryStockSymbolField.bind('<Return>', 
                                        self.addNewLineToOutputAreaTable)
        self.entryStockSymbolField.config(width=8)
        self.entryStockSymbolField.pack(side=LEFT)
        

    def createControlsAtUp(self):
        
        self.controlRefreshAllBtn = tk.Button(self.frame1,
                                  text="Refresh",
                                  command=self.refreshOutputAreaTable)
        self.controlRefreshAllBtn.pack(side=RIGHT, padx=10, pady=10)
        
    def addNewLineToOutputAreaTable(self,event):
        
        self.cleanUpPlotArea()
        self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_FEEDBACK)
        
        try:
            newSymbol = self.entryStockSymbolField.get().strip()
            if newSymbol is '':
                return
            
            #check if symbol exists at all in google finance
            newSymbolsGlobal = ""
            try:
                #this query is made to get actual global stock quote
                #just in case user did not provide global
                qryForGettingFullQuote = getQuotes(newSymbol.upper())
                jsonDmps = dumps(qryForGettingFullQuote, indent=2)
                df = read_json(jsonDmps)
                #merge two column values to get global symbol
                newSymbolsGlobal = str(df.at[0,"Index"]) + ":" + str(df.at[0,"StockSymbol"])
            except HTTPError as e:
                self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_QUOTE_NOT_FOUND)
                print("expected error","during quote confirm:", type(e), "≤≥", e)
                return
            except URLError as e:
                self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_INTERNET)
                print("expected error", "during quote confirm:", type(e), "≤≥", e)
                return
            except Exception as e:
                self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_FEEDBACK)
                print("error", "during quote confirm:", type(e), "≤≥", e, "\n", format_exc())
                return
            
            if ":" not in newSymbolsGlobal:
                return
            
            newSymbolsGlobal = newSymbolsGlobal.upper()
            
            #duplicate check
            currentSymbols = []
            for c in self.outpAreaTree.get_children():
                currentSymbols.append(self.outpAreaTree.item(c)["values"][0])
            
            if newSymbolsGlobal in [cs.upper() for cs in currentSymbols]:
                #duplicate found; exit
                self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_ALREADY_LISTED)
                return

            self.memManager.addStockSymbolToMemory(newSymbolsGlobal)
            
            #clean entry field
            self.entryStockSymbolField.delete(0, 'end')

            self.refreshOutputAreaTable()
            
        except Exception as e:
            print("error", "during adding new line to output:", type(e), "≤≥", e, "\n", format_exc())
        
    def createOutpuAreaTable(self):
        
        try:
            self.frame2 = tk.Frame(self, relief=RAISED, borderwidth=1)
            self.frame2.pack(fill=BOTH, expand=True)
            
            self.opatScroll = ttk.Scrollbar(self.frame2, orient="vertical")

            #define table (in treeview form)
            self.outpAreaTree = ttk.Treeview(self.frame2, 
                                             selectmode="browse", 
                                             yscrollcommand=self.opatScroll.set)
            #selectmode=browse -- allow select only one line at a time
            self.outpAreaTree['columns'] = ('symbol', 'date', 'price')
            
            self.opatScroll.configure(command=self.outpAreaTree.yview)
            
            self.outpAreaTree.pack(side=LEFT, fill=BOTH, expand=1)
            self.opatScroll.pack(side=RIGHT, fill="y")

            self.outpAreaTree.heading("symbol", text="Symbol")
            self.outpAreaTree.heading("date", text="Last updated")
            self.outpAreaTree.heading("price", text="Price")
            
            #get data and fill table
            self.fetchRenewPopulateOutputAreaTable()

        except URLError as e:
            self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_INTERNET)
            print("expected error", "during output area create:", type(e), "≤≥", e)
        except Exception as e:
            self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_FEEDBACK)
            print("error", "during output area create:", type(e), "≤≥", e, "\n", format_exc())
        finally:
            #we don't use first column, it is inconvenient here;
            #always remove it (in case of any error or no error) -
            #because width of the component should appear same, when 
            #starting with error or data;
            self.outpAreaTree['show'] = 'headings'
            
    def askToProducePlotForPeriodFromDaysBackUntilFirstWorkingDayBeforeToday(self, daysToDecrement):
        
        self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_FEEDBACK)
        
        #only when one line is selected in table area
        if len(self.outpAreaTree.selection()) == 1:
            
            self.today = date.today()
            #first find out last working day, before today
            #don't include today in calculation (as there is no data on that day)
            self.lastWorkingDay = self.lastWorkingDayBeforeGivenDate(self.today)
            self.lwdInString = self.lastWorkingDay.strftime("%d.%m.%Y")
            dateTempStrVar = tk.StringVar()
            dateTempStrVar.set(self.lwdInString)
            #store new date into input field "to date"
            self.entryTimeToField["textvariable"] = dateTempStrVar
            
            before = self.lastWorkingDay - timedelta(days=int(daysToDecrement))
            
            #now find out if this last day was working day
            self.lwdm1InString = before.strftime("%d.%m.%Y")
            dateTempStrVar = tk.StringVar()
            dateTempStrVar.set(self.lwdm1InString)
            #store new date into input field "from date"
            self.entryTimeFromField["textvariable"] = dateTempStrVar
            
            #ask plot area to follow
            self.drawPlot()
         
        else:
            self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_STOCK_SELECTED)
           
    def lastWorkingDayBeforeGivenDate(self, dateGiven):
        
        lastWorkingDayWas = dateGiven
        dayOfWeekInEng = calendar.day_name[dateGiven.weekday()]
        #if today is Monday ...
        if dayOfWeekInEng == 'Monday':
            #... then last working day should be minus 3 days, Friday
            lastWorkingDayWas = dateGiven - timedelta(days=3)
        elif dayOfWeekInEng == 'Sunday':
            #should be Friday
            lastWorkingDayWas = dateGiven - timedelta(days=2)
        else:
            lastWorkingDayWas = dateGiven - timedelta(days=1)
        return lastWorkingDayWas
                     
    def createInputLineAtDownForPlot(self):
        
        self.frame3 = tk.Frame(self, relief=RAISED, borderwidth=1)
        self.frame3.pack(fill=BOTH, expand=True)
        
        self.fiveDaysPlotBtn = tk.Button(self.frame3, text="5d")
        self.fiveDaysPlotBtn["command"] = lambda: self.drawPlotWhenClickOnTimeInputBtn(daysToDecrement=5)
        self.fiveDaysPlotBtn.pack(side=LEFT, padx=2, pady=2)
        
        self.twoWeeksPlotBtn = tk.Button(self.frame3, text="2w")
        self.twoWeeksPlotBtn["command"] = lambda: self.drawPlotWhenClickOnTimeInputBtn(daysToDecrement=14)
        self.twoWeeksPlotBtn.pack(side=LEFT, padx=2, pady=2)
        
        self.oneMonthPlotBtn = tk.Button(self.frame3, text="1m")
        self.oneMonthPlotBtn["command"] = lambda: self.drawPlotWhenClickOnTimeInputBtn(daysToDecrement=30)
        self.oneMonthPlotBtn.pack(side=LEFT, padx=2, pady=2)
        
        self.threeMonthsPlotBtn = tk.Button(self.frame3, text="3m")
        self.threeMonthsPlotBtn["command"] = lambda: self.drawPlotWhenClickOnTimeInputBtn(daysToDecrement=90)
        self.threeMonthsPlotBtn.pack(side=LEFT, padx=2, pady=2)
        
        self.sixMonthsPlotBtn = tk.Button(self.frame3, text="6m")
        self.sixMonthsPlotBtn["command"] = lambda: self.drawPlotWhenClickOnTimeInputBtn(daysToDecrement=150)
        self.sixMonthsPlotBtn.pack(side=LEFT, padx=2, pady=2)
        
        self.oneYearPlotBtn = tk.Button(self.frame3, text="1y")
        self.oneYearPlotBtn["command"] = lambda: self.drawPlotWhenClickOnTimeInputBtn(daysToDecrement=365)
        self.oneYearPlotBtn.pack(side=LEFT, padx=2, pady=2)
        
        self.twoYearsPlotBtn = tk.Button(self.frame3, text="2y")
        self.twoYearsPlotBtn["command"] = lambda: self.drawPlotWhenClickOnTimeInputBtn(daysToDecrement=730)
        self.twoYearsPlotBtn.pack(side=LEFT, padx=2, pady=2)
        
        self.threeYearsPlotBtn = tk.Button(self.frame3, text="3y")
        self.threeYearsPlotBtn["command"] = lambda: self.drawPlotWhenClickOnTimeInputBtn(daysToDecrement=1095)
        self.threeYearsPlotBtn.pack(side=LEFT, padx=2, pady=2)
        
        self.fiveYearsPlotBtn = tk.Button(self.frame3, text="5y")
        self.fiveYearsPlotBtn["command"] = lambda: self.drawPlotWhenClickOnTimeInputBtn(daysToDecrement=1825)
        self.fiveYearsPlotBtn.pack(side=LEFT, padx=2, pady=2)
        
        #input field "from date"
        self.entryTimeFromField = tk.Entry(self.frame3)
        self.entryTimeFromField.bind('<Return>', 
                                        self.drawPlotWhenReturnOnTimeInputEntry)
        self.entryTimeFromField.config(width=10)
        self.entryTimeFromField.pack(side=LEFT, pady=5)
        
        self.defatultStartDate = tk.StringVar()
        self.defatultStartDate.set("01.01.2017")
        #TODO needs review and testing - fixed static text entering here;
        #might this cause possible date format problem if 
        #starting app under computer with different locale?
        self.entryTimeFromField["textvariable"] = self.defatultStartDate
        
        #input field "to date"
        self.entryTimeToField = tk.Entry(self.frame3)
        self.entryTimeToField.bind('<Return>', 
                                        self.drawPlotWhenReturnOnTimeInputEntry)
        self.entryTimeToField.config(width=10)
        self.entryTimeToField.pack(side=LEFT)
        
        self.defatultEndDate = tk.StringVar()
        self.today = date.today()
        self.todayInString = self.today.strftime("%d.%m.%Y")
        self.defatultEndDate.set(self.todayInString)
        self.entryTimeToField["textvariable"] = self.defatultEndDate
        
    def createFeedbackLabelAtDown(self):
        
        self.feedbackNoteLabel = tk.Label(self.frame3, text=self.feedbackNoteStr,
                                        anchor="e", font="Verdana 11")
        self.feedbackNoteLabel.pack(expand=True, fill=BOTH)
                             
    def createPlotArea(self): 
        
        #this would hold plot, initially it has no plot (is empty)
        self.frame4 = tk.Frame(self, relief=RAISED, borderwidth=1, height=352)
        #ps! height is important here to get right - it was taken from
        #the height of the actual plot (found out by repeated plot creating)
        self.frame4.pack(fill=BOTH, expand=True)

    def drawPlotWhenClickOnTimeInputBtn(self, daysToDecrement):
        #this is convenience method (method name simplification)
        
        self.askToProducePlotForPeriodFromDaysBackUntilFirstWorkingDayBeforeToday(daysToDecrement)

    def drawPlotWhenReturnOnTimeInputEntry(self, event):
        #this is convenience method (method name to explain its source, discards the event, redirects)
                
        self.drawPlot()
    
    def drawPlotWhenSelectOnOutputListItem(self, event):
        #this is convenience method (method name to explain its source, discards the event, redirects)
        
        self.drawPlot()
        
    def drawPlot(self):
        
        try:
            #only if exactly one line is selected in output area table (tree view)
            if len(self.outpAreaTree.selection()) == 1:
               
                self.cleanUpPlotArea() 
                
                selected = self.outpAreaTree.selection()[0]
                stockSymbolGlobalSelected = self.outpAreaTree.item(selected)["values"][0]
                
                #print("generating plot for",stockSymbolGlobalSelected)
                dateStartOfFromField = self.entryTimeFromField.get().strip()
                dateEndOfToField = self.entryTimeToField.get().strip()
                #print(dateStartOfFromField)
                #print(dateEndOfToField)
      
                #convert to date objects
                atime = datetime.strptime(dateStartOfFromField, "%d.%m.%Y")
                btime = datetime.strptime(dateEndOfToField, "%d.%m.%Y")
                 
                oneStockDataOnDatesDF = DataReader(stockSymbolGlobalSelected, 'google', atime, btime)
     
                #actual plotting here
                #take only the index column and the close column
                #and make a plot
                stockCloseDataDF = oneStockDataOnDatesDF['Close']
 
                #must include import here (and not in head of file),
                #because otherwise will fail under macOS
                #with macOS system error
                import matplotlib.pyplot as plt
                
                try:
                    plt.close('all')
                    #this is to close previous/all figures opened thus far;
                    #otherwise will receive:
                    '''.../python3.6/xxx/matplotlib/pyplot.py:524: RuntimeWarning: 
                    More than 20 figures have been opened. Figures created through 
                    the pyplot interface (`matplotlib.pyplot.figure`) are retained 
                    until explicitly closed and may consume too much memory. (To 
                    control this warning, see the rcParam `figure.max_open_warning`).
                    max_open_warning, RuntimeWarning)'''
                except Exception as e:
                    pass
                fig = plt.figure(num=None, figsize=(3,3.5), dpi=100, tight_layout=True)
                #ps! tight_layout is important here, without it, text on x axis goes
                #over the bottom line partly, and is hidden, and it is not easy to get
                #it scaled (none found yet), other than using this argument
                subplot = fig.add_subplot(111)
                subplot.plot(stockCloseDataDF)
                #subplot.plot(stockCloseDataDF,marker='o')
                
                #it is also important that labels on x axis
                #will all be visible, therefore rotate them
                #(otherwise they are overlapping, and some
                #text unreadable)
                locs, labels = plt.xticks()
                plt.setp(labels, rotation=90)
                
                plt.grid(True, which='major', linestyle='--')
                
                pltCanvas = FigureCanvasTkAgg(fig, master=self.frame4)
                pltCanvas.show()
         
                self.cleanUpPlotArea()
               
                self.plotCanvasWidget = pltCanvas.get_tk_widget()
                self.plotCanvasWidget.pack(fill=BOTH)
                
                self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_FEEDBACK)
                
            else:
                self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_STOCK_SELECTED)
            
        except RemoteDataError as e:                
            print("expected error", 'skipped plotting because of:', type(e), "≤≥", e)
            self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_HISTORICAL_DATA_FOUND)

            self.cleanUpPlotArea()

        except ConnectionError as e:
            print("expected error", 'skipped plotting because of:', type(e), "≤≥", e)
            self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_INTERNET)
            
            self.cleanUpPlotArea()
                
        except Exception as e:
            print("error", 'skipped plotting because of:', type(e), "≤≥", e, "\n", format_exc())
            self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_FEEDBACK)
            
            self.cleanUpPlotArea()
        
        #always, after plotting, move focus to output area table; 
        #below, need to give it some time otherwise focus might not work
        #(not 100%, but mostly reliable)
        root.after(400, lambda: self.outpAreaTree.focus_set())
        
    def cleanUpPlotArea(self):
        """Will clean away the old plot (if it was there;
            if it wasn't then it just executes pass)"""
            
        try:
            self.plotCanvasWidget = self.plotCanvasWidget
            self.plotCanvasWidget.destroy()
            #need to replace existing, by deleting the previous first
        except Exception as e:
            #also expected - probably no plot to remove
            pass    

    def updateFeedbackNoteLabelText(self, newText):
        """Will be called to update text of feedback label"""
        
        self.feedbackNoteStr = newText + " "
        try:
            self.feedbackNoteLabel["text"] = self.feedbackNoteStr
        except AttributeError as e:
            #it is possible that it is called before component label
            #has been initiated (/created/constructed);
            #never mind, as long as the note string has been changed
            #(here, above) the component will have this text
            #in it once it is being constructed
            print("expected error", "during update of feedback label", type(e), e)
        except Exception as e:
            print("error", "during update of feedback label", type(e), e, "\n", format_exc())
        
    def deleteAllLinesInOutputAreaTable(self):
        
        for c in self.outpAreaTree.get_children():
            self.outpAreaTree.delete(c)
        
    def refreshOutputAreaTable(self):
        
        try:
            self.deleteAllLinesInOutputAreaTable()
            self.fetchRenewPopulateOutputAreaTable(initial=False)

            self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_FEEDBACK)
        except URLError as e:
            self.updateFeedbackNoteLabelText(self.FEEDBACK_STR_NO_INTERNET)
            print("expected error", "during refresh output area", type(e), e)
        except Exception as e:
            print("error", "during refresh output area", type(e), e, "\n", format_exc())
        finally:
            self.cleanUpPlotArea()
        
    def fetchRenewPopulateOutputAreaTable(self, initial=True):
        """ Renew memory (includes fetching correct data) and 
        based on that fill output area table (tree view)"""

        self.memManager.fetchFreshDataToRenewMemory(initial)
        #build output area table from data that is in the memory
        self.buildOutputAreaTableFromMemory()
    
    def buildOutputAreaTableFromMemory(self):
        """Extract needed info from memory and build output 
        area table (tree view); expect memory to be up-to-date"""

        #read memory;
        data = self.memManager.getMemoryAsDataFrame()
         
        dataCleaned = []
        #from provided dataframe, extract "stock symbol", "last updated", "price"
        for i in range(0, len(data)):
            dataCleaned.append([str(data.iloc[i,0]) + ":" + str(data.iloc[i,3]),data.iloc[i,1],data.iloc[i,2]])
 
        #build tree items, all will be top level items
        for d in dataCleaned:
            self.outpAreaTree.insert("", 0, values=[d[0],d[1],d[2]])
        
        #on tree react on select 
        #    (on key (arrow up and down) or 
        #    button (left mouse click) release 
        #    (stress on release! event should be binded not on to the 
        #    time of select/key press - otherwise get wrong info -, but 
        #    to their release) 
        #plot area should follow (plot will be recreated)
        self.outpAreaTree.bind("<ButtonRelease-1>", self.drawPlotWhenSelectOnOutputListItem)
        self.outpAreaTree.bind("<KeyRelease-Up>", self.drawPlotWhenSelectOnOutputListItem)
        self.outpAreaTree.bind("<KeyRelease-Down>", self.drawPlotWhenSelectOnOutputListItem)

"""Manages memory - storing/reading/fetching data 
over Internet to memory for StockPriceOverviewAppl"""
class SPOAMemoryManager(tk.Frame):
    #when start very first time, these are the
    #stock symbols loaded into output area;
    #just to have something listed
    initialListOfStockSymbols = ['BA', 'NYSE:LMT']
    
    #memory1;
    # will hold running list of correct stock symbols 
    # (these are global, e.g. instead of VOLV-A there 
    # would be STO:VOLV-A)
    listOfSymbolsWhereEachElementHasGlobalSymbolForm = []
    
    #memory2;
    # will hold last state;
    # it is in DataFrame format;
    # this is also what is stored in a state file
    lastStateDF = DataFrame()

    #file where state is stored;
    #allows to continue where left off (most importantly, 
    #contains stock symbols);
    #allow to hold memory longer than possible on runtime
    csvFilenameToStoreStateTo = 'StateDataForStockPriceOverviewAppl.csv'
    
    def fetchFreshDataToRenewMemory(self, initial=True):
        
        #compose stock symbols list [memory 1]
        #first decide where to take stock symbols from
        if initial:
            #    a) starting with default list of symbols 
            #       (fresh, new state / very first starting / use defaults)
            try:
                self.readStockSymbolsFromFileIntoMemory()
                #having reached here, it means successful file read
                # (file exists and is not empty)
                # it means it is not initial loading after all
                # (we will not use defaults)
                
                # b) continue, but now take list from a file 
                #    (already stored state / restore / take symbols from file) 
                
                initial = False
            except EmptyDataError as e:
                #having reached here, it means file exists but it is empty;
                # (user have intentionally cleared the list)
                # it means it is not initial loading after all
                
                # b) continue, but now take list from a file 
                #    (already stored state / restore / take symbols from file) 

                initial = False
            except FileNotFoundError as e:
                #having reached here, it means file does not exist;
                # it is initial; stay with default option a)
                pass
            except Exception as e:
                print("error", "during initial data read", type(e), e, "\n", format_exc())
                #having reached here, we encountered (unknown) exception with file
                #that we haven't anticipated
                # stay with option a)
        #else:        
        #   c) take symbols list from a memory (it is repeating visit / no need 
        #      to read file / stock symbols are already stored in runtime memory/list,
        #      which is already up-to-date);
        #       it is reoccurring visit, we have already been here before;
        #       (nothing needs to be done here)
             
        if initial:
            #if a), fill memory, with symbols from default list
            self.initiateMemoryToDefault()
        #else memory should be filled or is intentionally empty
       
        self.loadNewDataFromInternetToMemory()
        
    def initiateMemoryToDefault(self):
        self.listOfSymbolsWhereEachElementHasGlobalSymbolForm = self.initialListOfStockSymbols.copy()
        #memory 2 state is now invalid
        self.invalidateMemory2()
    
    def storeMemory2IntoFile(self):
        #as we do not need default index column, remove it also before save
        self.lastStateDF.to_csv(self.csvFilenameToStoreStateTo, index=False)
    
    def getSymbolsFromMemory2WhereResultSymbolsHaveGlobalSymbolForm(self):
        allSymbols = []
        #this is done for convenience only (making variable shorter)
        data = self.lastStateDF.copy()
        for i in range(0, len(data)):
            #get global symbol of each row
            #(merge two column values to get global symbol)
            allSymbols.append(str(data.iloc[i,0]) + ":" + str(data.iloc[i,3]))
        return allSymbols
    
    def getMemoryAsDataFrame(self):
        return self.getMemory2()
        
    def getMemory2(self):
        return self.lastStateDF.copy()
    
    def loadNewDataFromInternetToMemory(self):
        #get fresh data, in dataframe format
        dataFr = self.fetchAndPrepareDataFrameFilledWithLatestStockPrices()
        #fill memory
        self.renewEntireMemory(dataFr)
    
    def fetchLatestStockPricesForStocksGiven(self, listOfStocks):
        """Returns json list, where every json unformatted"""
        return getQuotes(listOfStocks)
    
    def fetchAndPrepareDataFrameFilledWithLatestStockPrices(self):
        
        #start with empty dataframe
        df = DataFrame()
        
        #only if there are any symbols
        if len(self.listOfSymbolsWhereEachElementHasGlobalSymbolForm) > 0:
            #query symbol's latest price info
            #(data received will be in json format)
            latestStockStateFetched = self.fetchLatestStockPricesForStocksGiven(self.listOfSymbolsWhereEachElementHasGlobalSymbolForm)
            jsonDmps = dumps(latestStockStateFetched, indent = 2)
            #ask pandas help in converting from json to dataframe
            df = read_json(jsonDmps)
            
            #prepare format
            #leave only 4 columns
            df = df.loc[:,["Index",'LastTradeDateTimeLong', 'LastTradePrice', 'StockSymbol']].copy()
        #else:
            #no symbols; then user have deleted all symbols from the list; 
            #rely on empty dataframe (empty is also a state)
        
        return df

    def readStockSymbolsFromFileIntoMemory(self):
        
        #read stock symbols from dataframe stored in file to a memory
        dftemp = read_csv(self.csvFilenameToStoreStateTo)
        self.renewEntireMemory(dftemp)
        
    def renewEntireMemory(self, newStateDataFrame):
        self.renewMemory2(newStateDataFrame)
        self.updateMemory1ByMakingItSyncWithMemory2()
        
    def renewMemory2(self, newStateDataFrame):
        self.lastStateDF = newStateDataFrame.copy()
    
    def invalidateMemory2(self):
        """Clears memory 2"""
        self.lastStateDF = DataFrame()
    
    def updateMemory1ByMakingItSyncWithMemory2(self):
        """Makes memory 1 up-to-date (follows memory 2)"""
        newSymbsList = self.getSymbolsFromMemory2WhereResultSymbolsHaveGlobalSymbolForm()
        self.updateMemory1ListOfSymbolsWhereEachElementHasGlobalSymbolForm(newSymbsList)
    
    def updateMemory1ListOfSymbolsWhereEachElementHasGlobalSymbolForm(self, newListOfSymbols):
        self.listOfSymbolsWhereEachElementHasGlobalSymbolForm = newListOfSymbols

    def addStockSymbolToMemory(self, symbolGlobalFormToAdd):
        self.addItemToMemory1(symbolGlobalFormToAdd)
        
    def addItemToMemory1(self, symbolGlobalFormToAdd):
        #prerequirements: before calling, memory 2 must be up-to-date;
        self.updateMemory1ByMakingItSyncWithMemory2()
        self.listOfSymbolsWhereEachElementHasGlobalSymbolForm.append(symbolGlobalFormToAdd)  
        #memory 2 state is now invalid
        self.invalidateMemory2()
        
        self.loadNewDataFromInternetToMemory()
        #and save new state to a file
        self.storeMemory2IntoFile()

    def removeStockSymbolFromMemory(self, symbolGlobalFormToRemove):
        self.removeItemFromMemory1(symbolGlobalFormToRemove)
        
    def removeItemFromMemory1(self, symbolGlobalFormToRemove):
        #prerequirements: before calling, memory 2 must be up-to-date;
        self.updateMemory1ByMakingItSyncWithMemory2()
        self.listOfSymbolsWhereEachElementHasGlobalSymbolForm.remove(symbolGlobalFormToRemove)
        #memory 2 state is now invalid
        self.invalidateMemory2()
        
        self.loadNewDataFromInternetToMemory()
        #and save new state to a file
        self.storeMemory2IntoFile()
    
if __name__ == '__main__':
    root = tk.Tk()

    app = StockPriceOverviewAppl(master=root)
    app.mainloop()
#%%

""" 
errors, issues, good-to-haves:

    errors unsolved:
        (none known - could be, but testing was limited here)
      
    other soft issues:
        - self.location(150,150) is not working
        - need testing of "#TODO needs review" part 
    
    features good-to-haves for future:
        (none planned)
   
    other TODOs:
        (none planned)

"""