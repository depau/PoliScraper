# -*- coding: utf-8 -*-

import datetime, icalendar, re, uuid, warnings
from bs4 import BeautifulSoup
#from typing import overload

date2ssepoch = lambda date: int(datetime.date(*reversed([int(i) for i in date.strip().split("/")])).strftime("%s"))
time2sec = lambda time: int(time.split(":")[0])*60*60 + int(time.split(":")[1])*60

def datetime2ical(date, time=0):
    d = datetime.datetime.fromtimestamp(date+time)
    d.hour, d.minute = [int(i) for i in time.split(":")]
    return d.strftime("TZID=Europe-Rome:%Y%m%dT%H%M00")

teacher_re = re.compile(r"<b>\s*(?P<id>\d+)\s+-\s+(?P<name>[\w\s\\'.,;]+)\s*</b>(?:\s*[(]\s*<b>\s*(?:Docente)|(?:Professor)\s*:\s*</b>\s*(?P<teacher>[\w ]+)\s*[)])?", flags=re.M|re.I|re.U)
ltime_re = re.compile(r"(?P<day>[\wàèéìòù]+)\s+dalle\s+(?P<start>\d+:\d+)\s+alle\s+(?P<end>\d+:\d+),\s+(?P<lesson>\w+)", flags=re.M|re.I|re.U)
lang_re = re.compile(r'var\s+jaf_js_LANG\s+=\s+[\'"](\w+)[\'"]\s*;', flags=re.U)
roomurl_re = re.compile(r"id_?aula=(\d+)", flags=re.U)

lesson_str = {"EN": u"lesson", "IT": u"lezione"}
training_str = {"EN": u"training", "IT": u"esercitazione"}
room_str = {"EN": "room", "IT": "aula"}
lesson_details_str = {
    "EN": u"Teacher: {teacher}\nRoom: {room}\nRoom info: {room_url}\nAddress: {address}\nSemester: {semester}\nCourse ID: {id}\nCourse description: {url}",
    "IT": u"Docente: {teacher}\nAula: {room}\nInfo aula: {room_url}\nIndirizzo: {address}\nSemestre: {semester}\nID corso: {id}\nDescrizione corso: {url}"}
ceda_room_url = u"https://www7.ceda.polimi.it/spazi/spazi/controller/Aula.do?evn_init=event&idaula={0}"
ceda_course_url = u"https://www4.ceda.polimi.it/manifesti/manifesti/controller/ricerche/RicercaPerInsegnamentoPublic.do?insegn_ricerca={id}&lang={lang}"

weekdays = {u"mon": 0,
            u"tue": 1,
            u"wed": 2,
            u"thu": 3,
            u"fri": 4,
            u"sat": 5,
            u"sun": 6,
            u"lun": 0,
            u"mar": 1,
            u"mer": 2,
            u"gio": 3,
            u"ven": 4,
            u"sab": 5,
            u"dom": 6}

get_weekday = lambda day: weekdays[day.lower()[:3]]

def contains_timetable(html):
    soup = BeautifulSoup(html, 'html.parser')
    o = soup.find("div", id="orarioTestuale")
    if o:
        return True
    else:
        if soup.find("div", id="orarioSinottico"):
            return "synoptic"
        else:
            return None

def purge_wsp(string):
    s = re.sub(r'\s{3,}', "", string, flags=re.M|re.U)
    return re.sub(r'\s{2,}', " ", string, flags=re.M|re.U)

def parse_timetable(html, print_divs=False, print_html=False, print_regex=False):
    soup = BeautifulSoup(html, 'html.parser')

    if print_html: print soup.prettify()

    o = soup.find("div", id="orarioTestuale")
    if not o or len(o) == 0:
        if soup.find("div", id="orarioSinottico"):
            raise NotTextualError("Provided timetable is synoptic; please use the textual timetable")
        raise NotTimetableError("Provided web page does not contain a valid timetable")

    lang = "IT"
    match = lang_re.search(unicode(soup))
    if print_regex: print match, match and match.groups() or ""
    if match:
        lang = match.group(1)

    courses = []

    for div in o.find_all("div"):
        if print_divs: print purge_wsp(unicode(div))
        match = teacher_re.search(purge_wsp(unicode(div)))
        if print_regex: print match, match and match.groupdict() or ""
        if not match:
            continue

        course = {"id": match.group("id"),
                  "name": match.group("name"),
                  "teacher": match.group("teacher") and match.group("teacher") or "Unknown/Multiple",
                  "url": ceda_course_url.format(id=match.group("id"), lang=lang)}
        # print (course)
        n = div.next_sibling
        try:
            while n and "Docente" not in unicode(n) and "Professor" not in unicode(n):
                if "Semestre" in unicode(n) or "Semester" in unicode(n):
                    course["semester"] = int(unicode(n.next_sibling).strip())
                    n = n.next_sibling
                elif "Inizio lezioni" in unicode(n) or "Start of lessons" in unicode(n):
                    course["start"] = date2ssepoch(unicode(n.next_sibling))
                    n = n.next_sibling
                elif "Fine lezioni" in unicode(n) or "End of lessons" in unicode(n):
                    course["end"] = date2ssepoch(unicode(n.next_sibling))
                    n = n.next_sibling
                elif n.name == "ul":
                    course["schedule"] = _parse_schedule_ul(n, print_divs=print_divs, print_regex=print_regex)
                    n = n.next_sibling
                n = n.next_sibling
        except AttributeError:
            import traceback; traceback.print_exc();
        courses.append(course)

    return courses, lang

def _parse_schedule_ul(ul, print_divs=False, print_regex=False):
    schedule = []
    for li in ul.children:
        nwli = purge_wsp(unicode(li))
        if print_divs: print nwli
        match = ltime_re.search(nwli)
        if print_regex: print (match), match and match.groupdict() or ""
        if not match:
            continue
        lesson = {"dow":    get_weekday(match.group("day")),
                  "start":  time2sec(match.group("start")),
                  "end":    time2sec(match.group("end")),
                  "lesson": True}
        l = match.group("lesson")
        if "training" in l or "esercitazione" in l:
            lesson["lesson"] = False

        a = li.find("a")
        aunica_roomurl = a.get("href")
        rmatch = roomurl_re.search(aunica_roomurl)
        lesson["room_url"] = rmatch and ceda_room_url.format(rmatch.group(1)) or "  "
        lesson["room"] = purge_wsp(a.get_text())
        lesson["address"] = unicode(a.next_sibling).strip()[1:-1]

        schedule.append(lesson)
    return schedule

def gen_timetable_ical(ttable, lang="IT"):
    cal = icalendar.Calendar()
    cal.add("prodid", "Poli2iCal")

    dtstamp = datetime.datetime.now()

    for course in ttable:
        if "schedule" not in course:
            warnings.warn("Course has no schedule, skipping: {0}".format(course), RuntimeWarning)
            continue
        for lesson in course["schedule"]:
            event = icalendar.Event()

            dtstart = datetime.datetime.fromtimestamp(course["start"] + lesson["start"])
            wddelta = lesson["dow"] - dtstart.weekday()
            if wddelta != 0:
                dtstart = dtstart.replace(day=dtstart.day+wddelta)
            dtend = datetime.datetime.fromtimestamp(course["end"] + lesson["end"])
            duration = datetime.timedelta(seconds=lesson["end"]-lesson["start"])
            uid = unicode(uuid.uuid5(uuid.NAMESPACE_OID, "{}_{}_{}_{}".format(course["id"], course["start"], lesson["dow"], lesson["start"]))) + u"@polimi.it"
            summary = u"{0} ({1})".format(course["name"].title(), lesson_str[lang] if lesson["lesson"] else training_str[lang])
            location = u"{0} {1} - {2}".format(room_str[lang].title(), lesson["room"], lesson["address"])
            contact = course["teacher"]
            t = course.copy()
            t.update(lesson)
            description = lesson_details_str[lang].format(**t)
            url = course["url"]
            rrule = {"freq": "weekly", "until": dtend}

            event.add("summary", summary)
            event.add("dtstart", dtstart)
            event.add("duration", duration)
            event.add("uid", uid)
            event.add("location", location)
            event.add("contact", contact)
            event.add("description", description)
            event.add("url", url)
            event.add("rrule", rrule)

            cal.add_component(event)

    return cal.to_ical()

class NotTimetableError(ValueError):
    pass

class NotTextualError(ValueError):
    pass