# A simple and slightly stupid script that gets the SolarEdge optimizer
# data from the SolarEdge website and sends email if there are problems.
from datetime import datetime, timedelta
from dateutil import tz

from solaredgeoptimizers import solaredgeoptimizers

import smtplib, ssl
from email.message import EmailMessage

# FIXME: Get .const to work here.
from const import (
    SOLAREDGE_SITEID,
    SOLAREDGE_USERNAME,
    SOLAREDGE_PASSWORD,
    MAIL_RECIPIENT,
    MAIL_SENDER,
    MAIL_PASSWORD,
    SMTP_HOST,
)

import const

def solaredge_power(starttime, endtime):

    solaredge = solaredgeoptimizers(
        SOLAREDGE_SITEID, SOLAREDGE_USERNAME, SOLAREDGE_PASSWORD
    )

    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()

    #print("solaredge.check_login()", solaredge.check_login())

    #all_panels=solaredge.requestListOfAllPanels()
    # print("All Panels: ", all_panels.__dir__())
    # ['siteId', 'inverters', '__module__', '__init__', '_SolarEdgeSite__GetAllInverters', 'returnNumberOfOptimizers', 'ReturnAllPanelsIds', '__dict__', '__weakref__', '__doc__', '__new__', '__repr__', '__hash__', '__str__', '__getattribute__', '__setattr__', '__delattr__', '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__', '__reduce_ex__', '__reduce__', '__subclasshook__', '__init_subclass__', '__format__', '__sizeof__', '__dir__', '__class__']

    #logical_layout = solaredge.requestLogicalLayout()
    #print("logical_layout:", logical_layout, logical_layout.__dir__())

    #panels = solaredge.requestListOfAllPanels()
    #print("panels:", panels, panels.__dir__())
    #panels: <solaredgeoptimizers.SolarEdgeSite object at 0x10ecbf8b0> ['siteId', 'inverters', '__module__', '__init__', '_SolarEdgeSite__GetAllInverters', 'returnNumberOfOptimizers', 'ReturnAllPanelsIds', '__dict__', '__weakref__', '__doc__', '__new__', '__repr__', '__hash__', '__str__', '__getattribute__', '__setattr__', '__delattr__', '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__', '__reduce_ex__', '__reduce__', '__subclasshook__', '__init_subclass__', '__format__', '__sizeof__', '__dir__', '__class__']


    data=solaredge.requestAllData()

    #print("data: ", data.__dir__())
    # ['serialnumber', 'paneel_id', 'paneel_desciption', 'lastmeasurement', 'model', 'manufacturer', 'current', 'optimizer_voltage', 'power', 'voltage', 'lifetime_energy', '_json_obj', '__module__', '__doc__', '__init__', '__dict__', '__weakref__', '__new__', '__repr__', '__hash__', '__str__', '__getattribute__', '__setattr__', '__delattr__', '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__', '__reduce_ex__', '__reduce__', '__subclasshook__', '__init_subclass__', '__format__', '__sizeof__', '__dir__', '__class__']



    message = ""
    output = ""
    panels = []
    panels_seen = []
    for optimizer in data:
        #print("optimizer.paneel_id:", optimizer.paneel_id)
        #optimizer.paneel_id: 189955290
        #print("optimizer.paneel_desciption:", optimizer.paneel_desciption)
        #optimizer.paneel_desciption: Panel 1.1.1

        #system_data = solaredge.requestSystemData(optimizer.paneel_id)
        #print("system_data:", system_data, system_data.__dir__())
        #system_data: <solaredgeoptimizers.SolarEdgeOptimizerData object at 0x104b71720> ['serialnumber', 'paneel_id', 'paneel_desciption', 'lastmeasurement', 'model', 'manufacturer', 'current', 'optimizer_voltage', 'power', 'voltage', 'lifetime_energy', '_json_obj', '__module__', '__doc__', '__init__', '__dict__', '__weakref__', '__new__', '__repr__', '__hash__', '__str__', '__getattribute__', '__setattr__', '__delattr__', '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__', '__reduce_ex__', '__reduce__', '__subclasshook__', '__init_subclass__', '__format__', '__sizeof__', '__dir__', '__class__']



        history = solaredge.requestItemHistory(optimizer.paneel_id, starttime, endtime)
        #print(" history: ", history.__dir__())
        #history:  ['__new__', '__repr__', '__hash__', '__getattribute__', '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__', '__iter__', '__init__', '__or__', '__ror__', '__ior__', '__len__', '__getitem__', '__setitem__', '__delitem__', '__contains__', '__sizeof__', 'get', 'setdefault', 'pop', 'popitem', 'keys', 'items', 'values', 'update', 'fromkeys', 'clear', 'copy', '__reversed__', '__class_getitem__', '__doc__', '__str__', '__setattr__', '__delattr__', '__reduce_ex__', '__reduce__', '__subclasshook__', '__init_subclass__', '__format__', '__dir__', '__class__']
        #print("history: ", history)
        #print("history.values: ", history.values())
        #print("history.keys: ", history.keys())


        # Calculate the daytime average
        daytime_sum = 0
        daytime_count = 0
        # Why is desciption misspelled.
        panel_id = optimizer.paneel_desciption
        panels_seen.append(panel_id)
        for key, value in history.items():
            # Convert to local time
            localtime = key.astimezone(to_zone)
            timestr = localtime.strftime("%d. %B %Y %I:%M%p %z")
            hour = localtime.hour
            # If sun should be out, then find the average
            if hour >= 9 and hour <= 17:
                daytime_sum += value
                daytime_count += 1

            output_line = "%s, %f, %d, %s\n" %(panel_id, value, datetime.timestamp(key), timestr)
            #print(output_line)
            output += output_line

        # If we have a low average, then save that info.
        if (daytime_count > 0):
            daytime_average = daytime_sum/daytime_count
            if daytime_average < 100:
                message += "%s average is %f, which is low.\n" % (panel_id, daytime_average)

                
    # If panels.txt does not exist, then create it.
    if panels.len() == 0:
        print("panels.txt not found, generating it now")
        with open("panels.txt", "r") as fp:
            fp.write('\n'.join(panels))
    else:
        for panel in panels:
            if not panel in panels.seen:
                message += "panel %s not seen in the data?" % (panel)
                
    
    # If any of the panels had low day time averages, then send email.
    if message != "":
        print(message)

        msg = EmailMessage()
        msg.set_content(message + "\n" + output)
        msg['Subject'] = "Solar panel(s) output is low?"
        msg['From'] = MAIL_SENDER
        msg['To'] = MAIL_RECIPIENT

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, 465, context=context) as server:
            server.login(MAIL_SENDER, MAIL_PASSWORD)
            server.send_message(msg, from_addr=MAIL_SENDER, to_addrs=MAIL_RECIPIENT)

    return output             

if __name__ == "__main__":
    
    # Get the most data, but just for one day
    starttime=None
    endtime=None

    # Get 5 days of data
    #now = datetime.now()
    #starttime = now - timedelta(days=5)
    #endtime = now

    #starttime = datetime(now.year, now.month, now.day)
    #endtime = int(datetime.timestamp(starttime) + int(timedelta(days=5).total_seconds() * 1000))
    

    print(solaredge_power(starttime, endtime))
    
