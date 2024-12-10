#import bokeh as bk
from bokeh.plotting import show, curdoc, figure
from bokeh.layouts import layout 
import bokeh.models as mo
import pandas as pd
import numpy as np

INPATH = r"CourseData.txt"
DELIM = "_"
DELIM2 = ";"
DATANAMES = ["name","courseid","profNames","campus","meetings"]
DATANAMES2 = ["startdate","enddate","DOW","starttime","endtime","bldg","room"]
MINTIMEOPEN = 0 #Exclusive

def removeOnlineCourses(allData):
    onCampuslines = []
    indexer = np.isin(allData,"None" + DELIM2*4+DELIM)
    onCampuslines = allData[indexer == False]
    return list(onCampuslines)

def unpackline(line,datanames,datanames2):
    #Load the global variables in
    global DELIM
    global DELIM2

    #Dictionary because bokeh
    # File structure:
    # name_courseid_profName;_campus_meeting#;startdate;enddate;DOW;starttime;endtime;bldg;room#_...
    line = line.split(DELIM)
    course = {}
    course["meetings"] = []
    for i,elm in enumerate(line):
        parts = elm.split(DELIM2)
        if i >= 5 or datanames[i] == "meetings":
            data = {}
            parts.pop(0)
            for j,part in enumerate(parts):
                data[datanames2[j]] = part
            course["meetings"].append(data)

        else:
            data = []
            for part in parts:
                data.append(part)
            course[datanames[i]] = data

    course["meetings"].pop()
    course["profNames"].pop()
    return course

def separateData(courselist):
    sepcourselist = []
    for course in courselist:
        sepcourses = []
        for meeting in course["meetings"]:
            sepcourse = {}
            sepcourse["name"] = course["name"]
            sepcourse["courseid"] = course["courseid"]
            sepcourse["profNames"] = course["profNames"]        
            sepcourse["campus"] = course["campus"]
            sepcourse["startdate"] = meeting["startdate"]
            sepcourse["enddate"] = meeting["enddate"]
            sepcourse["DOW"] = meeting["DOW"]
            sepcourse["starttime"] = meeting["starttime"]
            sepcourse["endtime"] = meeting["endtime"]
            sepcourse["bldg"] = meeting["bldg"]
            sepcourse["room"] = meeting["room"]
            sepcourses.append(sepcourse)
        sepcourselist += (sepcourses)
    return sepcourselist

def separateroomTimes(roomtimes):
    seproomtime = {}
    for room,data in roomtimes.items():
        for weekday,times in data.items():
            seproomtime[room+":"+weekday] = times
    return seproomtime
            
#list appending with return
def list_append(lst, item):
    lst.append(item)
    return lst

def findRoomTimes_Used(sepdata):
    roomTimes_Used = {}
    #Loop through and get a dictionary of rooms
    # which each has a list in it
    # which each entry of the list is a dictionary of starttime, endtime, DOW
    for course in sepdata:
        bldgRoom = course["bldg"] + ":" + course["room"]
        if not (course["starttime"] == "" or course["endtime"] == ""):
        #Put it in a dictionary for easier usage
            roomTimes_Used[bldgRoom] = list_append(roomTimes_Used.get(bldgRoom,[]),
            {"starttime":course["starttime"],"endtime":course["endtime"],
            "DOW":course["DOW"],"startdate":course["startdate"],
            "enddate":course["enddate"]})
    
    roomTimes_Used.pop(":")
    return roomTimes_Used

def miltomin(mil):
    milstr = str(mil)
    milhour = milstr[:2]
    milmin = milstr[2:4]
    hour = int(milhour)
    min = int(milmin)
    while hour > 0:
        hour += -1
        min += 60

    return min

def mintomil(min,delim = ""):
    hour = 0
    while min >= 60:
        hour += 1
        min -= 60
    
    hourstr = str(hour).zfill(2)
    minstr = str(min).zfill(2)
    mil = hourstr+delim+minstr
    return mil

def findRoomTimes_Unused(sepdata):
    roomtime_Used = findRoomTimes_Used(sepdata)
    #Loop through rooms, 
    # get a list of lists of roomtimes, 
    # change em to list of roomtimes_unused
    timesInUse = {}
    for room,timeslist in roomtime_Used.items():
        
        weekTimes = {"M":[],"T":[],"W":[],"H":[],"F":[]}
        for time in timeslist:

            for day in time["DOW"].replace("Th","H"):
                try:
                    starttime = miltomin(time["starttime"])
                    endtime = miltomin(time["endtime"])
                    duration = endtime-starttime
                    
                    weekTimes[day].append([starttime,duration])
                except:
                    print(f"{room} is missing a time")
        #Simplify the lists
        for day in weekTimes:
            weekTimes[day].sort(key = lambda x: x[0])

        timesInUse[room] = weekTimes
    
    roomTimes_Unused = {}
    for room,weekTimes in timesInUse.items():

        weekTimesUnused = {}
        for weekday,times in weekTimes.items():
            times.append([24*60,0])
            timeslist = [[0,times[0][0]]]
            #List structure [endtime,duration till next]
            for i in range(len(times)):
                if times[i][0] != 24*60: #make sure it isn't the last entry
                    endtime = times[i][0] + times[i][1]
                    durationtillnext = times[i+1][0] - endtime

                    if durationtillnext > MINTIMEOPEN:
                        timeslist.append([endtime,durationtillnext])
                else:
                    endtime = times[i][0] + times[i][1]
                    durationtillnext = 24*60 - endtime

            weekTimesUnused[weekday] = timeslist
            
        roomTimes_Unused[room] = weekTimesUnused

    return roomTimes_Unused

def createFilteredTables(sepcourselist): 
    #Create datatable
    dataframe = pd.DataFrame(sepcourselist)
    source = mo.ColumnDataSource(data = dataframe)
    fsource = mo.ColumnDataSource(data = dataframe)
    columns = [
            mo.TableColumn(field = "name", title = "Class Title"),
            mo.TableColumn(field = "courseid", title = "Course ID"),
            mo.TableColumn(field = "campus", title = "Campus"),
            mo.TableColumn(field = "bldg",title = "Building"),
            mo.TableColumn(field = "room",title = "Room"),
            mo.TableColumn(field = "starttime",title = "Start Time"),
            mo.TableColumn(field = "endtime",title = "End Time"),
            mo.TableColumn(field = "DOW",title = "Days of the week"),
            mo.TableColumn(field = "profNames", title = "Professor"),
            mo.TableColumn(field = "startdate",title = "Start Date"),
            mo.TableColumn(field = "enddate",title = "End Date")

    ]
    table = mo.DataTable(source = source, columns = columns, resizable = "both",height = 600,width = 1200)
    ftable = mo.DataTable(source = fsource, columns = columns, resizable = "both",height = 600,width = 1200)


    #Create filter inputs
    # Get options for the multiselect
    bldgset = sorted(list(set(dataframe["bldg"])-set([''])))
    bldgset.reverse()
    options = [("All","All")]
    for elm in bldgset:
        options.append([elm,elm])
    bldgtitle = mo.Div(text = r'<p style="font-size:14px"><b>Building</b></p>')
    bldgselect = mo.MultiSelect(options=options,value = ["All"],width = 200)
    bldgbox = mo.Column(bldgtitle,bldgselect)   
    # Get input for room#
    roomtitle = mo.Div(text = r'<p style="font-size:14px"><b>Room#</b></p>')
    roomInput = mo.TextInput(placeholder = "All",width = 200)
    roombox = mo.Column(roomtitle,roomInput)
    # Get input for DOW
    DOWtitle = mo.Div(text = r'<p style="font-size:14px"><b>Days of the Week (i.e. MTWThF)</b></p>')
    DOWInput = mo.TextInput(placeholder = "All",width = 200)
    DOWbox = mo.Column(DOWtitle,DOWInput)
    # Get input for prof name
    proftitle = mo.Div(text = r'<p style="font-size:14px"><b>Professor Name</b></p>')
    profInput = mo.TextInput(placeholder = "All",width = 200)
    profbox = mo.Column(proftitle,profInput)
    # Get input for class name
    nametitle = mo.Div(text = r'<p style="font-size:14px"><b>Class Name</b></p>')
    nameInput = mo.TextInput(placeholder = "All",width = 200)
    namebox = mo.Column(nametitle,nameInput)
    # Get input for time
    timeslider = mo.RangeSlider(start = 6*60,end = 24*60,value = (6*60,24*60),
                                show_value = False, tooltips = False,
                                step = 10,width = 1000)
    timediv = mo.Div(text = r'<p style="font-size:14px">Range of Time: <strong>6:00AM</strong> to <strong>12:00AM</strong></p>')
    #  Time inputbox
    starttimeinput = mo.NumericInput(mode = "int",low = 600,high = 2400,value = 600,format = "0000",align = "start",width = 90)
    endtimeinput = mo.NumericInput(mode = "int",low = 600,high = 2400,value = 2400,format = "0000",align = "end",width = 90)
    timelinkcallback = mo.CustomJS(args = {"startbox":starttimeinput,"endbox":endtimeinput,"timeslider":timeslider,"timediv":timediv},code=r"""
                                function miltomins(mil){
                                    const milstr = "0"+mil.toString();   
                                    let hours = parseInt(milstr.slice(-4,-2));
                                    let mins = parseInt(milstr.slice(-2));
                                    return (60*hours + mins);         
                                }
                                function minstomil(mins){
                                    let hours = 0
                                    while (mins >= 60){
                                        hours++;
                                        mins -= 60;
                                    }
                                    hours = hours.toString();
                                    mins = mins.toString();
                                    let mil = parseInt(hours+("0" + mins).substr(-2));
                                    return mil
                                }
                                                        
                                                        
                                if (cb_obj == startbox){
                                    //console.log(miltomins(startbox.value))
                                    timeslider.value = [miltomins(startbox.value),timeslider.value[1]];
                                    timeslider.properties.value_throttled.change.emit()
                                }
                                if (cb_obj == endbox){
                                    //console.log(miltomins(endbox.value))
                                    timeslider.value = [timeslider.value[0],miltomins(endbox.value)];
                                    timeslider.properties.value_throttled.change.emit()
                                }
                                if (cb_obj == timeslider){
                                    endbox.value = minstomil(timeslider.value[1]);
                                    startbox.value = minstomil(timeslider.value[0]);
                                }
                                   
                                   """)
    starttimeinput.js_on_change("value",timelinkcallback)
    endtimeinput.js_on_change("value",timelinkcallback)
    timeslider.js_on_change("value",timelinkcallback)
    timebox = layout([[timediv],[starttimeinput,timeslider,endtimeinput]])
    

    #Create callbacks to filter table
    filtercallback = mo.CustomJS(args={"source":source,"fsource":fsource,"bldgbox":bldgselect,
                                       "roombox":roomInput,"profbox":profInput,"namebox":nameInput,
                                       "timeslider":timeslider,"DOWbox":DOWInput,"timediv":timediv},code=r"""
        function cmpInput(cmpstr,sourcestr){
            let boolval = true
            if (sourcestr === null){
                boolval = true
            }
            else{
                boolval = sourcestr.toLowerCase().includes(cmpstr.toLowerCase());
            }
            return boolval
        }
            
        
        const sourcedata = source.data;
        const bldgs = source.data.bldg;
        let fsourcedata = Object.assign({}, sourcedata);
        const selects = bldgbox.value;
        const room = roombox.value;
        const prof = profbox.value;
        const name = namebox.value;
        const timerange = timeslider.value;
        const timestart = timerange[0];
        const timeend = timerange[1];
        let start = timestart
        let end = timeend

        //Change div time based on slider
        let hoursstart = 0;
        let startAMPM = "AM";
        while (start >= 60){
            hoursstart++;
            start -= 60;
        }
        if (hoursstart == 24){
            hoursstart = 12;
            startAMPM = "AM";
        }
        else if (hoursstart == 12){
            startAMPM = "PM";
        }
        else if (hoursstart > 12) {
            hoursstart -= 12;
            startAMPM = "PM";
        }
        let endAMPM = "AM";
        let hoursend = 0;
        while (end >= 60){
            hoursend++;
            end -= 60;
        }
        if (hoursend == 24){
            hoursend = 12;
            endAMPM = "AM";
        }
        else if (hoursend == 12){
            endAMPM = "PM";
        }
        else if (hoursend > 12) {
            hoursend -= 12;
            endAMPM = "PM";
        }
        timediv.text = '<p style="font-size:14px">Range of time: <strong>' + Math.round(hoursstart) + ":" + ("0" + Math.round(start)).substr(-2) + startAMPM + "</strong> to <strong>" + Math.round(hoursend) + ":" + ("0" + Math.round(end)).substr(-2) + endAMPM + "</strong></p>";

        //Filter the table
          //Find indexes
        let findexes = []
        for(let i = 0; i < sourcedata.name.length; i++){
            //Test if room is good
            let roombool = cmpInput(room,sourcedata.room[i]);

            //Test if prof is good
            let profbool = false;
            for(let j = 0; j < sourcedata.profNames[i].length; j++){
                if (cmpInput(prof,sourcedata.profNames[i][j])){
                    profbool = true;
                }
            }
            //Test if name is good
            let namebool = (cmpInput(name,sourcedata.name[i][0]));
            
            //Test if bldg is good
            const bldgbool = ((selects.indexOf(sourcedata.bldg[i]) > -1) || (selects.indexOf("All") > -1));

            //Test if time is good
                //start time
            let sourcestarthour = sourcedata.starttime[i].slice(0,2)
            let sourcestartmin = sourcedata.starttime[i].slice(2,4)
            const sourcestarttime = parseInt(sourcestarthour)*60 + parseInt(sourcestartmin)
            const cmpstarttime = parseInt(timestart)

                //end time
            let sourceendhour = sourcedata.endtime[i].slice(0,2)
            let sourceendmin = sourcedata.endtime[i].slice(2,4)
            const sourceendtime = parseInt(sourceendhour)*60 + parseInt(sourceendmin)
            const cmpendtime = parseInt(timeend)

            const startinbool = (cmpstarttime <= sourceendtime && cmpstarttime >= sourcestarttime)
            const endinbool = (cmpendtime <= sourceendtime && cmpendtime >= sourcestarttime)
            const containsbool = (cmpendtime > sourceendtime && cmpstarttime < sourcestarttime)
            const timebool = (startinbool || endinbool || containsbool)

            //Test if DOW is good
            let DOWbool = true;
            //const DOWs = ["F","H","W","T","M"];
            let DOWdata = new String(DOWbox.value);
            DOWdata = DOWdata.replace("Th","H").toLowerCase();
            if (DOWdata === null){
                DOWbool = true;
            }
            else{
                let DOWboollist = [];
                let sourceDOWlist = new String(sourcedata.DOW[i]);
                sourceDOWlist = sourceDOWlist.replace("Th","H").toLowerCase();
                for(let j = 0;j < DOWdata.length;j++){
                    if (sourceDOWlist.indexOf(DOWdata[j]) > -1){
                        DOWboollist.push(true);                        
                    }
                    else{
                        DOWboollist.push(false);
                    }
                }
                if (DOWboollist.indexOf(false) > -1){
                    DOWbool = false;
                }
            }
            
            // Combine tests
            if ((timebool && bldgbool && roombool && profbool && namebool && DOWbool)){
                findexes.push(sourcedata.index[i])
            } 

            
        }
        fsourcedata.index = findexes
        fsourcedata.DOW = Array.from(findexes,(i) => fsourcedata.DOW[i])
        fsourcedata.bldg = Array.from(findexes,(i) => fsourcedata.bldg[i])
        fsourcedata.campus = Array.from(findexes,(i) => fsourcedata.campus[i])
        fsourcedata.courseid = Array.from(findexes,(i) => fsourcedata.courseid[i])
        fsourcedata.enddate = Array.from(findexes,(i) => fsourcedata.enddate[i])
        fsourcedata.endtime = Array.from(findexes,(i) => fsourcedata.endtime[i])
        fsourcedata.name = Array.from(findexes,(i) => fsourcedata.name[i])
        fsourcedata.profNames = Array.from(findexes,(i) => fsourcedata.profNames[i])
        fsourcedata.room = Array.from(findexes,(i) => fsourcedata.room[i])
        fsourcedata.startdate = Array.from(findexes,(i) => fsourcedata.startdate[i])
        fsourcedata.starttime = Array.from(findexes,(i) => fsourcedata.starttime[i])
        fsource.data = fsourcedata;   
        //console.log(fsource.data)  
        //console.log(source.data)
        //console.log("Finished")          
                                 """)
    bldgselect.js_on_change("value",filtercallback)
    roomInput.js_on_change("value",filtercallback)
    profInput.js_on_change("value",filtercallback)
    nameInput.js_on_change("value",filtercallback)
    DOWInput.js_on_change("value",filtercallback)
    timeslider.js_on_change("value_throttled",filtercallback)

    #Create layout and show it
    tableTab = mo.TabPanel(child=table, title="All Classes")
    ftableTab = mo.TabPanel(child=ftable, title="Filtered Classes")
    #tablecol = mo.Column(timebox,mo.Tabs(tabs =[ftableTab,tableTab]))
    
    #lay = layout([[inputcol,tablecol]])
    return bldgbox,roombox,DOWbox,namebox,profbox,timebox,[ftableTab,tableTab]

def createRoomsUnusedGaant(seproomtimes,bldgbox,roombox,DOWbox,timebox):
    #Create change times to pandas applicable times
    BOXHEIGHTDICT = {"F":[0.1,0.24],"H":[0.26,0.40],"W":[0.42,0.56],"T":[0.58,0.72],"M":[0.74,0.9]}
    sourcestart = []
    sourceend = []
    sourcestartmil = []
    sourceendmil = []
    sourceduration = []
    sourceroom = [room[:len(room)-2] for room,times in seproomtimes.items() for interval in times]
    uniquerooms = sorted(list(set(sourceroom)))
    sourcebottom = []
    sourcetop = []
    sourceDOW = []
    sourceBLDG = []
    sourceRoomNum = []

    for i,vals in enumerate(seproomtimes.items()):
        room = vals[0]
        times = vals[1]
        newtimes = []
        for interval in times:
            splitroom = room.split(":")
            newtime = pd.to_datetime(mintomil(interval[0],":"))
            newdelta = pd.to_timedelta(interval[1],'m')
            newtimes.append([newtime,newdelta])
            #Put into datasource array
            sourcestart.append(newtime)
            sourceend.append(newtime+newdelta)
            sourcestartmil.append(mintomil(interval[0]))
            sourceendmil.append(mintomil(interval[0] + interval[1]))
            sourceduration.append(interval[1])
            sourceBLDG.append(splitroom[0])
            sourceRoomNum.append(splitroom[1])
            sourceDOW.append(splitroom[2])
            sourcebottom.append(BOXHEIGHTDICT[splitroom[2]][0] + uniquerooms.index(room[:len(room)-2]))
            sourcetop.append(BOXHEIGHTDICT[splitroom[2]][1] + uniquerooms.index(room[:len(room)-2]))

        seproomtimes[room] = newtimes

    #Create datasource
    sourcedict = {
        "start":sourcestart,
        "end":sourceend,
        "startmil":sourcestartmil,
        "endmil":sourceendmil,
        "duration":sourceduration,
        "room":sourceroom,
        "DOW":sourceDOW,
        "bldg":sourceBLDG,
        "roomNum":sourceRoomNum,
        "bottom":sourcebottom,
        "top":sourcetop
        }
    datasource = mo.ColumnDataSource(data = sourcedict)
    fdatasource = mo.ColumnDataSource(data = sourcedict)

    #Make the table
    columns = [
            mo.TableColumn(field = "bldg",title = "Building"),
            mo.TableColumn(field = "roomNum",title = "Room"),
            mo.TableColumn(field = "duration",title = "Availability remaining (mins)"),
            mo.TableColumn(field = "startmil",title = "Becomes availible at:"),
            mo.TableColumn(field = "endmil",title = "Becomes closed at:"),
            mo.TableColumn(field = "DOW",title = "Weekday")
    ]
    roomTable = mo.DataTable(source = fdatasource, columns = columns, resizable = "both",height = 600,width = 1200)

    #Make the duration bo
    durationtitle = mo.Div(text = r'<p style="font-size:14px"><b>Minimum Minutes Available</b></p>')
    durationinput = mo.NumericInput(value = 0,width = 200)
    durationbox = mo.Column(durationtitle,durationinput)

    #Make the Gannt chart
    roomChart = figure(x_axis_type='datetime', x_range = (pd.to_datetime("06:00"),pd.to_datetime("23:59")), 
           y_range = uniquerooms,height = 600,width = 1200,
           tools = "pan,wheel_zoom,box_zoom")
           
    #Defaults
    roomChart.toolbar.active_drag = None
    roomChart.xaxis.bounds = pd.to_datetime("00:01"),pd.to_datetime("23:59")

    roomChart.xaxis[0].ticker.desired_num_ticks = 24 #Only 24hr ticks
    #Create the actual blue bars
    roomChart.quad(left='start',right='end',bottom = "bottom", top = "top", source=datasource)
    bldginput = bldgbox.children[1]
    roominput = roombox.children[1]
    DOWinput = DOWbox.children[1]
    timeslider = timebox.children[1].children[1]
    #TODO: create a "Excluded bldg:room" list
    callback = mo.CustomJS(args = {"source":datasource,"fsource":fdatasource,"roomchart":roomChart,
                                   "axisbounds":roomChart.xaxis.bounds,"bldgbox":bldginput,"roombox":roominput,
                                    "DOWbox":DOWinput,"timeslider":timeslider,"durationbox":durationinput},code = r"""
                            function cmpInput(cmpstr,sourcestr){
                                let boolval = true
                                if (sourcestr === null){
                                    boolval = true
                                }
                                else{
                                    boolval = sourcestr.toLowerCase().includes(cmpstr.toLowerCase());
                                }
                                return boolval
                            }

                            const data = source.data;
                            let fdata = Object.assign({},source.data);
                            const bldgs = bldgbox.value;
                            const room = roombox.value;
                            const DOW = DOWbox.value;
                            let duration = durationbox.value;
                            const timestart = timeslider.value[0];
                            const timeend = timeslider.value[1];
                            const hour0 = axisbounds[0] - 60000;
                            const hour24 = axisbounds[0] + 60000;

                            //filter the graph
                            // store the good indexes here
                            let findexes = [];
                            for(let i = 0; i < data.start.length; i++){
                                //Test if bldg is good
                                let bldgbool = ((bldgs.indexOf(data.bldg[i]) > -1) || (bldgs.indexOf("All") > -1));

                                //Test if room is good
                                let roombool = cmpInput(room,data.roomNum[i]);   

                                //Test if DOW is good
                                let CleanDOW = DOW.toLowerCase().replace("th","h");
                                if (CleanDOW == "") {CleanDOW = "MTWThF"}
                                let DOWbool = cmpInput(data.DOW[i],CleanDOW);
                                
                                //Test is duration is good
                                if (duration === null){
                                    duration = 0;
                                    durationbox.value = 0;
                                }
                                let durationbool = (data.duration[i] >= duration);
                                
                                //Test if time is good
                                    //start time
                                let startmilstr = data.startmil[i].toString();
                                let sourcestarthour = startmilstr.slice(0,2);
                                let sourcestartmin = startmilstr.slice(2,4);
                                const sourcestarttime = parseInt(sourcestarthour)*60 + parseInt(sourcestartmin);
                                const cmpstarttime = timestart;

                                    //end time
                                let endmilstr = data.endmil[i].toString();
                                let sourceendhour = endmilstr.slice(0,2);
                                let sourceendmin = endmilstr.slice(2,4);
                                const sourceendtime = parseInt(sourceendhour)*60 + parseInt(sourceendmin);
                                const cmpendtime = timeend;

                                //Not a carbon copy of the other time test because we 
                                // ensure the duration within is satisfied aswell   
                                const startinbool = (cmpstarttime <= sourceendtime && cmpstarttime >= sourcestarttime && (sourceendtime - cmpstarttime >= duration));
                                const endinbool = (cmpendtime <= sourceendtime && cmpendtime >= sourcestarttime && (cmpendtime - sourcestarttime >= duration));
                                const containsbool = (cmpendtime > sourceendtime && cmpstarttime < sourcestarttime);
                                const timebool = (startinbool || endinbool || containsbool);

                                // Combine tests
                                if ((bldgbool && roombool && DOWbool && durationbool && timebool)){
                                    findexes.push(i);
                                } 
                            }
                            
                            fdata.start = Array.from(findexes,(i) => data.start[i]);
                            fdata.end = Array.from(findexes,(i) => data.end[i]);
                            fdata.room = Array.from(findexes,(i) => data.room[i]);
                            fdata.startmil = Array.from(findexes,(i) => data.startmil[i]);
                            fdata.endmil = Array.from(findexes,(i) => data.endmil[i]);
                            fdata.duration = Array.from(findexes,(i) => timestart > ((data.start[i]-hour0)/60000) ? ((data.end[i]-hour0)/60000) - timestart : data.duration[i]);
                            fdata.DOW = Array.from(findexes,(i) => data.DOW[i]);
                            fdata.bldg = Array.from(findexes,(i) => data.bldg[i]);
                            fdata.roomNum = Array.from(findexes,(i) => data.roomNum[i]);
                            //Recalculate
                            const uniqueRooms = Array.from(new Set(fdata.room), (x) => x).sort();
                            const DOWbounds = {"F":[0.1,0.24],"H":[0.26,0.40],"W":[0.42,0.56],"T":[0.58,0.72],"M":[0.74,0.9]}
                            data.bottom = Array.from(data.room,(val,i) => (findexes.indexOf(i) > -1) ? DOWbounds[data.DOW[i]][0] + uniqueRooms.indexOf(data.room[i]) : 0);
                            data.top = Array.from(data.room,(val,i) => (findexes.indexOf(i) > -1) ? DOWbounds[data.DOW[i]][1] + uniqueRooms.indexOf(data.room[i]) : 0);
                            fdata.bottom = data.top;
                            fdata.top = data.top;
                            fsource.data = fdata;
                            source.data = data;
                            
                            console.log("Room times data")
                            console.log(fdata)
                            console.log(data)
                            
                            //Change xRange
                            roomchart.x_range["start"] = hour0 + 60000*timestart;
                            roomchart.x_range["end"] = hour0 + 60000*timeend;
                            roomchart.y_range.factors = uniqueRooms;
                            

""")
    bldginput.js_on_change("value",callback)
    roominput.js_on_change("value",callback)
    DOWinput.js_on_change("value",callback)
    timeslider.js_on_change("value_throttled",callback)
    durationinput.js_on_change("value",callback)

    roomChartTab = mo.TabPanel(child=roomChart, title="Availability Chart")
    roomTableTab = mo.TabPanel(child=roomTable, title="Availability Table")
    return roomChartTab, roomTableTab, durationbox

    
def createHTML(inputcol,timebox,tabslist):
    col2 = mo.Column(timebox,mo.Tabs(tabs = tabslist))
    row1 = mo.Row(inputcol,col2)
    lay = layout(row1)
    show(lay)

if __name__ == "__main__":
    infile = open(INPATH,"r")
    
    allData = np.array(infile.read().split("\n"))
    onCampusClasses = removeOnlineCourses(allData)
    onCampusClasses.pop()
    courselist = []
    for course in onCampusClasses:
        courselist.append(unpackline(course,DATANAMES,DATANAMES2))
    sepdata = separateData(courselist)
    roomtTimes_Used = findRoomTimes_Used(sepdata)
    roomTimes_Unused = findRoomTimes_Unused(sepdata)
    seproomtimes_unused = separateroomTimes(roomTimes_Unused)

    bldgbox,roombox,DOWbox,namebox,profbox,timebox,tablist = createFilteredTables(sepdata) 
    seproomcharttab,seproomtabletab,durationbox = createRoomsUnusedGaant(seproomtimes_unused,bldgbox,roombox,DOWbox,timebox)
    tablist.insert(0,seproomcharttab)
    tablist.insert(0,seproomtabletab)
    inputcol = mo.Column(bldgbox,roombox,DOWbox,namebox,profbox,durationbox)
    createHTML(inputcol,timebox,tablist)


    print("Finished")