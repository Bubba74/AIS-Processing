
import os
from time import time

def mkdir(dirname):
	if not os.path.isdir(dirname):
		os.mkdir(dirname)
	
if 'buffered' not in globals():
	buffered = []
	buffer_length = 100

	#Create the logs dir if it does not already exist
	mkdir('logs')
	
	#Write to the next log file
	index = 0
	time = str(round(time(),0))
	while os.path.isfile('logs/'+str(index)+'.log'):
		index += 1
	output_file_name = 'logs/'+ str(index) + '.log'
	fout = open(output_file_name, 'w')

def flush():
	global buffered
	for string in buffered:
		fout.write(string+'\n')
	fout.flush()
	buffered = []

def log(string, console=True):
	if console:
		print string

	buffered.append(str(string))
	if len(buffered) == buffer_length:
		flush()

import threading

class FinalFlush (threading.Thread):
	def __init__(self, group=None, target=None, name=None, verbose=None, main_thread=None):
		super(FinalFlush,self).__init__(group=None, target=None, 
			              name=None, verbose=None)
		self.main_thread = main_thread
		self.func = target
	def __init__(self, main_thread, target):
		super(FinalFlush, self).__init__(self)
		self.main_thread = main_thread
		self.target	 = target

	def run ():
		self.main_thread.join()
		self.target()

t = FinalFlush(target=flush, main_thread=threading.current_thread())
t.start()


	
