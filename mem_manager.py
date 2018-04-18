"""
Author: Dm4Rnde (dm4rnde@pm.me)
"""


from shared_constants import *
from scraper import WebResourceFetcher 

from traceback import format_exc
from pandas import DataFrame
from pandas import read_csv
from pandas.errors import EmptyDataError


"""
Manages memory (state data):
    - storing (state stored to a csv file)
    - reading and restoring (state from a csv file)
    - fetching data (get fresh data over Internet)
"""

class SPOAMemoryManager():
    
    # Initially, when start very first time, these are the
    # symbols loaded (just to have at least something listed).
    initial_list_of_stock_symbols_global_form = ['NYSE:BA', 'NYSE:LMT']
    
    # MEMORY1:
    #    will hold running list of correct stock symbols
    #    that are in 'global form'
    #    (e.g. instead of VOLV-A there would be STO:VOLV-A; 
    #    instead of BA there would be NYSE:BA)
    list_of_symbols = []
    
    # MEMORY2:
    #    will hold last state of user data;
    #    it is in DataFrame format;
    #    every line contains stock symbol, last trade date, last trade price;
    #    this is what is stored into file, 
    #    and then it is used to restore user data on program startup
    state_dataframe = DataFrame()

    # Indicates file where state is stored in table-like form;
    # allows to continue where left off;
    # allows to hold memory on runtime.
    csv_filename_to_store_state_to = 'StateDataForStockPriceOverviewAppl.csv'
    
    webresourcefetcher = None
    
    def __init__(self):
        self.webresourcefetcher = WebResourceFetcher()

    def fetch_fresh_data_to_renew_memory(self, initial=True):
        
        print_debug_stmt('fetch_fresh_data_to_renew_memory')
        # compose stock symbols list [memory 1]
        # first decide where to take stock symbols from
        if initial:
            #    a) starting with default list of symbols 
            #       (fresh, new state / very first starting / use defaults)
            try:
                self.read_or_restore_state_from_file_to_memory()
                # having reached here, it means successful file read
                #  (file exists and is not empty)
                #  it means it is not initial loading after all
                #  (we will not use defaults)
                
                #  b) continue, but now take list from a file 
                #    (already stored state / restore / take symbols from file) 
                
                initial = False
                
            except EmptyDataError as e:
                # having reached here, it means file exists but it is empty;
                #  (user have intentionally cleared the list)
                #  it means it is not initial loading after all
                
                #  b) continue, but now take list from a file 
                #    (already stored state / restore / take symbols from file) 

                initial = False
                
            except FileNotFoundError as e:
                # having reached here, it means file does not exist;
                #  it is initial; stay with default option a)
                pass
            
            except Exception as e:
                print("error", "during initial data read", type(e), e, "\n", format_exc())
                # having reached here, we encountered (unknown) exception with file
                # that we haven't anticipated
                #  stay with option a)
        #else:        
        #   c) take symbols list from a memory (it is repeating visit / no need 
        #      to read file / stock symbols are already stored in runtime memory/list,
        #      which is already up-to-date);
        #       it is reoccurring visit, we have already been here before;
        #       (nothing needs to be done here)
             
        if initial:
            # if a), fill memory, with symbols from default list
            print_debug_stmt('initial')

            self.initiate_memory_to_default()
        # else memory should be filled or is intentionally empty
       
        print_debug_stmt('pre load_fresh_data_from_internet_to_memory')
        self.load_fresh_data_from_internet_to_memory()
        print_debug_stmt('post load_fresh_data_from_internet_to_memory')
        
    def initiate_memory_to_default(self):
        
        self.list_of_symbols = self.initial_list_of_stock_symbols_global_form.copy()
        # memory 2 state is now invalid
        self.invalidate_memory2()
    
    def store_memory2_into_file(self):
        
        # as we do not need default index column, remove it also before save
        self.state_dataframe.to_csv(self.csv_filename_to_store_state_to, index=False)
    
    def get_symbols_global_form_fr_memory2(self):
        
        print_debug_stmt('get_symbols_global_form_fr_memory2')
        list_of_symbols = []

        data = self.state_dataframe.copy()
        print_debug_stmt('data')
        print_debug_stmt(data)
        for i in range(0, len(data)):
            print_debug_stmt('i', i)
            # get global symbol of each row
            list_of_symbols.append(str(data.iloc[i, 0]))
        
        print_debug_stmt('list_of_symbols', list_of_symbols)
        return list_of_symbols
    
    def get_memory_as_dataframe(self):
        # returns dataframe
        
        print_debug_stmt('get_memory_as_dataframe')
        print_debug_stmt('self.state_dataframe')
        print_debug_stmt(self.state_dataframe)
        return self.state_dataframe.copy()
    
    def load_fresh_data_from_internet_to_memory(self):
        
        # get fresh data, in dataframe format
        print_debug_stmt('load_fresh_data_from_internet_to_memory')
        dataframe_flled_w_latest_stock_data = self.fetch_and_prepare_dataframe_flled_w_latest_stock_data()
        #fill memory
        self.renew_entire_memory(dataframe_flled_w_latest_stock_data)
  
    def scape_latest_data_from_internet(self, list_of_stock_symbols):
        """Retrieves latest trade price/date of given stock 
        symbols from specific resource from the Internet; returns 
        results in DataFrame."""
        
        return self.webresourcefetcher.scrape_latest_data_on_symbols_from_internet(list_of_stock_symbols)
    
    def fetch_and_prepare_dataframe_flled_w_latest_stock_data(self):
        
        # start with empty dataframe
        df = DataFrame()
        
        # only if there are any symbols
        print_debug_stmt('fetch_and_prepare_dataframe_flled_w_latest_stock_data')
        print_debug_stmt('self.list_of_symbols')
        print_debug_stmt(self.list_of_symbols)
        if len(self.list_of_symbols) > 0:
            # query symbol's latest price info
            latest_data = None
            try:
                latest_data = self.scape_latest_data_from_internet(self.list_of_symbols)
            except Exception as e:
                # this happens when dependency/service (i.e., google) will change
                print('CRITICAL: problem with fetching stock data; program can not start', 
                      "\n", type(e), "\n", e, "\n", format_exc())
                #raise e
                exit()
            
            # prepare format
            # leave only 4 columns
            print_debug_stmt('latest_data')
            print_debug_stmt(latest_data)
            
            print_debug_stmt(latest_data.loc[:, COL_NAMES].copy())
            df = latest_data.loc[:, COL_NAMES].copy()
        #else:
            #no symbols; then user have deleted all symbols from the list; 
            #rely on empty dataframe (empty is also a state)
        
        return df

    def read_or_restore_state_from_file_to_memory(self):
        
        # read stock symbols from dataframe stored in file to a memory
        dataframe_w_latest_stored_data = read_csv(self.csv_filename_to_store_state_to)
        self.renew_entire_memory(dataframe_w_latest_stored_data)
        
    def renew_entire_memory(self, dataframe_w_latest_stock_data):
        
        print_debug_stmt('renew_entire_memory')
        self.renew_memory2(dataframe_w_latest_stock_data)
        self.update_memory1_by_making_it_sync_w_memory2()
        print_debug_stmt('renew_entire_memory 2')
        
    def renew_memory2(self, dataframe_w_latest_stock_data):
        
        self.state_dataframe = dataframe_w_latest_stock_data.copy()
    
    def invalidate_memory2(self):
        """Clears memory 2"""
        
        self.state_dataframe = DataFrame()
    
    def update_memory1_by_making_it_sync_w_memory2(self):
        """Makes memory 1 up-to-date (follows memory 2)"""
        
        print_debug_stmt('update_memory1_by_making_it_sync_w_memory2')
        list_of_symbols_memory2 = self.get_symbols_global_form_fr_memory2()
        print_debug_stmt('list_of_symbols_memory2')
        print_debug_stmt(list_of_symbols_memory2)
        self.update_memory1_list_of_symbols(list_of_symbols_memory2)
        print_debug_stmt('update_memory1_by_making_it_sync_w_memory2 2')
    
    def update_memory1_list_of_symbols(self, list_of_gl_symbols):
        self.list_of_symbols = list_of_gl_symbols

    def add_stock_symbol_to_memory(self, symbols_global_form_to_add):
        self.add_stock_symbol_to_memory1(symbols_global_form_to_add)
        
    def add_stock_symbol_to_memory1(self, symbols_global_form_to_add):
        # Prerequisites: before calling, memory 2 must be up-to-date
        
        print_debug_stmt('add_stock_symbol_to_memory1')
        self.update_memory1_by_making_it_sync_w_memory2()
        print_debug_stmt('symbols_global_form_to_add')
        print_debug_stmt(symbols_global_form_to_add)
        self.list_of_symbols.append(symbols_global_form_to_add)  
        
        # memory 2 state is now invalid and needs to be renewed
        self.invalidate_memory2()
        
        self.load_fresh_data_from_internet_to_memory()
        # and save new state to a file
        self.store_memory2_into_file()

    def remove_stock_symbol_from_memory(self, symbol_to_remove):
        self.remove_stock_symbol_from_memory1(symbol_to_remove)
        
    def remove_stock_symbol_from_memory1(self, symbol_to_remove):
        # Prerequisites: before calling, memory 2 must be up-to-date
        
        self.update_memory1_by_making_it_sync_w_memory2()
        
        self.list_of_symbols.remove(symbol_to_remove)
        
        # memory 2 state is now invalid and needs to be renewed
        self.invalidate_memory2()
        
        self.load_fresh_data_from_internet_to_memory()
        # and save new state to a file
        self.store_memory2_into_file()
        