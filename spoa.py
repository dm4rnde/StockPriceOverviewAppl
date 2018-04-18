"""
Author: Dm4Rnde (dm4rnde@pm.me)
"""

import time
import threading
from mem_manager import SPOAMemoryManager
import tkinter as tk    
from tkinter import ttk
from tkinter import LEFT, RIGHT, BOTH, RAISED, X
from tkinter import DISABLED, NORMAL
# license note: tkinter is part of python, probably licensed under PSFL 
# (which is BSD compatible)

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# license note: matplotlib, itself, uses only BSD code; is based on PSFL
# in short: is, as is PSFL, BSD compatible
# https://matplotlib.org/2.0.2/devel/license.html#license-discussion
# https://github.com/matplotlib/matplotlib/blob/master/setup.py

from datetime import date
from datetime import datetime
from datetime import timedelta
import calendar

# license note: pandas, has BSD 3-Clause License, it is BSD-licensed library
# http://pandas.pydata.org/pandas-docs/stable/overview.html#license
# https://github.com/pandas-dev/pandas/blob/master/setup.py
from pandas import DataFrame
from pandas.errors import EmptyDataError
from pandas_datareader.data import DataReader
from pandas_datareader._utils import RemoteDataError

from requests.exceptions import ConnectionError

from urllib.error import URLError
from urllib.error import HTTPError

from traceback import format_exc

from shared_constants import *

"""
spoa - Stock Price Overview Application


Prerequisites: 
    - connection to the Internet
    (stock symbols and up-to-date data
    is queried from the Internet)

#!!# see end of file, for errors/issues unsolved, good-to-haves, or other TODOs #!!# 


NOTE1:
    Have tested application with:
        works with: 
            ETR:DAI, NYSE:LMT, F, TSLA, STO:VOLV-A, NYSE:TM, TYO:7203, KRX:005380,
            DAI:FRA, TL0:ETR, AMZ:FRA, BMW:ETR, STOHF
        have to adjust to make work: 
            FRA:DAI (try DAI:FRA instead),  
            ETR:TL0 (try TL0:ETR instead), 
            FRA:AMZ (try AMZ:FRA instead), 
            ETR:BMW (try BMW:ETR),
            BA (try NYSE:BA)

    All other possibilities, have not been tested.

NOTE2:
    When entering new stock, it might be easier to 
    get correct/intended stock back if asking 
    distinctive symbol that google knows about, as 
    underlying logic scrapes values from google search
    results (first entry).
    Globally distinctive name consist of: 
    '<Google Finance Symbol>:<stock symbol>'
    
    (but if this is not getting results, try 
    '<stock symbol>:<Google Finance Symbol>' instead)
    .
    
    Google Finance Symbol can be found from
    table here:
    http://www.wikinvest.com/wiki/List_of_Stock_Exchanges.

NOTE3:
    Please note! Sometimes, when entering only stock symbol
    without specifying stock exchange part, you might get
    successfully new stock added to list (stock found back); 
    but this might not be always work or give correct
    stock back.
    
    For example: 
        AMZN or TSLA or F, will give NASDAQ:AMZN, 
        NASDAQ:TSLA, NYSE:F.
    
        But, BA will not give results (you have to use
        NYSE:BA or BA:NYSE instead), TL0 will 
        give TL0:FRA (you might intended TL0:ETR).
         
    To get correct stock back, it is better to add 
    always globally distinctive name.
    
"""


"""
Contains GUI related components and their interactions.
Does not contain state storing/reading logic (this 
responsibility is delegated to another object).
"""
class StockPriceOverviewAppl(tk.Frame):
    
    mem_manager = None

    feedback_note_str = ''
    FEEDBACK_STR_NO_FEEDBACK = ''
    FEEDBACK_STR_ALREADY_LISTED = 'already listed'
    FEEDBACK_STR_NO_INTERNET = 'no Internet connection'
    FEEDBACK_STR_QUOTE_NOT_FOUND = 'quote not found'
    FEEDBACK_STR_NO_HISTORICAL_DATA_FOUND = 'no historical data found'
    FEEDBACK_STR_NO_STOCK_SELECTED = 'no stock selected'
    FEEDBACK_STR_FEEDBACK = 'refreshed'
    
    feedback_note_label = None
    
    # treeview's output area tree;
    # this is where table with stock symbols
    # and their data appear
    treeview_s_output_area_tree = None
     
    def open_popup_menu(self, event):
        
        print_debug_stmt('popup open')
        # allow open popup only if anything selected
        if len(self.treeview_s_output_area_tree.selection()) == 1:
            self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
            self.popupmenu.post(event.x_root, event.y_root)
    
    def is_entered_text_representing_stock_symbol_possibly_in_global_form(self, entered_text):
        # global form should contain colon in it
        
        if ':' in entered_text:
            return True 
        return False
    
    def register_buy_stock_symbol_of_selected_line_of_treeview_s_output_area(self):
        
        if len(self.treeview_s_output_area_tree.selection()) == 1:
            
            for i in self.treeview_s_output_area_tree.selection():
                stock_symbol_selected = self.treeview_s_output_area_tree.item(i)['text']
                
                df = DataFrame([stock_symbol_selected])
                df.to_clipboard(index=False, header=False)
        
    def copy_stock_symbol_of_selected_line_of_treeview_s_output_area(self):
        
        self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
        for i in self.treeview_s_output_area_tree.selection():
            # next will now work, because of "automatic" conversion to int
            # (https://stackoverflow.com/questions/42701981/selection-from-a-treeview-automatically-converts-string-numbers-to-integers?noredirect=1)
            #stock_symbol_of_selected_row = self.treeview_s_output_area_tree.item(i)['values'][0]
            # using workaround instead, text field (it is duplicated value of first column of current row)
            stock_symbol_selected = self.treeview_s_output_area_tree.item(i)['text']
            print_debug_stmt('stock_symbol_selected')
            print_debug_stmt(stock_symbol_selected)
            
            # make use of pandas dataframe function 
            # to store text to clipboard
            df = DataFrame([stock_symbol_selected])
            df.to_clipboard(index=False, header=False)
            
    def remove_line_from_treeview_s_output_area(self):
        
        # let thread handle the remove process
        self.start_pb_thread(event=None, target1=self.remove_selected_symbol)
    
    def remove_selected_symbol(self):
        
        print_debug_stmt('remove_selected_symbol')
        
        self.entry_stock_symbol_field.configure(state=DISABLED)
        
        self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
        
        for i in self.treeview_s_output_area_tree.selection():
            print_debug_stmt('self.treeview_s_output_area_tree.item(i)')
            print_debug_stmt(self.treeview_s_output_area_tree.item(i))

            # can't rely on this option, as it will "auto convert" to int, which 
            # is not what would like (000270 becomes 270);
            # https://stackoverflow.com/questions/42701981/selection-from-a-treeview-automatically-converts-string-numbers-to-integers?noredirect=1
            #stock_symbol_selected = self.treeview_s_output_area_tree.item(i)['values'][0]
            
            # using workaround instead, text field (it is duplicated value of first column of current row)
            stock_symbol_selected = self.treeview_s_output_area_tree.item(i)['text']
            print_debug_stmt('stock_symbol_selected')
            print_debug_stmt(stock_symbol_selected)
            self.mem_manager.remove_stock_symbol_from_memory(stock_symbol_selected)

        # because of change in memory must trigger update on output area table
        self.refresh_treeview_s_output_area()
            
    def add_new_line_to_treeview_s_output_area(self, event):
        
        print_debug_stmt('add_new_line_to_treeview_s_output_area')
        
#         self.progressbar_should_work = True
#         self.feedback_progress_bar.start()
        # let thread handle the add process
        self.start_pb_thread(event=None, target1=self.add_new_symbol)
        #self.pb_thread.start()

    def add_new_symbol(self):
        
        self.entry_stock_symbol_field.configure(state=DISABLED)
#         self.thread_progressbar = threading.Thread(target=self.foo)
#         self.thread_progressbar.daemon = True
#         self.thread_progressbar.start()
#         root.after(20, self.check_pb_thread)
        
        self.clean_up_plot_area()
        self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
        
        try:
            new_symbol = self.entry_stock_symbol_field.get().strip()
            if new_symbol is '' or ' ' in new_symbol:
#                 self.progressbar_should_work = False
#                 self.entry_stock_symbol_field.configure(state=NORMAL)
                return
            
            # check if symbol exists at all in google finance
#             new_symbol_global_form = ''
            try:
                # this query is made to get actual global stock quote
                # just in case user did not provide global
                temp_list = []
                new_symbol = new_symbol.upper()
                temp_list.append(new_symbol)
                df = self.mem_manager.scape_latest_data_from_internet(temp_list)

# #                 new_symbolNotGlobalPart = ''
#                 # try using original entry as much as possible
#                 # because returned from query data, edits a bit numbers
#                 # (for example if to send KRX:005380 you get back
#                 # KRS:5380, but now when sending latter, you will 
#                 # not get back result)
#                 if not self.is_entered_text_representing_stock_symbol_possibly_in_global_form(new_symbol):
#                     # probably local form
#                     # treat as in local form, not in global form; e.g. 
#                     # quote TSLA (instead of NASDAQ:TSLA)
#                     # TODO
# #                     local_stock_symbol = new_symbol.upper()
# #                     new_symbol_global_form = str(df.at[0, 'Index']).upper() + ':' + new_symbolNotGlobalPart.upper()
#                     new_symbol_global_form = new_symbol
# 
#                 else:
#                     # being global already 
#                     new_symbol_global_form = new_symbol.upper()
                    
            except HTTPError as e:
                self.update_feedback_note_label_text(self.FEEDBACK_STR_QUOTE_NOT_FOUND)
                print('expected error', 'during quote confirm:', type(e), '≤≥', e, '\n')
#                 self.progressbar_should_work = False
#                 self.entry_stock_symbol_field.configure(state=NORMAL)
                return
            
            except URLError as e:
                self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_INTERNET)
                print('expected error', 'during quote confirm:', type(e), '≤≥', e, '\n', format_exc())
#                 self.progressbar_should_work = False
#                 self.entry_stock_symbol_field.configure(state=NORMAL)
                return
            
            except Exception as e:
                self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
                print('error', 'during quote confirm:', type(e), '≤≥', e, '\n', format_exc())
#                 self.progressbar_should_work = False
#                 self.entry_stock_symbol_field.configure(state=NORMAL)
                return
            
#             if not self.is_entered_text_representing_stock_symbol_possibly_in_global_form(new_symbol):
#                 # if still not global form, then can not work
#                 # w that input string; call input not usable
#                 return
            
            # duplicate check
            current_symbols = []
            for c in self.treeview_s_output_area_tree.get_children():
                current_symbols.append(str(self.treeview_s_output_area_tree.item(c)['values'][0]))
            
            if new_symbol in [cs.upper() for cs in current_symbols]:
                # duplicate found; exit
                self.update_feedback_note_label_text(self.FEEDBACK_STR_ALREADY_LISTED)
#                 self.progressbar_should_work = False
#                 self.entry_stock_symbol_field.configure(state=NORMAL)
                return

            print_debug_stmt('new_symbol')
            print_debug_stmt(new_symbol)
            self.mem_manager.add_stock_symbol_to_memory(new_symbol)
            
            # clean entry field
            self.entry_stock_symbol_field.delete(0, 'end')

            self.refresh_treeview_s_output_area()
            
        except Exception as e:
            print('error', 'during adding new line to output:', type(e), '≤≥', e, '\n', format_exc())
        
#         self.progressbar_should_work = False
#         self.entry_stock_symbol_field.configure(state=NORMAL)
        
    def ask_to_produce_plot_for_period_from_days_back_until_first_working_day_before_today(self, days_to_decrement):
        
        self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
        
        # only when one line is selected in table area
        if len(self.treeview_s_output_area_tree.selection()) == 1:
            
            self.today = date.today()
            # first find out last working day, before today
            # don't include today in calculation (as there is no data on that day)
            self.last_working_day = self.last_working_day_before_given_date(self.today)
            self.lwd_in_string = self.last_working_day.strftime('%d.%m.%Y')
            date_temp_str_var = tk.StringVar()
            date_temp_str_var.set(self.lwd_in_string)
            # store new date into input field 'to date'
            self.entry_time_to_field['textvariable'] = date_temp_str_var
            
            before = self.last_working_day - timedelta(days=int(days_to_decrement))
            
            # now find out if this last day was working day
            self.lwdm1_in_string = before.strftime('%d.%m.%Y')
            date_temp_str_var = tk.StringVar()
            date_temp_str_var.set(self.lwdm1_in_string)
            # store new date into input field 'from date'
            self.entry_time_from_field['textvariable'] = date_temp_str_var
            
            # ask plot area to follow
            self.draw_plot()
         
        else:
            self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_STOCK_SELECTED)
           
    def last_working_day_before_given_date(self, date_given):
        
        last_working_day_was = date_given
        day_of_week_in_eng = calendar.day_name[date_given.weekday()]
        # if today is Monday ...
        if day_of_week_in_eng == 'Monday':
            # ... then last working day should be minus 3 days, Friday
            last_working_day_was = date_given - timedelta(days=3)
        elif day_of_week_in_eng == 'Sunday':
            # should be Friday
            last_working_day_was = date_given - timedelta(days=2)
        else:
            last_working_day_was = date_given - timedelta(days=1)
        return last_working_day_was
                                                  
    def draw_plot_when_click_on_time_input_btn(self, days_to_decrement):
        # this is convenience method (method name simplification)
        
        self.ask_to_produce_plot_for_period_from_days_back_until_first_working_day_before_today(days_to_decrement)

    def draw_plot_when_return_on_time_input_entry(self, event):
        # this is convenience method (method name to explain its source, discards the event, redirects)
         
        # TODO; disabled because google finance change       
        #self.draw_plot()
        pass
    
    def draw_plot_when_select_on_output_list_item(self, event):
        # this is convenience method (method name to explain its source, discards the event, redirects)
        
        # TODO; disabled because google finance change       
        #self.draw_plot()
        pass
        
    def draw_plot(self):
        
        try:
            # only if exactly one line is selected in output area table (tree view)
            if len(self.treeview_s_output_area_tree.selection()) == 1:
               
                self.clean_up_plot_area() 
                
                selected = self.treeview_s_output_area_tree.selection()[0]
                stock_symbol_global_selected = self.treeview_s_output_area_tree.item(selected)['values'][0]
                
                date_start_of_from_field = self.entry_time_from_field.get().strip()
                date_end_of_to_field = self.entry_time_to_field.get().strip()
      
                # convert to date objects
                atime = datetime.strptime(date_start_of_from_field, '%d.%m.%Y')
                btime = datetime.strptime(date_end_of_to_field, '%d.%m.%Y')
                 
                one_stock_data_on_dates_DF = DataReader(stock_symbol_global_selected, 'google', atime, btime)
                # TODO
                
                # actual plotting here
                # take only the index column and the close column
                # and make a plot
                stock_close_data_DF = one_stock_data_on_dates_DF['Close']
 
                # must include import here (and not in head of file),
                # because otherwise will fail under macOS
                # with macOS system error
                import matplotlib.pyplot as plt
                
                try:
                    plt.close('all')
                    # this is to close previous/all figures opened thus far;
                    # otherwise will receive:
                    '''.../python3.6/xxx/matplotlib/pyplot.py:524: RuntimeWarning: 
                    More than 20 figures have been opened. Figures created through 
                    the pyplot interface (`matplotlib.pyplot.figure`) are retained 
                    until explicitly closed and may consume too much memory. (To 
                    control this warning, see the rcParam `figure.max_open_warning`).
                    max_open_warning, RuntimeWarning)'''
                
                except Exception as e:
                    pass
                
                fig = plt.figure(num=None, figsize=(3, 3.5), dpi=100, tight_layout=True)
                # ps! tight_layout is important here, without it, text on x axis goes
                # over the bottom line partly, and is hidden, and it is not easy to get
                # it scaled (none found yet), other than using this argument
                subplot = fig.add_subplot(111)
                subplot.plot(stock_close_data_DF)
                #subplot.plot(stock_close_data_DF,marker='o')
                
                # it is also important that labels on x axis
                # will all be visible, therefore rotate them
                # (otherwise they are overlapping, and some
                # text unreadable)
                locs, labels = plt.xticks()
                plt.setp(labels, rotation=90)
                
                plt.grid(True, which='major', linestyle='--')
                
                plt_canvas = FigureCanvasTkAgg(fig, master=self.frame4)
                plt_canvas.show()
         
                self.clean_up_plot_area()
               
                self.plot_canvas_widget = plt_canvas.get_tk_widget()
                self.plot_canvas_widget.pack(fill=BOTH)
                
                self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
                
            else:
                self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_STOCK_SELECTED)
            
        except RemoteDataError as e:                
            print('expected error', 'skipped plotting because of:', type(e), '≤≥', e, '\n', format_exc())
            self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_HISTORICAL_DATA_FOUND)

            self.clean_up_plot_area()

        except ConnectionError as e:
            print('expected error', 'skipped plotting because of:', type(e), '≤≥', e, '\n', format_exc())
            self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_INTERNET)
            
            self.clean_up_plot_area()
                
        except Exception as e:
            print('error', 'skipped plotting because of:', type(e), '≤≥', e, '\n', format_exc())
            self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
            
            self.clean_up_plot_area()
        
        # always, after plotting, move focus to output area table; 
        # below, need to give it some time otherwise focus might not work
        # (not 100%, but mostly reliable)
        root.after(400, lambda: self.treeview_s_output_area_tree.focus_set())
        
    def clean_up_plot_area(self):
        """Will clean away the old plot (if it was there;
        if it wasn't then it just executes pass)"""
            
        try:
            self.plot_canvas_widget = self.plot_canvas_widget
            self.plot_canvas_widget.destroy()
            # need to replace existing, by deleting the previous first
        
        except Exception as e:
            # also expected - probably no plot to remove
            pass    

    def update_feedback_note_label_text(self, newText):
        """Will be called to update text of feedback label"""
        
        self.feedback_note_str = newText + ' '
        try:
            self.feedback_note_label['text'] = self.feedback_note_str
            
        except AttributeError as e:
            # it is possible that it is called before component label
            # has been initiated (/created/constructed);
            # never mind, as long as the note string has been changed
            # (here, above) the component will have this text
            # in it once it is being constructed
            print('expected error', 'during update of feedback label', type(e), e, '\n', format_exc())
            
        except Exception as e:
            print('error', 'during update of feedback label', type(e), e, '\n', format_exc())
        
    def delete_all_lines_in_treeview_s_output_area_table(self):
        
        for c in self.treeview_s_output_area_tree.get_children():
            self.treeview_s_output_area_tree.delete(c)
        
    def refresh_treeview_s_output_area(self):
        
        self.start_pb_thread(event=None, target1=self.refresh_content)
        #self.pb_thread.start()
        
    def refresh_content(self):        
        
        self.entry_stock_symbol_field.configure(state=DISABLED)
        
#         self.feedback_progress_bar.start(10)
        try:
            self.delete_all_lines_in_treeview_s_output_area_table()
            self.fetch_and_renew_treeview_s_output_area(initial=False)

            self.update_feedback_note_label_text(self.FEEDBACK_STR_FEEDBACK)
            
        except URLError as e:
            self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_INTERNET)
            print('expected error', 'during refresh output area', type(e), e, '\n', format_exc())
            
        except Exception as e:
            print('error', 'during refresh output area', type(e), e, '\n', format_exc())
            
        finally:
            self.clean_up_plot_area()
            self.entry_stock_symbol_field.configure(state=NORMAL)
#             self.feedback_progress_bar.stop()
            
    def fetch_and_renew_treeview_s_output_area(self, initial=True):
        """ Renew memory (includes fetching correct data) and 
        based on that fill output area table (tree view) """

        print_debug_stmt('fetch_and_renew_treeview_s_output_area')
        self.mem_manager.fetch_fresh_data_to_renew_memory(initial)
        
        # build treeview's output area table from 
        # data that is in the memory
        self.build_treeview_s_output_area_table_from_memory()
        print_debug_stmt('fetch_and_renew_treeview_s_output_area 2')
    
    def build_treeview_s_output_area_table_from_memory(self):
        """Extract needed info from memory and build output 
        area table (in treeview); expect memory to be up-to-date."""

        print_debug_stmt('build_treeview_s_output_area_table_from_memory')
        # read memory
        user_state_data = self.mem_manager.get_memory_as_dataframe()
        print_debug_stmt('user_state_data')
        print_debug_stmt(user_state_data)
        
        data_cleaned = [] 
        # from provided dataframe, extract 'stock symbol', 'last updated', 'price'

        for i in range(0, len(user_state_data)):
#             stock_symbol_global_form = str(user_state_data.iloc[i, 1]) + ":" + str(user_state_data.iloc[i, 0])

            # semantic match #1 FOLLOW-UP (begin)
            stock_symbol = str(user_state_data.iloc[i, 0])
            company_name = str(user_state_data.iloc[i, 1])
            source = str(user_state_data.iloc[i, 2])
            last_trade_time = str(user_state_data.iloc[i, 3])
            last_trade_price = str(user_state_data.iloc[i, 4])
            
            print_debug_stmt('data_cleaned')
            print_debug_stmt(data_cleaned)
            print_debug_stmt('stock_symbol')
            print_debug_stmt(stock_symbol)
            print_debug_stmt('type(stock_symbol)')
            print_debug_stmt(type(stock_symbol))
            
            data_cleaned.append([stock_symbol, company_name, source, last_trade_time, last_trade_price])
            # semantic match #1 FOLLOW-UP (end)
            
            #data_cleaned.append([str(data.iloc[i, 0]), data.iloc[i, 1], data.iloc[i, 2]])
        
        print_debug_stmt('build_treeview_s_output_area_table_from_memory for')
 
        # build tree items, all will be top level items;
        # given: list of lists
        for data_list in data_cleaned:
                
            # semantic match #1 FOLLOW-UP (begin)
            #self.treeview_s_output_area_tree.insert('', 0, values=['\''+d[0]+'\'', d[1], d[2], d[3], d[4]])
            # '' -- don't change it
            # 0 -- last goes to top (opposite -- 'end')
            # text -- to be as id
            # ps! when reading back values, they might get converted into 
            # int incidentally, which is will skew intended type; therefore as a workaround
            # using text value as holder for data_list[0], as its type will remain;
            # https://stackoverflow.com/questions/42701981/selection-from-a-treeview-automatically-converts-string-numbers-to-integers?noredirect=1
            self.treeview_s_output_area_tree.insert('', 0, text=str(data_list[0]), values=data_list)
            # semantic match #1 FOLLOW-UP (end)
        
        # on tree react on select 
        #    (on key (arrow up and down) or 
        #    button (left mouse click) release 
        #    (stress on release! event should be binded not on to the 
        #    time of select/key press - otherwise get wrong info -, but 
        #    to their release) 
        # plot area should follow (plot will be recreated)
        self.treeview_s_output_area_tree.bind('<ButtonRelease-1>', self.draw_plot_when_select_on_output_list_item)
        self.treeview_s_output_area_tree.bind('<KeyRelease-Up>', self.draw_plot_when_select_on_output_list_item)
        self.treeview_s_output_area_tree.bind('<KeyRelease-Down>', self.draw_plot_when_select_on_output_list_item)

    def create_plot_area(self): 
        
        # this would hold plot, initially it has no plot (is empty)
        self.frame4 = tk.Frame(self, relief=RAISED, borderwidth=1, height=352)
        # ps! height is important here to get right - it was taken from
        # the height of the actual plot (found out by repeated plot creating)
        self.frame4.pack(fill=BOTH, expand=True)

    def create_popup_menu(self):
        # popup menu will be usually hidden;
        # it will appear only when mouse right click
        # on output area (tree view)
        
        self.popupmenu = tk.Menu(root, tearoff=0)
        self.popupmenu.add_command(label='remove', 
                                   command=self.remove_line_from_treeview_s_output_area)
        self.popupmenu.add_command(label='copy symbol', 
                                   command=self.copy_stock_symbol_of_selected_line_of_treeview_s_output_area)
#         self.popupmenu.add_command(label='register buy', 
#                                    command=self.register_buy_stock_symbol_of_selected_line_of_treeview_s_output_area)
        self.treeview_s_output_area_tree.bind('<Button-3>', self.open_popup_menu)

    def create_feedback_label_at_down(self):
        
        self.frame3 = tk.Frame(self, relief=RAISED, borderwidth=1)
        self.frame3.pack(fill=BOTH, expand=True)
        
        self.feedback_note_label = tk.Label(self.frame3, text=self.feedback_note_str,
                                        anchor='e', font='Verdana 11')
        self.feedback_note_label.pack(expand=True, fill=BOTH)

#plot area to be removed
#     def create_input_line_at_down_for_plot(self):
#         
#         self.frame3 = tk.Frame(self, relief=RAISED, borderwidth=1)
#         self.frame3.pack(fill=BOTH, expand=True)
#         
#         self.five_days_plot_btn = tk.Button(self.frame3, text='5d', state=DISABLED)
#         self.five_days_plot_btn['command'] = lambda: self.draw_plot_when_click_on_time_input_btn(days_to_decrement=5)
#         self.five_days_plot_btn.pack(side=LEFT, padx=2, pady=2)
#         
#         self.two_weeks_plot_btn = tk.Button(self.frame3, text='2w', state=DISABLED)
#         self.two_weeks_plot_btn['command'] = lambda: self.draw_plot_when_click_on_time_input_btn(days_to_decrement=14)
#         self.two_weeks_plot_btn.pack(side=LEFT, padx=2, pady=2)
#         
#         self.one_month_plot_btn = tk.Button(self.frame3, text='1m', state=DISABLED)
#         self.one_month_plot_btn['command'] = lambda: self.draw_plot_when_click_on_time_input_btn(days_to_decrement=30)
#         self.one_month_plot_btn.pack(side=LEFT, padx=2, pady=2)
#         
#         self.three_months_plot_btn = tk.Button(self.frame3, text='3m', state=DISABLED)
#         self.three_months_plot_btn['command'] = lambda: self.draw_plot_when_click_on_time_input_btn(days_to_decrement=90)
#         self.three_months_plot_btn.pack(side=LEFT, padx=2, pady=2)
#         
#         self.six_months_plot_btn = tk.Button(self.frame3, text='6m', state=DISABLED)
#         self.six_months_plot_btn['command'] = lambda: self.draw_plot_when_click_on_time_input_btn(days_to_decrement=150)
#         self.six_months_plot_btn.pack(side=LEFT, padx=2, pady=2)
#         
#         self.one_year_plot_btn = tk.Button(self.frame3, text='1y', state=DISABLED)
#         self.one_year_plot_btn['command'] = lambda: self.draw_plot_when_click_on_time_input_btn(days_to_decrement=365)
#         self.one_year_plot_btn.pack(side=LEFT, padx=2, pady=2)
#         
#         self.two_years_plot_btn = tk.Button(self.frame3, text='2y', state=DISABLED)
#         self.two_years_plot_btn['command'] = lambda: self.draw_plot_when_click_on_time_input_btn(days_to_decrement=730)
#         self.two_years_plot_btn.pack(side=LEFT, padx=2, pady=2)
#         
#         self.three_years_plot_btn = tk.Button(self.frame3, text='3y', state=DISABLED)
#         self.three_years_plot_btn['command'] = lambda: self.draw_plot_when_click_on_time_input_btn(days_to_decrement=1095)
#         self.three_years_plot_btn.pack(side=LEFT, padx=2, pady=2)
#         
#         self.five_years_plot_btn = tk.Button(self.frame3, text='5y', state=DISABLED)
#         self.five_years_plot_btn['command'] = lambda: self.draw_plot_when_click_on_time_input_btn(days_to_decrement=1825)
#         self.five_years_plot_btn.pack(side=LEFT, padx=2, pady=2)
#         
#         # input field 'from date'
#         self.entry_time_from_field = tk.Entry(self.frame3, state=DISABLED)
#         self.entry_time_from_field.bind('<Return>', 
#                                         self.draw_plot_when_return_on_time_input_entry)
#         self.entry_time_from_field.config(width=10)
#         self.entry_time_from_field.pack(side=LEFT, pady=5)
#         
#         self.defatult_start_date = tk.StringVar()
#         self.defatult_start_date.set('01.01.2017')
#         # TODO needs review and testing - fixed static text entering here;
#         # might this cause possible date format problem if 
#         # starting app under computer with different locale?
#         self.entry_time_from_field['textvariable'] = self.defatult_start_date
#         
#         # input field 'to date'
#         self.entry_time_to_field = tk.Entry(self.frame3, state=DISABLED)
#         self.entry_time_to_field.bind('<Return>', 
#                                         self.draw_plot_when_return_on_time_input_entry)
#         self.entry_time_to_field.config(width=10)
#         self.entry_time_to_field.pack(side=LEFT)
#         
#         self.defatult_end_date = tk.StringVar()
#         self.today = date.today()
#         self.today_in_string = self.today.strftime('%d.%m.%Y')
#         self.defatult_end_date.set(self.today_in_string)
#         self.entry_time_to_field['textvariable'] = self.defatult_end_date
        
    def create_treeview_s_output_area(self):
        
        try:
            self.frame2 = tk.Frame(self, relief=RAISED, borderwidth=1)
            self.frame2.pack(fill=BOTH, expand=True)
            
            self.opat_scroll = ttk.Scrollbar(self.frame2, orient='vertical')

            # define table (in treeview form)
            self.treeview_s_output_area_tree = ttk.Treeview(self.frame2, 
                                             selectmode='browse', 
                                             yscrollcommand=self.opat_scroll.set)
            # selectmode=browse -- allow select only one line at a time
            self.treeview_s_output_area_tree['columns'] = COL_NAMES
            
            self.opat_scroll.configure(command=self.treeview_s_output_area_tree.yview)
            
            self.treeview_s_output_area_tree.pack(side=LEFT, fill=BOTH, expand=1)
            self.opat_scroll.pack(side=RIGHT, fill='y')

            for col_head in COL_NAMES:
                self.treeview_s_output_area_tree.heading(col_head, text=col_head)
#             self.treeview_s_output_area_tree.heading('symbol', text='Symbol')
#             self.treeview_s_output_area_tree.heading('date', text='Last updated')
#             self.treeview_s_output_area_tree.heading('price', text='Price')
            
            # get data and fill table
            self.fetch_and_renew_treeview_s_output_area()

        except URLError as e:
            self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_INTERNET)
            print('error', 'during output area create:', type(e), '≤≥', e, '\n', format_exc())
            
        except Exception as e:
            self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
            print('error', 'during output area create:', type(e), '≤≥', e, '\n', format_exc())
            
        finally:
            # we don't use first column, it is inconvenient here;
            # always remove it (in case of any error or no error) -
            # because width of the component should appear same, when 
            # starting with error or data;
            self.treeview_s_output_area_tree['show'] = 'headings'

    feedback_progress_bar = None
    
    def create_feedback_at_up(self):

#         s = ttk.Style()
#         s.theme_use('classic')
        s = ttk.Style()
        s.theme_use('clam')
        s.configure("grey.Horizontal.TProgressbar", foreground='blue', background='grey')
# #         s.configure("blue.Horizontal.TProgressbar", foreground='blue', background='blue')
        self.feedback_progress_bar = ttk.Progressbar(self.frame1, orient='horizontal',
                                        mode='indeterminate', style="grey.Horizontal.TProgressbar")
#                                         length=100, mode='indeterminate')
#         self.feedback_progress_bar.pack(fill=BOTH, padx=10, pady=10)
        #self.feedback_progress_bar.pack()
        #self.feedback_progress_bar.config(width=8)
        self.feedback_progress_bar.pack(side=LEFT, padx=10, fill=X, expand=True)
#         self.feedback_progress_bar.update_idletasks()
#         self.feedback_progress_bar.start()
        
        self.start_pb_thread()
        
        #foo_thread.start()
        #root.after(20, check_pb_thread)
#         self.feedback_progress_bar.stop()
#         self.feedback_progress_bar.start(10)

    pb_thread = None
     
    def check_pb_thread(self):
        
        print_debug_stmt('check_pb_thread')
        if self.pb_thread.is_alive():
            root.after(3, self.check_pb_thread)
        else:
            self.feedback_progress_bar.stop()
            self.entry_stock_symbol_field.configure(state=NORMAL)
        print_debug_stmt('check_pb_thread')

    def start_pb_thread(self, event=None, target1=None):
        
        self.pb_thread = threading.Thread(target=target1)
        self.pb_thread.daemon = True
        self.feedback_progress_bar.start()
        self.pb_thread.start()
        root.after(3, self.check_pb_thread)
            
    def create_controls_at_up(self):
        
        self.control_refresh_all_btn = tk.Button(self.frame1,
                                  text='Refresh',
                                  command=self.refresh_treeview_s_output_area)
        self.control_refresh_all_btn.pack(side=RIGHT, padx=10, pady=10)

    def create_inputs_at_up(self):
        
        self.frame1 = tk.Frame(self, relief=RAISED, borderwidth=1)
        self.frame1.pack(fill=BOTH, expand=True)
        
        self.entry_stock_symbol_label = tk.Label(self.frame1,
                              text='Add stock symbol',
                              justify='left',
                              font='Verdana 13')
        self.entry_stock_symbol_label.pack(side=LEFT, padx=10, pady=10)
        
        self.entry_stock_symbol_field = tk.Entry(self.frame1)
        self.entry_stock_symbol_field.bind('<Return>', 
                                        self.add_new_line_to_treeview_s_output_area)
        self.entry_stock_symbol_field.config(width=15)
        self.entry_stock_symbol_field.pack(side=LEFT)

    def create_menu(self):
        
        self.menubar = tk.Menu(root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='File', menu=self.filemenu)
        self.filemenu.add_command(label='Exit', command=root.destroy)
        root.config(menu=self.menubar)

    def create_widgets(self):
        
        self.create_menu()
        self.create_inputs_at_up()
        self.create_feedback_at_up()
        self.create_controls_at_up()
        self.create_treeview_s_output_area()
        #self.create_input_line_at_down_for_plot()
        self.create_feedback_label_at_down()
        self.create_popup_menu()
        #self.create_plot_area()

    def __init__(self, master=None):
        
        try:
            tk.Frame.__init__(self)
            
            # state storing/reading logic
            self.mem_manager = SPOAMemoryManager()
            
            self.master.title('Stock prices overview')
            
            self.create_widgets()
            
            # this will disallow manual resize of window
            root.wm_resizable(0, 0)
            
            # TODO review: this is not working
            #self.location(150,150)
           
            #root.configure(background='grey')
            
            self.pack()

            # for 'react on window resize' debugging only-->
            #self.bind('<Configure>', self.onceSizeReady)
            # <--
            
        except Exception as e:
            print('error', 'during init:', e, '\n', format_exc())
    
    #for 'react on window resize' debugging only-->
#     def onceSizeReady(self, event):
#         w, h = self.winfo_reqwidth(), self.winfo_reqheight()
#         print(w,h)
#         #gives current window size
    #<--
      
if __name__ == '__main__':
    root = tk.Tk()

    app = StockPriceOverviewAppl(master=root)
    app.mainloop()

""" 
Current commit solved:
    * google finance exists no more -- adapting; changed

errors, issues, good-to-haves:

    errors:
        chart side (historical data side) does not work anymore
        - because of dependency, google finance side, has ceased
        (https://github.com/pydata/pandas-datareader/issues/395)
        14 Nov 2017 following did not work:
            sudo pip3.6 install pandas_datareader --upgrade
            (https://stackoverflow.com/a/46356247)
            (because edit made to change that includes related url finance.google.com change,
            does not build, https://github.com/pydata/pandas-datareader/issues/391)
    
    other soft issues:
        - need testing of "#TODO needs review" part 
    
    features good-to-haves for future:
        (none planned)
   
    other TODOs:
        (none planned)
"""