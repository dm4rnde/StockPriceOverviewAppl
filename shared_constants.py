# semantic match #1 FOLLOW-UP
# WARNING! IF CHANGE BELOW SEMANTICALLY (i.e., ADD/REMOVE COLUMN, REORDERING),
# PLEASE SEARCH OVER THE PROJECT FOR "semantic match #1 FOLLOW-UP"
# (these places needs adjusting accordingly)
COL_NAMES = ['Symbol', 'Company (Exchange)', 'Source', 'Last trade time', 'Last trade price']
# symbol can be global, like NASDAQ:TSLA
# or local (let user decide);
# only source currently is: google; but 
# there could be also yahoo (not implemented)
# this is the columns that appear on the GUI and in the file;

# this allows to turn debugging on
# in case there is a problem;
# this is custom-made approach to
# getting more info on overall 
# process;
# turn this on when need to find 
# difficult problem, off when 
# pushing code to repository
DEBUG_ON = False

# print debug statement;
# output debug messages through 
# this method; then debugging output 
# can be turned off/on in one place,
# from here
def print_debug_stmt(*pars):
    if DEBUG_ON:
        print(pars)