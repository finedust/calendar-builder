#! /usr/bin/env python3


###
# File: downloader.py
#
# Description: Fetches the lectures list from the server API and adds them to an
#                exportable ics calendar file.
#
# Note: This file may be executed as a standalone script or called inside the app.
#
# Author: Francesco Tosello
###

__AUTHOR__ = "Francesco Tosello"


###
# Technical description
#
# 1. Choose a course code (e.g. 8010) -> get a curriculum code (e.g. Manifesto-2018_8010_000_000_2017)
# 2. Choose an year, and eventually some additional lectures from the list in the curriculum
# 3. From that get a list of teachings (ids, e.g. 323944)
# 4. Now get a calendar of the lessons for the next X days
###

###
# Error codes:
#
# 0 OK
# 1 Unable to get a list of lectures (curriculum not found, error fetching the list)
# 2 Malformed data
# 3 Can't export to file
# 4 User didn't confirm the operation
###


# Imports
from api_constants import *
from argparse import ArgumentParser
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from json import loads as parse_json, dumps as to_json_bytes
from datetime import datetime, timedelta, timezone
from re import sub
from ics import Calendar, Event

# Constants
NO_LIMIT_VALUE = 10000

DATE_FORMAT = "%d-%m-%y" # format used when parsing dates
DEFAULT_START_DATE = datetime.today().astimezone().strftime(DATE_FORMAT)
DEFAULT_END_DATE = (datetime.today().astimezone() + timedelta(3650)).strftime(DATE_FORMAT)
START_DATE_DESCRIPTION = "timetables starting date"
END_DATE_DESCRIPTION = "timetables end date"

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
LECTURE_COURSE_ID = "course"
LECTURE_START = "from"
LECTURE_END = "to"
LECTURE_NOTES = "note"
LECTURE_LOCATION = "location"

SUBJECT_REGEX = '\([\w\-]*\)' # remove this regex from title

CALENDAR_CREATOR = "Lecture Scraper"
DEFAULT_FILENAME = "lectures.ics"


def fetch_json(resource, filters = {}, fields = [], limit = 40):
	'''
	Fetches a json for given resource and parameters.
	Parameters:
		resource: string
		filters: dictionary
		fields: list of strings
	Returns the json records if positive, an empty list if an error occurred.

	TODO: Maybe a little escaping of the url must be done.
	TODO: Use filters (maybe)
	'''
	req_payload = {RESOURCE_PARAMETER: resource, LIMIT_PARAMETER: int(limit)}
	if filters: req_payload[FILTERS_PARAMETER] = filters
	if fields: req_payload[FIELDS_PARAMETER] = fields
	r = Request(DATA_QUERY_URL, headers = {'Content-Type': 'application/json'}, \
		data = to_json_bytes(req_payload).encode())
	try:
		with urlopen(r) as response:
			if response.code is not 200:
				print("Bad response code: {}".format(response.code))
				return []
			json = parse_json(response.read())
			if json['success'] is not True:
				print("An error occurred: {}".format(json['error']['message']))
				return []
			if 'total' in json['result'] and int(json['result']['total']) > 0:
				return json['result']['records']
			else:
				print("No results found.")
				exit(1)
	except HTTPError as httpe:
		print(httpe)
		exit(1)

def fetch_curricula(code):
	'''
	Fetch the curricula associated with this degree code.
	Returns a list.
	'''
	return fetch_json(RESOURCE_CURRICULA_AVAILABLE, {FIELD_CURRICULUM_COURSE_CODE: str(code)})


def fetch_teachings(curriculum, year = 0, teachings = [], inactive = False):
	'''
	This functions returns a list of teachings (dictionary).
	If no teaching is found then exit with a message.
	'''
	filters = {FIELD_CURRICULUM_CODE: str(curriculum)}
	if not teachings and year > 0:
		filters[FIELD_CURRICULUM_YEAR] = int(year)
		filtered_list = fetch_json(RESOURCE_CURRICULA_DETAILS, filters)
	elif teachings:
		tlist = fetch_json(RESOURCE_CURRICULA_DETAILS, filters, limit = NO_LIMIT_VALUE)
		filtered_list = []
		for t in tlist:
			if not t[FIELD_CURRICULUM_TEACHING_ID]: continue # skip this
			if int(t[FIELD_CURRICULUM_YEAR]) == int(year): # if the year is not specified no course will be added
				filtered_list.append(t)
			else: # do not add it twice
				for tin in teachings:
					try:
						cid = int(tin)
						if int(t[FIELD_CURRICULUM_TEACHING_ID]) == cid:
							filtered_list.append(t)
							break
					except ValueError:
						if type(tin) == str and tin.lower() in t[FIELD_CURRICULUM_SUBJECT_DESCRIPTION].lower():
							filtered_list.append(t)
							break
		if not filtered_list: # try with a rougher search
			for t in tlist:
				if not t[FIELD_CURRICULUM_TEACHING_ID]: continue # skip this
				for tin in teachings:
					if type(tin) is not str: continue # we don't need course ids
					if all([ \
						bool( x in t[FIELD_CURRICULUM_SUBJECT_DESCRIPTION].lower() ) for x in tin.lower().split() \
						]):
						filtered_list.append(t)
						break
	if not inactive and filtered_list:
		filtered_list_2 = []
		for t in filtered_list:
			if t[FIELD_CURRICULUM_ACTIVE]: filtered_list_2.append(t)
		filtered_list = filtered_list_2
	if filtered_list:
		return filtered_list
	else:
		print("No teaching has been found with your filters, please check your request.")
		exit(0) # it is not really an error

def fetch_courses(teachings, fork_regex = None):
	'''
	Get the list of lectures for these teachings.
	If the component id is not in the online teachings list then exclude it.
	Parameters: teaching (list), fork_regex (string).
	'''
	lectures = fetch_json(RESOURCE_TEACHING_DETAILS, \
		{FIELD_TEACHING_ROOT_ID: [\
			str(t[FIELD_CURRICULUM_TEACHING_ID]) for t in teachings if t[FIELD_CURRICULUM_TEACHING_ID] ]}, \
			limit = NO_LIMIT_VALUE)
	ldict = {}
	for l in lectures: ldict.setdefault(int(l[FIELD_TEACHING_ROOT_ID]), []).append(l)
	
	def choose_fork(teachings):
		'''
		Choose between a list of forked teachings.
		'''
		if fork_regex:
			valid_teachings = [t for t in teachings if fork_regex in t[FIELD_TEACHING_SUBJECT_DESCRIPTION]]
			if len(valid_teachings) == 1:
				return valid_teachings[0]
			else:
				print("Unable to extract a single match with the regex that you provided.")
		print("Chose a teaching from these:")
		for i,t in enumerate(teachings):
			print("{:d}. Description: {}".format(i+1, t[FIELD_TEACHING_SUBJECT_DESCRIPTION]) + \
				" lectured by {}".format(t[FIELD_TEACHING_TEACHER_NAME]) if t[FIELD_TEACHING_TEACHER_NAME] else "" + \
				" in {}.".format(t[FIELD_TEACHING_LANGUAGE]) if t[FIELD_TEACHING_LANGUAGE] else ".")
		num = 0
		while num < 1 or num > len(teachings):
			num = int(input("Insert the teaching number: "))
		return teachings[num-1]

	def resolve_teachings(code, teachings):
		'''
		Recursively select a list of teachings choosing between forks.
		Returns a list.
		'''
		choice_list = [t for t in teachings if t[FIELD_TEACHING_FATHER_ID] and int(t[FIELD_TEACHING_FATHER_ID]) == int(code)]
		if not choice_list: return [t for t in teachings if int(t[FIELD_TEACHING_ID]) == int(code)] # simple teaching
		sel_lectures = []
		# suppose that this is either a fork or an integrated course
		if choice_list[0][FIELD_TEACHING_TYPE] == FIELD_TEACHING_TYPE_PART:
			for t in choice_list: sel_lectures += resolve_teachings(t[FIELD_TEACHING_ID], teachings)
		elif choice_list[0][FIELD_TEACHING_TYPE] == FIELD_TEACHING_TYPE_FORK:
			sel_lectures += resolve_teachings(choose_fork(choice_list)[FIELD_TEACHING_ID], teachings)
		else:
			print("Unknown teaching type: {}".format(choice_list[0][FIELD_TEACHING_TYPE]))
			exit(2)
		return sel_lectures

	lectures = []
	for code in ldict: # cycle through courses
		lectures += resolve_teachings(code, ldict[code])
	return lectures

def retrieve_timetables(courses, start = DEFAULT_START_DATE, end = DEFAULT_END_DATE, coordinates = False):
	'''
	Given the courses retrieve the timetable.
	Returns a dictionary in which the keys are the course ids and the value a list
	 of structured data for the timetables.
	'''
	def parse_date(date_string, description):
		'''
		Get a date from a string, asking for a new if badly formatted.
		Parameters: date_string should be formatted as in DATE_FORMAT, and 
			description is a string to show which date to insert if needed.
		'''
		date = None
		while not date:
			try:
				date = datetime.strptime(date_string, DATE_FORMAT).astimezone()
			except ValueError as ve:
				date = None
				date_string = input("Please, insert the {} in this format: dd-mm-yy. Date: ".format(description))
		return date

	start_date = parse_date(start, START_DATE_DESCRIPTION)
	end_date = parse_date(end, END_DATE_DESCRIPTION)
	timetables = fetch_json(RESOURCE_TIMETABLES, \
		{FIELD_TIMETABLE_TEACHING_ID: [str(c[FIELD_TEACHING_ID]) for c in courses] }, \
		limit = NO_LIMIT_VALUE)
	room_codes = set([t[FIELD_TIMETABLE_ROOM_ID] for t in timetables if t[FIELD_TIMETABLE_ROOM_ID]])
	roomslist = [z for r in room_codes for z in r.split()]
	## Here comes a workaround for Briefcase that doesn't understands multiple list comprehension:
	#roomslist = []
	#for r in room_codes:
	#	roomslist += r.split()
	##
	rooms = fetch_json(RESOURCE_ROOMS, {FIELD_ROOMS_ROOM_ID: roomslist}, \
		limit = len(room_codes))
	classrooms = {}
	for r in rooms: classrooms.setdefault(r[FIELD_ROOMS_ROOM_ID], r)
	
	def build_location(classroom_ids):
		'''
		Make a string representing the location of the classroom(s).
		'''
		ids = classroom_ids.split()
		location = ""
		for idx, cl_id in enumerate(ids):
			if idx > 0: # not the first item
				location += " OPPURE "
			classroom = classrooms[cl_id]
			location += classroom[FIELD_ROOMS_NAME].title()
			if coordinates:
				if classroom[FIELD_ROOMS_LATITUDE]: # assume both coordinates null toghether
					location += (" - {} {}".format(\
						classroom[FIELD_ROOMS_LATITUDE], classroom[FIELD_ROOMS_LONGITUDE]))
			elif classroom[FIELD_ROOMS_FLOOR] or classroom[FIELD_ROOMS_ADDRESS]:
				location += " -"
				if classroom[FIELD_ROOMS_FLOOR]: location += " {}".format(classroom[FIELD_ROOMS_FLOOR])
				if classroom[FIELD_ROOMS_ADDRESS]:
					location += " in {}".format(classroom[FIELD_ROOMS_ADDRESS].replace(', ', ' '))
		return location

	def build_record(lecture):
		'''
		Builds a record that will be exported to the calendar starting from a lecture.
		'''
		return {LECTURE_COURSE_ID: int(lecture[FIELD_TIMETABLE_TEACHING_ID]), \
					LECTURE_START: datetime.strptime(str(lecture[FIELD_TIMETABLE_START]), DATETIME_FORMAT).astimezone(), \
					LECTURE_END: datetime.strptime(str(lecture[FIELD_TIMETABLE_END]), DATETIME_FORMAT).astimezone(), \
					LECTURE_NOTES: str(lecture[FIELD_TIMETABLE_NOTES]), \
					LECTURE_LOCATION: build_location(lecture[FIELD_TIMETABLE_ROOM_ID]), \
					}

	records = []
	for lecture in timetables:
		lec = build_record(lecture)
		if start_date <= lec[LECTURE_START] <= end_date:
			records.append(lec)
	return records

def export_calendar(courses, timetables, filename):
	c = Calendar(creator = CALENDAR_CREATOR)

	def create_lecture_event(lecture):
		'''
		Create the calendar event given the lecture.
		'''
		try:
			course = [x for x in courses if int(x[FIELD_TEACHING_ID]) == \
				lecture[LECTURE_COURSE_ID]][0] # assume there is only one
		except IndexError as ie:
			print("Something gone wrong, I can't find the course with this id: {}".format(lecture[LECTURE_COURSE_ID]))
			exit(2)
		e = Event()
		e.name = sub(SUBJECT_REGEX, '', course[FIELD_TEACHING_SUBJECT_DESCRIPTION].capitalize())
		if course[FIELD_TEACHING_TEACHER_NAME]:
			e.description = "Tenuto da {}".format(course[FIELD_TEACHING_TEACHER_NAME].title())
		e.begin = lecture[LECTURE_START]
		e.end = lecture[LECTURE_END]
		e.created = datetime.today().astimezone()
		if lecture[LECTURE_LOCATION]: e.location = lecture[LECTURE_LOCATION]
		if course[FIELD_TEACHING_URL]: e.url = course[FIELD_TEACHING_URL]
		return e

	for lecture in timetables:
		c.events.add(create_lecture_event(lecture))
	try:
		with open(filename, 'w') as ics_file:
			ics_file.writelines(c)
	except IOError as ioe:
		print("Unable to export the calendar to file: {}".format(ioe))
		exit(3)

def ask_for_confirmation(description = ""):
	'''
	Ask the user to confirm the output.
	'''
	if not quiet:
		repl = input(description)
		if repl and (repl is not 'y') and (repl is not "yes"):
			print("Ok, I quit.")
			exit(4)

def main(curriculum, year = 0, teachings = [], fork_regex = None, inactive = False, \
	start = DEFAULT_START_DATE, end = DEFAULT_END_DATE, filename = DEFAULT_FILENAME, coordinates = False):
	teachings = fetch_teachings(curriculum, year, teachings, inactive)
	if verbose or not quiet:
		print("I found {:d} teaching(s):".format(len(teachings)))
		for t in teachings: print(t)
	ask_for_confirmation("Do you confirm the teachings list? (Y/n)  ")
	courses = fetch_courses(teachings, fork_regex)
	if verbose or not quiet:
		print("So this is the list of your course(s) ({:d}):".format(len(courses)))
		for c in courses: print(c)
	ask_for_confirmation("Do you confirm the courses? (Y/n)  ")
	timetables = retrieve_timetables(courses, start, end, coordinates)
	if verbose or not quiet:
		print("I got {:d} lessons.".format(len(timetables)))
	ask_for_confirmation("Should I proceed and export the lessons? (Y/n)  ")
	export_calendar(courses, timetables, filename)
	print("Done, exported to {}.".format(filename))

def parse_args():
	parser = ArgumentParser(description = "Export your lectures in a calendar.", epilog = "written by " + __AUTHOR__)
	curricula_group = parser.add_mutually_exclusive_group(required = True)
	curricula_group.add_argument('-c', '--code', type = str, help = "This is your course's code (e.g. 8010).") # must be string otherwise the leading zero gets lost
	curricula_group.add_argument('--curriculum', help = "Insert directly the code of the curriculum.")
	parser.add_argument('-y', '--year', type = int, help = "Select the year of which you want to follow the lessons.")
	parser.add_argument('-t', '--teaching', dest = 'teachings', action = 'append', required = False, default = [], \
		help = "Add some extra teaching from your curriculum. \
		May be either a part of the subject name or better the component id of the teaching.")
	parser.add_argument('-f', '--file', default = DEFAULT_FILENAME, help = "Export the calendar to this file.")
	parser.add_argument('--inactive', '--include-inactive', dest = 'inactive', action = 'store_true', \
		help = "Search also for inactive teachings.")
	parser.add_argument('-fr', '--fork-regex', dest = 'fregex', help = "Match this string when choosing between forked teachings.")
	parser.add_argument('--from', '--from-date', dest = 'from_date', default = DEFAULT_START_DATE, \
		help = "Start date, format dd-mm-yy. Default today.")
	parser.add_argument('--to', '--to-date', default = DEFAULT_END_DATE, \
		help = "End date, format dd-mm-yy. Default approximatively 10 years (aka no end).")
	parser.add_argument('--coordinates', action = 'store_true', help = "Instead of the address store the gps coordinates of the classroom.")
	parser.add_argument('-v', '--verbose', action = 'store_true', help = "Print more information.")
	parser.add_argument('-q', '--quiet', action = 'store_true', help = "Do not ask for confirmation of operations.")
	args = parser.parse_args()

	global verbose, quiet
	verbose = args.verbose
	quiet = args.quiet

	if not args.curriculum: # inserted the course's code
		curricula = fetch_curricula(args.code)
		if not curricula: exit(1)
		if len(curricula) > 1:
			print("Choose a curriculum from these:")
			for i,curr in enumerate(curricula):
				print("{:d}. Code: '{}'. Description: {}.{}".format(i+1, curr[FIELD_CURRICULUM_CODE], \
					curr[FIELD_CURRICULUM_DESCRIPTION], \
					" Notes: " + curr[FIELD_CURRICULUM_NOTES] + "." if curr[FIELD_CURRICULUM_NOTES] else ''))
			num = 0
			while num < 1 or num > len(curricula):
				num = int(input("Insert the curriculum number: "))
			args.curriculum = curricula[num-1][FIELD_CURRICULUM_CODE]
		else: args.curriculum = curricula[0][FIELD_CURRICULUM_CODE]

	if not args.year and not args.teachings:
		print("Please, select an accademic year or at least a single teaching.")
		exit(1)

	return args.curriculum, args.year, args.teachings, args.fregex, args.inactive, \
		args.from_date, args.to, args.file, args.coordinates

if __name__ == '__main__':
	main(*parse_args())
