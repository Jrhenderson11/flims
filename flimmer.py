#!/usr/bin/env python3

import re
import os
import json
import imdb
import pickle
import pprint
import simplenote

from getpass import getpass
from colorama import Fore, Style
from multiprocessing.dummy import Pool as ThreadPool

def print_green(line):
	print(Fore.GREEN + Style.BRIGHT + line +Fore.RESET + Style.NORMAL)

def print_blue(line):
	print(Fore.BLUE + Style.BRIGHT + line +Fore.RESET + Style.NORMAL)

def print_red(line):
	print(Fore.RED + Style.BRIGHT + line +Fore.RESET + Style.NORMAL)


class Querier():

	def __init__(self, user, password):
		self.connector = simplenote.Simplenote(user, password)

	def get_lists(self):
		return self.connector.get_note_list()


	def get_dict(self):
		return {x['content'].split("\n")[0]:x['key'] for x in self.get_lists()[0]}

	def get_films_note(self):

		d = self.get_dict()
		
		for k,v in d.items():

			if 'FILM' in k:
				return self.connector.get_note(v)[0]['content']


class FilmParser():

	def __init__(self):
		self.ia = imdb.IMDb()

	def get_films(self, name):

		# Format name a bit (remove brackety stuff)

		name = re.sub("[\(\[].*?[\)\]]", "", name).strip()

		# Take first film for each
		possible = self.ia.search_movie(name)
		if len(possible) > 0:
			return self.ia.get_movie(possible[0].movieID)
		else:
			# Used to debug notes that aren't films
			print("No film found: {}".format(name))
			return None

def get_film_meth(name):
	'''Convinence method for parralellissatttion'''
	try:
		return {name:FilmParser().get_films(name)}
	except Exception as e:
		return {name:None}
	

def filter_films(contents):
	'''Return list of lines from text'''
	return list(filter(lambda x : '#' not in x and 'http' not in x, filter(None, contents.split('\n'))))


if __name__ == '__main__':

	# Read credentials
	try:
		with open('creds.json', 'r') as f:
			creds = json.loads(f.read())

		user = creds['username']
		password = creds['password']

	except Exception as e:
		print(e)
		user = input('Enter username:')
		password = getpass()

	# Check retrieved note against cached for differences

	# Retrieve notes
	q = Querier(user, password)

	print('[+] Retrieving note')
	remote_films = filter_films(q.get_films_note())

	# Check local file
	if 'retrieved_flims' in os.listdir():

		contents = open('retrieved_flims', 'r').read()
		local_films = filter_films(contents)

		films_to_retrieve = [x for x in remote_films if x not in local_films]
	else:
		films_to_retrieve = remote_films

	# Save films
	open('retrieved_flims', 'w').write('\n'.join(remote_films))
	
	pickle_file_name = 'flims.pickle'
	if films_to_retrieve != [] or pickle_file_name not in os.listdir():
	
		print('[+] Retrieving film details')

		# Spin up threads to retrieve from IMDb
		pool = ThreadPool(len(films_to_retrieve))
		fdict = {list(d.keys())[0]:d[list(d.keys())[0]] for d in pool.map(get_film_meth, films_to_retrieve)}
		pool.close()
		pool.join()

		# Remove films with no results (probably notes not actual titles)
		fdict = {k:v for k,v in fdict.items() if v is not None}
		
		# Save to pickle
		pickle_file = pickle.Pickler(open(pickle_file_name, 'wb'))
		pickle_file.dump(fdict)
	else:
		# Pickle file is up to date
		pickle_file = pickle.Unpickler(open(pickle_file_name, 'rb'))
		fdict = pickle_file.load()

	# Print out all film summaries
	summaries = {k:'{0} ({1}): {2}'.format(v['title'], v['year'], str(v['genres'])) for k,v in fdict.items()}

	pp = pprint.PrettyPrinter(width=120)
	pp.pprint(summaries)