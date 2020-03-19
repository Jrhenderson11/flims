#!/usr/bin/env python3

import re
import os
import json
import imdb
import pickle
import pprint
import random
import argparse
import simplenote

from getpass import getpass
from colorama import Fore, Style
from pyfiglet import figlet_format
from multiprocessing.dummy import Pool as ThreadPool

def red(string):
	return Fore.RED + Style.BRIGHT + string +Fore.RESET + Style.NORMAL

class Querier():

	def __init__(self, user, password):
		self.connector = simplenote.Simplenote(user, password)

	def get_lists(self):
		return self.connector.get_note_list()

	def get_dict(self):
		return {x['content'].split("\n")[0]:x['key'] for x in self.get_lists()[0]}

	def get_films_note(self):

		for k,v in self.get_dict().items():
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


def format_genre_list(genres):
	formatted = [Fore.RESET]
	colour_dict = {'Comedy':Fore.LIGHTBLUE_EX + Style.BRIGHT, 'Sci-Fi':Fore.LIGHTGREEN_EX + Style.BRIGHT, 'Horror': Fore.RED + Style.DIM, 'Romance':Fore.LIGHTMAGENTA_EX + Style.BRIGHT, 'Action':Fore.RED + Style.BRIGHT, 'Thriller':Fore.RED, 'Drama':Fore.GREEN, 'Mystery':Fore.YELLOW, 'Crime':Fore.LIGHTRED_EX + Style.BRIGHT, 'Adventure': Fore.YELLOW + Style.BRIGHT, 'Fantasy':Fore.MAGENTA}

	for g in genres:
		if g in colour_dict:
			formatted.append(colour_dict[g] + g + Fore.RESET + Style.NORMAL)
		else:
			formatted.append(g)

	return ' '.join(formatted).strip()

def print_film_dict(fdict):

	# Print out all film summaries
	table = [(v['title'][:44], str(v['year']), format_genre_list(v['genres'])) for k,v in fdict.items()]

	col_width = [max(len(x) for x in col) for col in zip(*table)]
	col_width[2] = 30

	index = 0
	for line in table:
		if index % 2 ==0 :
			print(Fore.LIGHTBLACK_EX, end='')
		print(" " + " | ".join(["{:{}}".format(x, col_width[i]) for i, x in enumerate(line)]) + Fore.RESET)

		index +=1


def pick_film(fdict):
	''' You asked your friends if they wanted to watch a film, they said "sure, got any ideas", you went "um..." so here you are'''

	titles = list(fdict.keys())
	randomer = random.Random()
	film = fdict[titles[randomer.randint(0, len(fdict)-1)]]

	print('Your chosen film is:')

	title = film['title']

	fonts = ['big', 'slant', 'small', 'standard', 'smslant', 'banner']
	colours = [Fore.LIGHTBLUE_EX + Style.BRIGHT, Fore.LIGHTGREEN_EX + Style.BRIGHT, Fore.RED + Style.DIM, Fore.LIGHTMAGENTA_EX + Style.BRIGHT, Fore.RED + Style.BRIGHT, Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.YELLOW + Style.BRIGHT, Fore.LIGHTRED_EX + Style.BRIGHT,  Fore.YELLOW + Style.BRIGHT, Fore.MAGENTA]

	font = fonts[randomer.randint(0, len(fonts)-1)]
	colour = colours[randomer.randint(0, len(colours)-1)]


	print(colour + figlet_format(title, font=font) + Fore.RESET + Style.NORMAL + '\n')
	print(Fore.LIGHTBLACK_EX + '	{}'.format(film['year']) + Fore.RESET + '\n')
	if 'plot outline' in film:
		print(film['plot outline'])


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-g', '--genre', help='Genre to filter for')
	parser.add_argument('-r', '--refresh', action='store_true', help='Forces tool to ignore cached data and refresh from remote')
	parser.add_argument('-p', '--pick_for_me', action='store_true', help='The option for when you\'re an indicisive idiot and need a python script to pick your films for you')

	args = parser.parse_args()
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
	pickle_file_name = 'flims.pickle'
	fdict = None

	print('[+] Retrieving note')
	remote_films = filter_films(q.get_films_note())

	# Check local file
	files = os.listdir()
	if not args.refresh and ('retrieved_flims' in files and pickle_file_name in files):

		contents = open('retrieved_flims', 'r').read()
		local_films = filter_films(contents)

		films_to_retrieve = [x for x in remote_films if x not in local_films]
	
		pickle_file = pickle.Unpickler(open(pickle_file_name, 'rb'))
		fdict = pickle_file.load()

	else:
		films_to_retrieve = remote_films

	# Save films
	open('retrieved_flims', 'w').write('\n'.join(remote_films))

	if films_to_retrieve != []:

		print('[+] Retrieving {} film details'.format(red(str(len(films_to_retrieve)))))

		# Spin up threads to retrieve from IMDb
		pool = ThreadPool(len(films_to_retrieve))
		retrieved = {list(d.keys())[0]:d[list(d.keys())[0]] for d in pool.map(get_film_meth, films_to_retrieve)}
		pool.close()
		pool.join()

		# Remove films with no results (probably notes not actual titles)
		retrieved = {k:v for k,v in retrieved.items() if v is not None}

		if fdict is not None:
			for x in retrieved.keys():
				fdict[x] = retrieved[x]
		else:
			fdict = retrieved

		# Save to pickle
		pickle_file = pickle.Pickler(open(pickle_file_name, 'wb'))
		pickle_file.dump(retrieved)

	if args.genre is not None:
		fdict = {k:v for k,v in fdict.items() if args.genre.lower() in str(v['genres']).lower()}

	if args.pick_for_me:
		pick_film(fdict)
	else:
		print_film_dict(fdict)
