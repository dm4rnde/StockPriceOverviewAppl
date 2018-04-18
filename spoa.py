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
    but this might not always work or give intended
    stock back.
    
    For example: 
        AMZN or TSLA or F, will give NASDAQ:AMZN, 
        NASDAQ:TSLA, NYSE:F.
    
        But, BA will not give results (you have to use
        NYSE:BA or BA:NYSE instead), TL0 will 
        give TL0:FRA (you might intended TL0:ETR).
         
    To get intended result, it is better to add 
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
        
        # let thread handle the add process
        self.start_pb_thread(event=None, target1=self.add_new_symbol)

    def add_new_symbol(self):
        
        self.entry_stock_symbol_field.configure(state=DISABLED)
        
        self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
        
        try:
            new_symbol = self.entry_stock_symbol_field.get().strip()
            if new_symbol is '' or ' ' in new_symbol:
                return
            
            # check if symbol exists at all in google finance
            try:
                # this query is made to get actual global stock quote
                # just in case user did not provide global
                temp_list = []
                new_symbol = new_symbol.upper()
                temp_list.append(new_symbol)
                df = self.mem_manager.scape_latest_data_from_internet(temp_list)

            except HTTPError as e:
                self.update_feedback_note_label_text(self.FEEDBACK_STR_QUOTE_NOT_FOUND)
                print('expected error', 'during quote confirm:', type(e), '≤≥', e, '\n')
                return
            
            except URLError as e:
                self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_INTERNET)
                print('expected error', 'during quote confirm:', type(e), '≤≥', e, '\n', format_exc())
                return
            
            except Exception as e:
                self.update_feedback_note_label_text(self.FEEDBACK_STR_NO_FEEDBACK)
                print('error', 'during quote confirm:', type(e), '≤≥', e, '\n', format_exc())
                return
            
            # duplicate check
            current_symbols = []
            for c in self.treeview_s_output_area_tree.get_children():
                current_symbols.append(str(self.treeview_s_output_area_tree.item(c)['values'][0]))
            
            if new_symbol in [cs.upper() for cs in current_symbols]:
                # duplicate found; exit
                self.update_feedback_note_label_text(self.FEEDBACK_STR_ALREADY_LISTED)
                return

            print_debug_stmt('new_symbol')
            print_debug_stmt(new_symbol)
            self.mem_manager.add_stock_symbol_to_memory(new_symbol)
            
            # clean entry field
            self.entry_stock_symbol_field.delete(0, 'end')

            self.refresh_treeview_s_output_area()
            
        except Exception as e:
            print('error', 'during adding new line to output:', type(e), '≤≥', e, '\n', format_exc())
        
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
        
    def refresh_content(self):        
        
        self.entry_stock_symbol_field.configure(state=DISABLED)
        
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
            self.entry_stock_symbol_field.configure(state=NORMAL)
            
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

        s = ttk.Style()
        s.theme_use('clam')
        # or classic
        s.configure("grey.Horizontal.TProgressbar", foreground='blue', background='grey')
        self.feedback_progress_bar = ttk.Progressbar(self.frame1, orient='horizontal',
                                        mode='indeterminate', style="grey.Horizontal.TProgressbar")
        self.feedback_progress_bar.pack(side=LEFT, padx=10, fill=X, expand=True)
        
        self.start_pb_thread()
        
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
        self.create_feedback_label_at_down()
        self.create_popup_menu()

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
    other soft issues:
        - need testing of "#TODO needs review" part 
    
    features good-to-haves for future:
        (none planned)
   
    other TODOs:
        (none planned)
"""