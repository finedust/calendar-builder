###
# File: api_constants.py
#
# Description: Here are the needed API constants:
#                urls, datasets, resources and fields strings
###

DATA_QUERY_URL = "https://dati.unibo.it/api/action/datastore_search"
RESOURCE_PARAMETER = "resource_id"
FILTERS_PARAMETER = "filters"
FIELDS_PARAMETER = "fields"
LIMIT_PARAMETER = "limit"

# In the following 'resources' you may use '2018' instead of 'latest'
RESOURCE_CURRICULA_AVAILABLE = "curriculadisponibili_latest_it" # update: every day
FIELD_CURRICULUM_COURSE_CODE = "corso_codice" # string - not null
FIELD_CURRICULUM_COURSE_DESCRIPTION = "corso_descrizione" # string - not null
FIELD_CURRICULUM_CODE = "curriculum_codice" # string - not null, primary key, unique
FIELD_CURRICULUM_DESCRIPTION = "curriculum_descrizione" # string - not null
FIELD_CURRICULUM_NOTES = "curriculum_note" # string
FIELD_CURRICULUM_URL = "url" # string - not null

RESOURCE_CURRICULA_STRUCTURE = "curriculastruttura_latest_it" # update: every day
FIELD_CURRICULUM_GROUP_YEAR = "annno" # integer - not null
FIELD_CURRICULUM_GROUP_ID = "gruppo_id" # string - not null, primary unique
FIELD_CURRICULUM_GROUP_FATHER = "gruppo_padre" # string
FIELD_GROUP_MAX_CFU = "cfu_massimo" # integer - not null
FIELD_GROUP_MIN_CFU = "cfu_minimo" # integer - not null
FIELD_GROUP_MANDATORY = "obbligatorio" # string - not null
FIELD_GROUP_MANDATORY_YES = "obbligatorio"
FIELD_GROUP_MANDATORY_NO = "a scelta"

RESOURCE_CURRICULA_DETAILS = "curriculadettagli_latest_it" # update: every day
FIELD_CURRICULUM_YEAR = "anno" # integer, not null
FIELD_CURRICULUM_SUBJECT_CODE = "materia_codice" # string
FIELD_CURRICULUM_SUBJECT_DESCRIPTION = "materia_descrizione" # string - not null
FIELD_CURRICULUM_TEACHING_NOTES = "insegnamento_note" # string
FIELD_CURRICULUM_TEACHING_PERIOD = "insegnamento_periodo" # string
FIELD_CURRICULUM_TEACHING_CFU = "insegnamento_crediti" # integer
FIELD_CURRICULUM_TEACHING_ID = "componente_id" # integer
FIELD_CURRICULUM_ACTIVE = "attivo" # boolean - not null

RESOURCE_TEACHING_DETAILS = "insegnamenti_latest_it" # update: every day
FIELD_TEACHING_COURSE_CODE = "corso_codice" # string - not null
FIELD_TEACHING_SUBJECT_CODE = "materia_codice" # string - not null
FIELD_TEACHING_SUBJECT_DESCRIPTION = "materia_descrizione" # string - not null
FIELD_TEACHING_URL = "url" # string (uri)
FIELD_TEACHING_TYPE = "tipo" # string
FIELD_TEACHING_TYPE_PART = "modulo"
FIELD_TEACHING_TYPE_FORK = "sdoppiamento"
FIELD_TEACHING_TEACHER_CODE = "docente_codice" # string
FIELD_TEACHING_TEACHER_NAME = "docente_nome" # string
FIELD_TEACHING_LANGUAGE = "lingua" # string
FIELD_TEACHING_ID = "componente_id" # integer - not null, primary key, unique
FIELD_TEACHING_FATHER_ID = "componente_padre" # integer
FIELD_TEACHING_ROOT_ID = "componente_radice" # integer - not null

RESOURCE_TIMETABLES = "orari_latest" # update: every day
FIELD_TIMETABLE_TEACHING_ID = "componente_id" # integer - not null
FIELD_TIMETABLE_START = "inizio" # datetime - not null
FIELD_TIMETABLE_END = "fine" # datetime - not null
FIELD_TIMETABLE_ROOM_ID = "aula_codici" # string
FIELD_TIMETABLE_NOTES = "note" # string

RESOURCE_ROOMS = "aule_latest" # update: every day
FIELD_ROOMS_ROOM_ID = "aula_codice" # string - not null, primary key, unique
FIELD_ROOMS_NAME = "aula_nome" # string - not null
FIELD_ROOMS_ADDRESS = "aula_indirizzo" # string
FIELD_ROOMS_FLOOR = "aula_piano" # string 	
FIELD_ROOMS_LATITUDE = "lat" # number
FIELD_ROOMS_LONGITUDE = "lon" # number