questions = q.preloads() + q.geopoint() + q.picture() + q.lga()

questions += [
    q.string("Facility name"),
    q.string("Street address"),
    q.string("Unique facility id"),
    q.string("Respondent #1 name"),
    q.string("Respondent #1 position within school"),
    q.phone_number("Respondent #1 phone number"),
    q.string("Respondent #2 name"),
    q.string("Respondent #2 position within school"),
    q.phone_number("Respondent #2 phone number"),



# [type] What type of school is this (what level of education)? (select one)
# {
#     "choices" : {
#         "Nursery/Pre-primary school only" : "nursery pre primary",
#         "Nursery/Pre-primary and primary school" : "nursery pre primary and primary",
#         "Primary school only" : "primary",
#         "Primary and secondary school" : "primary and secondary",
#         "Primary and junior secondary school" : "primary and jss",
#         "Primary, junior and secondary schools" : "primary jss and sss",
#         "Junior secondary school only" : "jss",
#         "Senior secondary school only" : "sss",
#         "Adult educational institution" : "adult ed",
#         "Adult literacy training" : "adult literacy",
#         "Adult vocational/technical training" : "adult vocational",
#         "Vocational school (post-primary)" : "vocational post primary",
#         "Vocational school (post-secondary)" : "vocational post secondary"
#         }
#     }

# [religious] Is this institution a religious school? (yes or no)

# [education type] What type of education does it offer? (select one)
# {
#     "choices" : {
#         "Formal education" : "formal",
#         "Formal education with religious component (integrated)" : "integrated",
#         "Exclusively religious education" : "religious"
#         }
#     }

# [managed by] Who manages the school? (select all that apply)
# {
#     "choices" : {
#         "Federal Government" : "federal govt",
#         "State Government" : "state govt",
#         "Local government" : "local govt",
#         "Private for profit" : "private for profit",
#         "Private not for profit" : "private not for profit",
#         "Other" : "other"
#         }
#     }

# =[infrastructure] Infrastructure=

# [all weather road] Is there an all weather road to this school? (yes or no)

# [days inaccessible] How many days in the past month was this school not accessible? (select one)
# {
#     "choices" : {"1-5 days" : "[1,5]",
#                   "6-15 days" : "[6,15]",
#                   "16-30 days" : "[16,30]",
#                   "More than 30 days" : "[31,infty)",
#                   "This road was always accessible" : "{0}"}
#     }


# [distance to secondary] What is the distance to the nearest secondary school in kilometers? (decimal)
# {
#     "relevant" : "[type]='nursery pre primary and primary' or [type]='primary' or [type]='primary and jss' or [type]='jss'"
#     }

# [transport to secondary] Is there daily public transport from this primary school to where nearest the secondary school is located? (yes or no)
# {
#     "relevant" : "[type]='nursery pre primary and primary' or [type]='primary' or [type]='primary and jss' or [type]='jss'"
#     }

# [power source types] What type(s) of power sources are available at this school? (select all that apply)
# {
#     "choices" : {"Generator" : "generator",
#                  "Solar system" : "solar",
#                  "Grid connection/power/PHCN" : "grid",
#                  "Other" : "other"}
#     }

# [days no electricity] How many days in past month was the school with no electricity (any source)? (integer)

# [repair time] The last time something broke how long did it take to get it fixed? (select one)
# {
#     "relevant" : "selected([power source types], 'Solar system') or selected([power source types], 'Generator')",
#     "choices" : {"Never broken yet" : "never broken",
#                  "Broke, fixed within a day" : 1,
#                  "Broke, fixed within a week" : 7,
#                  "Broke, fixed within a month" : 31,
#                  "More than 1 month" : "[31,infty)",
#                  "Not fixed yet" : "never fixed"}
#     }

# [water nearby] Is there a water source either on the premises or less than 100 meters away? (yes or no)

# [water sources] What is (are) the source(s) of water for this school? (select all that apply)
# {
#     "relevant" : "[water nearby] = 'yes'",
#     "choices" : {"Borehole/tube well" : "borehole tube well",
#                  "Protected dug well" : "protected dug well",
#                  "Unprotected dug well" : "unprotected dug well",
#                  "Protected spring" : "protected spring",
#                  "Unprotected spring" : "unprotected spring",
#                  "Tanker truck" : "tanker truck",
#                  "Rainwater collection tank" : "rainwater",
#                  "Public tap outside premises" : "public tap outside premises",
#                  "Tap at premises" : "tap at premises",
#                  "Cart with small tank/drum" : "cart with small tank drum",
#                  "Surface water such as pond/lake/river/stream" : "surface water",
#                  "Other" : "other"}
#     }

# [days no water] How many days in the past month was the school without water from any of the above sources? (integer)
# {
#     "relevant" : "[water nearby] = 'yes'"
#     }

# [days no potable water] How many days in the past month was the school without POTABLE water from any of the above sources? (integer)
# {
#     "relevant" : "[water nearby] = 'yes'"
#     }

# [physical condition] How would you characterize the physical structure of the school? (select one)
# {
#     "choices" : {
#         "Poorly maintained but still in use" : "poorly maintained",
#         "Not new but well maintained" : "well maintained",
#         "Newly Constructed" : "new",
#         "Dilapidated, not suitable for use" : "dilapidated"
#         }
#     }

# [latrine types] What type of latrines are on the premises? (select all that apply)
# {
#     "choices" : {
#         "Flush or pour flush toilet" : "flush toilet",
#         "Ventilated pit latrine with slab" : "ventilated pit latrine with slab",
#         "Pit latrine with slab" : "pit latrine with slab",
#         "Pit latrine without slab" : "pit latrine no slab",
#         "Open defecation (no facilities)" : "no facilities",
#         "Other" : "other"
#         },
#     "constraint" : ".='no_facilities' or not(selected(., 'no_facilities'))",
#     "jr:constraintMsg" : "No facilities cannot be selected with other options."
#     }

# [latrines separated by sex] Are there separate latrines for males and females? (yes or no)
# {
#     "relevant" : "[latrine types]!='no_facilities'"
#     }

# [latrines] How many of each type of sanitation system exist within the school? (integer table)
# {
#     "rows" : {
#         "'Improved' sanitation facilities" : "improved",
#         "Other sanitation facilities" : "not improved"
#         },
#     "relevant" : "[latrine types]!='no_facilities'"
#     }

# [days latrines not working] How many days in the past MONTH were more than half of these facilities not working? (integer)
# {
#     "relevant" : "[latrines improved] + [latrines not improved] > 0"
#     }

# [days rubbish appropriately disposed] How many times in the past 30 days was rubbish/waste burned or appropriately disposed? (integer)

# =[info tech] Information Technology=

# [landlines] How many working landline telephone numbers are there for this school? (integer)

# [mobile voice coverage] Is there reliable mobile voice coverage anywhere in the school premises? (yes or no)

# [cellular phone] Does the school have at least one functioning cellular phone that is not private? (yes or no)

# [computers] How many working computers exist in this school? (integer)

# [computers for students] How many of these working computers are for student use? (integer)

# [computers with internet] How many of the working computers at this school currently have working internet connection? (integer)

# [printer] Does the school have at least one working printer? (yes or no)

# =[teachers staff smcs] Teachers, Staff and School Management Committees (SMCs)=

# [teachers] What is the total number of teachers at the school? (integer table)
# {
#     "rows" : {"female" : "female", "male" : "male"}
#     }

# [qualified teachers] What is the number of qualified teachers with the following qualifications? (integer table)
# {
#     "rows" : {"Graduate with teacher qualification" : "graduate with qual",
#               "Nigeria Certificate in Education (NCE)" : "nce",
#               "Diploma, Grade II (Teacher Certificate Grade II)" : "grade two",
#               "Grade I" : "grade one"},
#     "columns" : {"female" : "female", "male" : "male"}
#     }

# [unqualified teachers] What is the number of unqualified teachers with the following qualifications or education level? (integer table)
# {
#     "rows" : {"Graduate without teacher qualification" : 1, 
#               "HSC/GCE A Level" : 2,
#               "WASC/GCE O Level/SSCE" : 3,
#               "Other" : "other"},
#     "columns" : {"female" : "female", "male" : "male"}
#     }

# [living quarters] Are there any teachers living quarters? (yes or no)

# [living quarters sufficient] How sufficient are the living quarters for teachers? (select one)
# {
#     "relevant" : "[living quarters]='yes'",
#     "choices" : {"Insufficient, we need to add extra living quarters for the teachers" : "insufficient",
#                  "Sufficient, we don't need to add any extra living quarters for the teachers" : "sufficient"}
#     }

# [living quarters condition] What is the physical condition of the teachers living quarters? (select one)
# {
#     "relevant" : "[living quarters]='yes'",
#     "choices" : {"Need no repairs" : 1,
#                  "Need minor repairs" : 2,
#                  "Need major repairs" : 3}
#     }

# [days understaffed] What is the number of days in past month that school was understaffed? (integer)

# [days understaffed and closed] What is the number of days in past month that school was closed due to lack of staff? (integer)

# [teachers on time] In your view, do teachers usually arrive to school on time? (yes or no)

# =[enrollment and attendance] STUDENT ENROLLMENT AND ATTENDANCE/TEACHER ATTENDANCE=

# [teacher attendance] What is the number of teachers who attended school during the last full school-going day? (integer)

# [max students] What is the maximum number of students that the school is designed to accommodate? (integer)

# [two shifts] Does the school operate in two shifts? (yes or no)

# [multiple class classrooms] How many classrooms have two or more classes taught at the same time? (integer)

# [enrollment] What is the total number of students enrolled during the current school year? (integer table)
# {
#     "rows" : {"female" : "female", "male" : "male"}
#     }

# [enrollment data collected] Is data being collected on the ages of enrolled students? (yes or no)

# [instruction] Please provide the following information on number of students (note)
# {
#     "relevant" : "[enrollment data collected]='yes'"
#     }

# [enrollment two] Number of students enrolled in school this school year (integer table)
# {
#     "relevant" : "[enrollment data collected]='yes'",
#     "rows" : {"primary 1-6" : "primary 1-6", "js 1-3" : "js 1-3", "ss 1-3" : "ss 1-3"},
#     "columns" : {"female" : "female", "male" : "male"}
#     }

# [repeating grades] Of those enrolled, number of students repeating the school year (integer table)
# {
#     "relevant" : "[enrollment data collected]='yes'",
#     "rows" : {"primary 1-6" : "primary 1-6", "js 1-3" : "js 1-3", "ss 1-3" : "ss 1-3"},
#     "columns" : {"female" : "female", "male" : "male"}
#     }

# [drop outs] Of those enrolled, number of students who dropped out since start of school year (integer table)
# {
#     "relevant" : "[enrollment data collected]='yes'",
#     "rows" : {"primary 1-6" : "primary 1-6", "js 1-3" : "js 1-3", "ss 1-3" : "ss 1-3"},
#     "columns" : {"female" : "female", "male" : "male"}
#     }

# [attendance] Of those enrolled, number of students who attended last full school-going day (integer table)
# {
#     "relevant" : "[enrollment data collected]='yes'",
#     "rows" : {"primary 1-6" : "primary 1-6", "js 1-3" : "js 1-3", "ss 1-3" : "ss 1-3"},
#     "columns" : {"female" : "female", "male" : "male"}
#     }

# =[fees] School Fees=

# [new student enrollment fee] What is the enrollment fee (cash) for NEW students for the school year (in naira)? (integer)

# [continuing student enrollment fee] What is the enrollment fee (cash) for continuing students for the school year (in naira)? (integer)

# [textbook fee] What is the textbook fee (cash) per student for the school year (in naira)? (integer)

# [follow national curriculum] Does this school follow a national curriculum? (yes or no)

# [booklist available] Would you be able to give us a copy of the booklist per class for this school year (GET COPY OF BOOKLIST IF POSSIBLE)? (yes or no)
# {
#     "relevant" : "[follow national curriculum]='no'"
#     }

# [uniform fee] What is the average school uniform fee (cash) per student for the school year (in naira)? (integer)

# [fee exemptions granted] Does the school grant exemptions from fees? (yes or no)

# [percent students exempt from fees] What is the percent of students exempt from fees? (integer)

# [in kind fees] What kind of IN KIND fees does the school charge? (string)

# =[budget] Budget=

# [funding sources] What are the main sources of funds for the school? (select all that apply)
# {
#     "choices" : {
#         "UBE Fund" : "ube",
#         "ETF" : "etf",
#         "LGA" : "lga",
#         "NGO" : "ngo",
#         "Other" : "other"
#         }
#     }

# [capitation grant] Does school receive a Capitation grant? (yes or no)

# [budgetary outlay timing] When does the School usually receive its budgetary outlay? (select one)
# {
#     "choices" : {
#         "Start of year" : "start",
#         "Middle of year" : "middle",
#         "End of year" : "end"
#         }
#     }

# [budget money spent by] Who decides how the budget money is spent ? (select all that apply)
# {
#     "choices" : {
#         "Principal" : "principal",
#         "School Management Committee" : "smc",
#         "Teachers" : "teachers",
#         "Other" : "other"
#         }
#     }

# [students on scholarship] How many students in the school receive scholarships? (integer)

# [scholarship amount] What is the scholarship amount for the school year? (integer)

# [teacher pay delayed] How many times has teacher pay been delayed in the past year? (integer)

# [teacher pay missed] How many times has teacher pay been missed in the past year? (integer)

# [reason teachers not paid] What is the reason that teachers have not been paid a wage? (select one)
# {
#     "choices" : {
#         "Those who were not paid were voluntary teachers" : "volunteers not paid",
#         "Budget delay or budget was not available" : "budget unavailable",
#         "Unqualified teachers were not paid" : "unqualified teachers not paid",
#         "Performance issue" : "performance issue",
#         "Other" : "other"
#         }
# }

# =[features and materials] SCHOOL FEATURES AND MATERIALS=

# [student meal location] Where do students usually have their meals? (select one)
# {
#     "choices" : {
#         "They do not have meals at school" : "no meals",
#         "Outside in a specific area within the school premises" : "outside",
#         "Classrooms" : "classrooms",
#         "Common room" : "common room",
#         "Other" : "other"
#         }
# }

# [functioning library] Does the school have a functioning library? (yes or no)

# [reading materials] How many books, magazines and other reading materials does library host? (integer)
# {
#     "relevant" : "[functioning library]='yes'"
#     }

# [new reading materials] How many times a year are new materials added to the library? (integer)
# {
#     "relevant" : "[functioning library]='yes'"
#     }

# [sports field] Does the school have an area or field to play sports? (yes or no)

# [covered roof] Does the school building have a covered roof? (yes or no)

# [boundary wall or fence] Does the school have a boundary wall/fence? (yes or no)

# [number of classrooms] The number of classrooms (integer table)
# {
#     "rows" : {
#         "total" : "total",
#         "in good condition" : "good condition",
#         "needing minor repairs" : "need minor repairs",
#         "needing major repairs" : "need major repairs",
#         "left unused" : "unused",
#         "having multiple uses" : "multiple use"
#         }
#     }

# [desks] What is the total number of desks in the school? (integer table)
# {
#     "rows" : {
#         "broken" : "broken",
#         "functional" : "functional"
#         }
#     }

# [benches and chairs] What is the total number of benches/chairs in the school? (integer table)
# {
#     "hint" : "I'm not sure how to handle three-seaters here.",
#     "rows" : {
#         "broken" : "broken",
#         "functional" : "functional"
#         }
#     }

# [chalkboards] Does each classroom have a chalkboard/blackboard? (yes or no)

# [english textbooks] How many English textbooks are there for every 10 students? (integer)

# [math textbooks] How many Math textbooks are there for every 10 students? (integer)

# [social studies textbooks] How many social studies textbooks are there for every 10 students? (integer)

# [science textbooks] How many primary science textbooks are there for every 10 students? (integer)

# [teachers guide] "Does each teacher have a teacher's guide or syllabus?" (yes or no)

# [notebooks or slates provided] Does the school provide notebooks or slates to the students? (yes or no)

# [notebooks or slates] How many notebooks or slates are there for every 10 students? (integer)
# {
#     "relevant" : "[notebooks or slates provided] = 'yes'"
#     }

# [pens and pencils provided] Does the school provide  PENS/PENCILS to the students? (yes or no)

# [pens and pencils sufficent] How sufficient Is the number of PENS/PENCILS to meet student needs? (select one)
# {
#     "choices" : {"Sufficient (every student has at least 1 pen/pencil)" : "100 percent",
#                  "Moderately insufficient (25% of students or fewer do not have a pen/pencil)" : "at least 75 percent",
#                  "Severely insufficient (more than 25% of students do not have a pen/pencil)" : "less than 75 percent"}
#     }
