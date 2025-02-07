import requests

API = "https://sis.jhu.edu/api/classes/"
with open('Key.txt', 'r') as f: KEY = f.readline()
KEYSTR = "?key="+KEY
CURRENTTERM = r"/Spring 2025" #USE /current IF YOU WANT THE CURRENT TERM
CURRENTTERM = CURRENTTERM.replace(" ","%20")
#The school names to search through
SCHOOLNAMES = [r"Whiting School of Engineering",r"Krieger School of Arts and Sciences"]
OUTPATH = r"CourseData.txt"

def getAllCourses():
    global CURRENTTERM
    print(f"Getting all courses from: {SCHOOLNAMES}")
    #Get all the data for each school in the current semester and put in one list
    courseRaws = []
    for school in SCHOOLNAMES:
        print(f"Getting Courses from: {school}")
        school = school.replace(" ","%20")
        r = requests.get(API + school + CURRENTTERM + KEYSTR)
        rj = r.json()
        courseRaws.extend(rj)
    #Now grab sections, it goes [[classcode,section],[classcode,section]]
    sections = []
    for course in courseRaws:
        section = course["SectionName"]
        coursecode = "".join(course["OfferingName"].split("."))
        sectioncode = coursecode+section
        sections.append(sectioncode)

    return courseRaws[:],sections[:] #Remove the 200 restriction when done

def getSectionRaws(courseRaws,sections):
    sectionRaws = []
    #For each course get the section data from the current term
    for i in range(len(courseRaws)):
        name = courseRaws[i]["OfferingName"]
        section = sections[i]
        print(f"{i}) Getting {name} : {section}...")
        r = requests.get(API + section + CURRENTTERM + KEYSTR)
        rj = r.json()

        #Check for weird circumstances
        if len(rj) != 1:
            continue #Just skip it no reason
            raise ValueError(f"ERROR: Data for {section} has length {len(rj)}")
        
        sectionRaws.append(rj[0])

    return sectionRaws
        
def writeData(sectionraws):
    global OUTPATH
    outfile = open(OUTPATH,"w")
    delim = "_"
    delim2 = ";"

    #outfile.write("name"+delim+
    #              "courseid"+delim+"profName"+delim+"campus_meeting#"+delim2+
    #              "startdate"+delim2+"enddate"+delim2+"DOW"+delim2+"starttime"
    #              +delim2+"endtime"+delim2+"place"+delim2+"room#"+delim+"...\n")
    
    for i,raw in enumerate(sectionraws):
        print(f"{i}) Writing Class: Section {raw["SectionName"]} - {raw["Title"]} ...")
        #Write the data needed,
        # should look like
        # name,courseid,profname,campus,meeting#,startdate,enddate,Dow,starttime,endtime,place,room#,...
        title = raw["Title"].replace(delim,"")
        title = title.replace(delim2,"")
        #Just so i know,
        if title != raw["Title"]: raise ValueError(f"!!Title changed for {raw['OfferingName']}!!")
        outfile.write(title+delim)
        outfile.write(raw["OfferingName"]+"."+raw["SectionName"]+delim)

        for prof in raw["InstructorsFullName"].split(";"):
            #Remove the delim from the prof string just incase
            prof = prof.replace(delim,"")
            prof = prof.replace(delim2,"")
            outfile.write(prof + delim2)
        outfile.write(delim)

        outfile.write(raw["Location"]+delim)
        #Now into the meetingtimes
        sectiondetails = raw["SectionDetails"][0]
        if len(raw["SectionDetails"]) != 1: #Just checking for potential edge cases
            raise ValueError(f"ERROR: section details for {raw["OfferingName"]+"."+raw["SectionName"]} has length {len(raw["SectionDetails"])}")
        meetings = sectiondetails["Meetings"]

        for i,meeting in enumerate(meetings):
            outfile.write(f"{i}"+delim2)
            dates = meeting["Dates"].split(" to ")
            outfile.write(dates[0]+delim2) #Start date
            outfile.write(dates[1]+delim2) #End date
            outfile.write(meeting["DOW"]+delim2) #DOW
            #times
            starttime,endtime = timeToMil(meeting["Times"])
            outfile.write(starttime+delim2)
            outfile.write(endtime+delim2)
            outfile.write(meeting["Building"]+delim2)
            outfile.write(meeting["Room"]+delim)

        outfile.write("\n")


    outfile.close()

def timeToMil(timestr):
    miltimes = []
    times = timestr.split(" - ")
    for time in times:
        miltime = time[:5].replace(":","")
        if "PM" in time:
            if miltime[:2] != "12":
                miltime = str(int(miltime)+1200)
        elif "AM" in time:
            miltime = miltime
        else:
            print("!!No times!!")
            return ("","")
        miltimes.append(miltime)

    if int(miltimes[1]) < int(miltimes[0]):
        raise ValueError(f"Start time {miltimes[0]} is larger than endtime {miltimes[1]}")
    
    return tuple(miltimes)




if __name__ == "__main__":
    courseraws,sections = getAllCourses()
    sectionraws = getSectionRaws(courseraws,sections)
    writeData(sectionraws)

    print("Finished")
    