# To write a first draft of the LGA survey, I'll start by creating a
# list of questions.

from txt2xform import *
import json

questions = [
    q(u"Name of LGA chairman", u"lga chairman name", "string"),
    q(u"Contact Phone number", u"lga chairman number", "phone number"),
    q(u"Name of LGA Secretary", u"lga secretary name", "string"),
    q(u"Population of LGA", u"lga population"),
    q(u"What year is this population data from?", u"lga population year of data"),
    q(u"Percentage of population that is rural", u"lga population rural", "percentage"),
    q(u"Area in square kilometers", u"lga area"),
    q(u"Total number of full time employed staff", u"lga full time staff"),
    ]

rows = [
    u"Overall management",
    u"Health",
    u"Education",
    u"Agriculture",
    (u"Public works/infrastructure", u"infrastructure"),
    u"Finance",
    u"Others",
    u"Total"
    ]

columns=[
    {"text" : u"Number full time", "name" : u"full time"},
    {"text" : u"Number working today", "name" : u"working today"},
    {"text" : u"Name of supervisory counselor", "name" : u"supervisory counselor", "question_type" : "string"},
    {"text" : u"Qualification of Supervisory Counselor", "name" : u"supervisory counselor qualification", "question_type" : "string"},
    {"text" : u"Median qualification", "question_type" : "string"},
    {"text" : u"Qualification of Supervisory Counselor", "name" : u"supervisory counselor qualification", "question_type" : "string"},
    {"text" : u"Median salary for extension worker"},
    {"text" : u"Contact phone number of supervisory counselor", "name" : u"supervisory counselor number", "question_type" : "phone number"},
    ]

questions += table(rows=rows, columns=columns)

columns = [
    {"text" : u"Annual budget (naira)", "name" : u"budget"},
    {"text" : u"Percentage disbursed till now for this year", "name" : u"budget spent to date", "question_type" : "percentage"},
    ]

questions += table(rows=rows, columns=columns)

rows = [
    u"Electricity",
    u"Water",
    u"Internet",
    u"Security",
    u"Cellular coverage",
    u"Computers"
    ]

columns = [
    {
        "question_type" : "select one",
        "text" : u"How would you rate the reliability of this service in the LGA?",
        "name" : u"reliability",
        "choices" : [
            (u"Always reliable", u"always"),
            (u"Sometimes reliable", u"some times"),
            (u"Never reliable", u"never"),
            (u"Service not available in LGA office", u"unavailable"),
            ]
        },
    ]

questions += table(rows=rows, columns=columns)

questions += [
    q(u"What is the distance from the LGA to the state capital, measured in kilometers?", u"kilometers to state capital"),
    q(u"What is the journey time from the LGA to the state capital, measured in minutes?", u"minutes to state capital"),
    q(u"How would you rate the accessibility to the LGA headquarters?",
      u"lga headquarters accessibility",
      "select one",
      choices=[
            u"All year",
            u"Seasonal",
            ]
      )
    ]


# <%
# table = {
#     "rows" : [
#         "Cars",
#         "Pick up trucks",
#         "Motorcycles",
#         "Bicycles",
#         "Other"
#         ],
#     "columns" : [
#         ["Total number", {
#                 "tag" : "total"
#                 }],
#         ["Number functional", {
#                 "tag" : "functional"
#                 }]
#         ]
#     }
# %>
# <%include file="table.txt" args="table=table"/>

# [transport other means] What are the other means of transportation in the LGA? (string)

# [dev intro] What are the four main partners in development working within the LGA? (note)

# %for i in range(1,5):
# [dev ${i} name] #${i}: Name of partner organization/agency etc (string)

# [dev ${i} type] #${i}: Describe the organization/partner (select one)
# {
#     "choices" : [
#         "Bilateral",
#         "Multilateral",
#         "Domestic NGO",
#         "International NGO",
#         "Other"
#         ]
# }

# [dev ${i} sector] #${i}: Sector of operation (string)

# [dev ${i} start date] #${i}: Start date of initiatives (date)

# [dev ${i} budget] #${i}: Approximate annual budget (naira) (integer)

# [dev ${i} phone number] #${i}: Local contact phone number (phone number)

# %endfor

# =[markets section] Markets=

# [markets] What is the number of major markets in the LGA? (integer)

# [markets daily] How many are daily markets? (integer)

# [markets weekly] How many are weekly markets? (integer)

# [markets inaccessible] How many markets were inaccessible during the previous month? (integer)

# [markets inaccessible reasons] What are the main reasons that markets were inaccessible during the previous month? (string)

# =[facilities] Facility Inventory=

# [school intro] Please get the following information for all schools in the LGA. (note)

# <%
# school_types = [
#     "Pre-primary",
#     "Primary",
#     "Junior Secondary School",
#     "Senior Secondary School",
#     "Secondary Schools with boarding facilities",
#     "Adult education institution",
#     "Religious School"
#     ]

# info = [
#     ["Total Number in LGA", {
#             "tag" : "total"
#             }],
#     ["Number closed in the past month", {
#             "tag" : "number closed past month"
#             }],
#     ["Main Reason for closure in the past month", {
#             "tag" : "closed past month reason",
#             "type" : "string"
#             }],
#     ["Number of days of closure in the past month", {
#             "tag" : "days closed past month"
#             }],
#     ["Total staff in the facility", {
#             "tag" : "total staff"
#             }],
#     ["Total staff absent for any day in the past month", {
#             "tag" : "total staff absent"
#             }],
#     ["Number of facilities not accessible by road in the past month", {
#             "tag" : "number inaccessible past month"
#             }],
#     ["Main reason for no-access in the past month", {
#             "tag" : "inaccessible reason",
#             "type" : "string"
#             }]
#     ]

# table = {
#     "rows" : school_types,
#     "columns" : info,
#     "prefix" : "education"
#     }
# %>
# <%include file="table.txt" args="table=table"/>

# [health intro] Please get the following information for all health facilities in the LGA. (note)

# <%
# health_facility_types = [
#     "Primary health clinic",
#     "Primary health care center",
#     "Health post",
#     "Specialist hospital",
#     "General hospital",
#     "Maternity ward",
#     "Cottage hospital",
#     "Comprehensive health center",
#     "Dental clinic",
#     "Federal medical center",
#     "Teaching hospital",
#     "Ward model primary health care center",
#     "Dispensary"
#     ]

# table = {
#     "rows" : health_facility_types,
#     "columns" : info,
#     "prefix" : "health"
#     }
# %>
# <%include file="table.txt" args="table=table"/>

survey = Survey(u"LGA", questions)

print json_dumps(survey)
# print survey.__unicode__()

