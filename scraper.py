"""
Author: Dm4Rnde (dm4rnde@pm.me)
"""

from pandas import DataFrame
from pandas import concat as concatdfs
from datetime import datetime
from datetime import date
from requests import get as requestsget
from lxml.html import fromstring

from shared_constants import *

class ScrapeFailedException(Exception):
    pass

class WebResourceFetcher():
    
    def scrape_latest_data_on_symbols_from_internet(self, list_of_stock_symbols):
        return self.get_quotes_when_having_list_of_globally_unique_stock_symbols(list_of_stock_symbols)
        
    def get_quotes_when_having_list_of_globally_unique_stock_symbols(self, symbols):
        """ 
        Having list of symbols
        (example: 
          ['NASDAQ:TSLA', 'TL0', 'AMZN', 
          'NYSE:F', 'STO:VOLV-A', 'ETR:BMW', 'NYSE:LMT', 
          'FRA:AMZ', 'NASDAQ:AAPL', 'ETR:VOW', 
          'KRX:005380', 'KRX:000270']
        ) 
        then goes to Internet to fetch up-to-date data
        on those stocks.
        PS! At the moment the symbol can be any string without space. If nothing
        found on that string, then will not return data on that string.
        
        Returns dataframe.
        """
         
        workdf = DataFrame(columns=COL_NAMES)
        
        # represents current time; as google finance should be real time
        date_and_time_now = datetime.now().strftime("%Y-%d-%m %H:%M")
        
        #https://finance.yahoo.com/quote/TSLA?p=TSLA
        #template = 'https://search.yahoo.com/search?p=TSLA%20NASDAQ&fr=uh3_finance_vert&fr2=p%3Afinvsrp%2Cm%3Asb'
        
        
        print_debug_stmt('symbols:', symbols)
        
        #exit(1)
        
        for symbol in symbols:
            # first option, try get data from Google
            source1_failed = False
            try:
                df_consit_of_one_line_w_data_on_symbol = self.scrape_data_from_google_source(symbol)
                tempdfstomerge = [workdf, df_consit_of_one_line_w_data_on_symbol]
                workdf = concatdfs(tempdfstomerge)
            except ScrapeFailedException:
                source1_failed = True
            
            # but 
            # 1.) google might block access w captcha greeting
            # 2.) there is no such finance symbol found in google
            # 3.) other error during scraping/querying
            
            # second option, if first fails, try get data from Yahoo
            source2_failed = False
            if source1_failed:
                try:
                    #TODO
                    #...
                    #
                    pass
                except ScrapeFailedException:
                    source2_failed = True                
            
        # reset index numbering
        workdf = workdf.reset_index(drop=True)
    
        print_debug_stmt('workdf')
        print_debug_stmt(workdf)
              
        return workdf

    def scrape_data_from_google_source(self, symbol):
        
        print_debug_stmt('scrape_data_from_google_source')
        source_name = 'google'
        #https://www.google.com/search?q=NASDAQ%3ATSLA&btnG=Search&hl=en-SE&gbv=1

        try:
            print_debug_stmt('symbol')
            print_debug_stmt(symbol)
            
            if len(symbol.split(':')) == 2:
                # expect to have receied something like:
                # ETR:TL0
                template = 'https://www.google.com/search?q={}%3A{}&btnG=Search&hl=en-SE&gbv=1'
                ticker_elements = symbol.split(':')
                
                stock_exchange_symbol = ticker_elements[0]
                local_stock_symbol = ticker_elements[1]
                
                correct_url = template.format(local_stock_symbol, stock_exchange_symbol)
                print_debug_stmt('correct_url', correct_url)
                return self.scrape_fr_google(symbol, correct_url)
               
            elif len(symbol.split(':')) < 2:
                #https://www.google.com/search?q=amzn&btnG=Search&hl=en-SE&gbv=1
                template = 'https://www.google.com/search?q={}&btnG=Search&hl=en-SE&gbv=1'
                correct_url = template.format(symbol)
                return self.scrape_fr_google(symbol, correct_url)
            
            else:
                raise ScrapeFailedException()
                
        except Exception:
            print_debug_stmt('scraping failed from given source:', source_name)
            raise ScrapeFailedException()
  
    def scrape_fr_google(self, symbol, correct_url):
        
        print_debug_stmt('scrape_fr_google')
        print_debug_stmt('correct_url')
        print_debug_stmt(correct_url)
        
        resp = requestsget(correct_url)
        print_debug_stmt('resp.status_code')
        print_debug_stmt(resp.status_code)
        
        if str(resp.status_code) == '200':
            
            
            parser = fromstring(resp.text)
            raw_html = parser.cssselect('#ires > ol div.g:nth-child(1)')[0]
            
            # dive must somehow relatable to finance (that his box is realy about the finance)
            if 'Google Finance' in raw_html.text_content():
            
                # semantic match #1 FOLLOW-UP (begin)
                span1st = raw_html.cssselect('h3 span')[0]
                print_debug_stmt('span1st')
                print_debug_stmt(span1st)
                print_debug_stmt('str(span1st.text_content())')
                print_debug_stmt(str(span1st.text_content()))
                company_name = span1st.text_content().lstrip('- ')
                
                print_debug_stmt('company_name')
                print_debug_stmt(company_name)
                
                tbl1st = raw_html.cssselect('table')[0]
                td1st = tbl1st.cssselect('td')[0]
                b1st = tbl1st.cssselect('b')[0]
                # at last, got the selector correct and price extracted
                last_trade_price = b1st.text_content()
                
                span2nd = tbl1st.cssselect('span')[1]
                last_trade_time = span2nd.text_content()
                year_atthemoment = date.today().strftime('%Y')
                last_trade_time = last_trade_time + ' ' + str(year_atthemoment)
                
                # this line  most match, in position and in content (semantically) w
                # the columns header stored in global constants (COL_NAMES) -- right
                # data must go to the right column
                temptupl = (symbol, company_name, 'google', last_trade_time, last_trade_price)
                # semantic match #1 FOLLOW-UP (end)

                temprowlist = []
                temprowlist.append(temptupl)
                tempdf = DataFrame(temprowlist, columns=COL_NAMES)
                return tempdf
            
            else:
                raise ScrapeFailedException()
         
        else:
            raise ScrapeFailedException()

