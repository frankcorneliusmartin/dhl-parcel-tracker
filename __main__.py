import datetime
import json
import time
import urllib.request
import webbrowser

from enum import Enum
from infi.systray import SysTrayIcon
from win10toast import ToastNotifier


code = "JVGL05238746303729119811"
url = f'https://track-and-trace.dhlparcel.nl/graphql?query=query%20TrackAndTrace($trackingCode:String!$postcode:String$locale:String$role:RoleVariant$environment:EnvironmentVariant$timeTravelOffset:Int$overrideIntervenable:Boolean)%7BtrackAndTrace(trackingCode:$trackingCode%20postcode:$postcode%20locale:$locale%20role:$role%20environment:$environment%20timeTravelOffset:$timeTravelOffset%20overrideIntervenable:$overrideIntervenable)%7BqueryVariant%20barcode%20shipmentVariant%20pointInTimeVariant%20pointInTime%20pointInTimeInterval%7Bfrom%20to%7DinitialDestination%7B__typename%20address%7Bstreet%20houseNumber%20addition%20postalCode%20city%20countryCode%20lines%7Dcode%20name%20locationVariant%7DlastKnownDestination%7B__typename%20address%7Bstreet%20houseNumber%20addition%20postalCode%20city%20countryCode%20lines%7Dcode%20name%20locationVariant%7Dshipper%7B__typename%20address%7Bstreet%20houseNumber%20addition%20postalCode%20city%20countryCode%20lines%7DcontactName%20name%20terminalCode%7Dreceiver%7B__typename%20address%7Bstreet%20houseNumber%20addition%20postalCode%20city%20countryCode%20lines%7DcontactName%20name%7Dsignature%20signedBy%20intervenable%20servicePoint%7BservicePointId%20name%20address%7Bstreet%20houseNumber%20addition%20postalCode%20city%20countryCode%7DgeoLocation%7Blatitude%20longitude%7DopeningTimes%7Bfrom%20to%20dayOfWeek%7DclosurePeriods%7Bfrom%20to%7D%7Dtimeline%7Bstage%20translatedStage%20completed%20exception%7Devents%7Bstage%20translatedStage%20events%7Bevent%20translatedEvent%20timestamp%20exception%20note%7D%7DeventsTotal%20showAsReturn%20expectedMailboxDelivery%7D%7D&variables=%7B%22trackingCode%22:%22{code}%22,%22postcode%22:%22%22,%22locale%22:%22nl-NL%22,%22role%22:%22receiver%22%7D'

toaster = ToastNotifier()
toaster.show_toast("Watching your package",
                   f"Notifications will be posted",
                   icon_path= "1" + ".ico",
                   duration=3)

def open_webpage(systray):
    url2 = f"https://www.dhlparcel.nl/nl/consument/volg-je-pakket?tc={code}&lc=nl-NL"
    webbrowser.open_new(url2)

def on_quit(systray):
    global running
    running = False

menu_options = (("Open webpage", None, open_webpage),)
systray = SysTrayIcon("icon.ico", "Starting", menu_options, on_quit=on_quit)
systray.start()


class ParcelState(Enum):
    AANGEMELD = 1
    SORTEREN = 2
    ONDERWEG = 3
    BEZORGT = 4

state = ParcelState.AANGEMELD
try:
    running = True
    while running:

        # keep track of the previous state. If the state changes we throw
        # a notification
        old_state = state

        # initial icon
        icon = f"{state.value}.ico"

        # retrieve parcel state
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        # PHL timeline, contains the four states with a complete section
        tat = data.get("data").get("trackAndTrace")
        stages = tat.get("timeline")

        # search for the higsest completed stage and set the state
        for idx, stage in enumerate(stages):
            # print(stage)
            if stage.get("completed"):
                state = ParcelState(idx+1)

        # in case the state has changed, notify the user and update the
        # tray-icon
        # print(state)
        # print(old_state)
        if state != old_state:
            # print(state)
            icon = f"{state.value}.ico"
            toaster.show_toast("Update from your parcel!", \
                f"New state: {stage}", icon_path=icon, duration=10)
            systray.update(icon=icon)

        # update tray tooltip
        interval = tat.get("pointInTimeInterval")
        parse = lambda t: datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
        try:
            from_ = parse(interval.get("from"))
            to_ = parse(interval.get("to"))
            systray.update(hover_text=\
                f"{from_.strftime('%H:%M')}-{to_.strftime('%H:%M (%d/%m)')}")
        except Exception:
            systray.update(hover_text=f"Tijdsvlak niet beschikbaar")

        # wait 10 second not to overflow the server with requests.
        time.sleep(10)

except KeyboardInterrupt:
    print('interrupted!')
