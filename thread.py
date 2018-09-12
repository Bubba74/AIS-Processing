
# Test a threading way of closing the log file after the main program exits

from util.Logging import log, flush


log('hi')
log('hello')
log('a')
