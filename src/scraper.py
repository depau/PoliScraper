#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__version__ = "0.1"
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib, WebKit, Soup
import webpoliscraper as wps
import os, sys, datetime

APP = "PoliMi Timetable Scraper"
CONFIG_DIR = os.path.expanduser("~/.config/poliscraper")
try:
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)
    else:
        if not os.path.isdir(CONFIG_DIR):
            CONFIG_DIR = None
except Exception:
    CONFIG_DIR = None

TTABLE_URI = "https://servizionline.polimi.it/portaleservizi/portaleservizi/controller/servizi/Servizi.do?evn_srv=evento&idServizio=398"
SCRAPE_TTIP = "Navigate to the textual timetable in order to scrape it."
SCRAPE_SYN_TTIP = "The synoptic timetable cannot be scraped. Please use the textual one."
SCRAPE_TXT_TTIP = "Scrape the current timetable"

MENU_XML = """<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
      <item>
        <attribute name="action">app.about</attribute>
        <attribute name="label" translatable="yes">_About</attribute>
      </item>
      <item>
        <attribute name="action">app.quit</attribute>
        <attribute name="label" translatable="yes">_Quit</attribute>
        <attribute name="accel">&lt;Primary&gt;q</attribute>
    </item>
    </section>
  </menu>
</interface>
"""

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, start_url=TTABLE_URI, print_divs=False, print_html=False, print_regex=False, print_ttable=False, *a, **kw):
        super(MainWindow, self).__init__(*a, **kw)

        self.start_url = start_url
        self.print_divs = print_divs
        self.print_html = print_html
        self.print_regex = print_regex
        self.start_url = start_url
        self.print_ttable = print_ttable

        self.r = Gtk.Builder()
        self.r.add_from_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), "scraper.ui"))
        self.r.connect_signals(self)

        cookiejar = self.get_cookiejar()
        if cookiejar:
            session = WebKit.get_default_session()
            session.add_feature(cookiejar)

        self.webview = WebKit.WebView()

        scrolledwindow = Gtk.ScrolledWindow()
        self.add(scrolledwindow) #self.r.get_object("scrolledwindow")
        scrolledwindow.add(self.webview)

        self.webview.connect("title-changed", self.on_title_changed)
        self.webview.connect("load-started", self.on_load_started)
        self.webview.connect("load-finished", self.on_load_finished)
        #self.webview.connect("icon-loaded", self.on_icon_loaded)
        self.ui_home()

        self.scrape_btn = self.r.get_object("scrape_button")
        self.scrape_btn.set_tooltip_text(SCRAPE_TTIP)
        self.r.get_object("warningicon").hide()

        self.hbar = self.r.get_object("headerbar")
        self.hbar.pack_start(self.scrape_btn)
        # self.hbar.pack_end(self.r.get_object("about_button"))
        self.hbar.pack_end(self.r.get_object("home_button"))
        self.hbar.pack_end(self.r.get_object("refresh_button"))
        self.hbar.pack_end(self.r.get_object("goto_button"))

        self.popover = Gtk.Popover()
        self.popover.set_position(Gtk.PositionType.TOP)
        self.popover.set_relative_to(self.r.get_object("goto_button"))

        pvbox = Gtk.Box()
        pvbox.set_orientation(Gtk.Orientation.VERTICAL)
        pvbox.add(Gtk.Label("Go to address"))
        pbox = Gtk.Box()
        pvbox.add(pbox)
        pbox.set_spacing(5)
        pvbox.set_property("margin", 10)
        pbox.set_orientation(Gtk.Orientation.HORIZONTAL)
        pbox.set_spacing(5)
        self.goto_entry = Gtk.Entry()
        self.goto_entry.set_input_purpose(Gtk.InputPurpose.URL)
        self.goto_entry.set_property("shadow_type", Gtk.ShadowType.NONE)
        self.goto_entry.set_width_chars(50)
        self.goto_entry.connect("activate", self.ui_do_goto)
        pbox.add(self.goto_entry)
        pbox.add(self.r.get_object("do_goto_button"))
        self.popover.add(pvbox)


        # self.win = self.r.get_object("window")
        # self.win.set_decorated(False)
        self.set_titlebar(self.hbar)
        self.set_default_size(1000, 600)
        # self.maximize()
        self.set_gravity(Gdk.Gravity.CENTER)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.show_all()

    def get_cookiejar(self):
        if not CONFIG_DIR:
            return
        try:
            cookiejar = Soup.CookieJarDB.new(os.path.join(CONFIG_DIR, "cookies.sqlite"), False)
            cookiejar.set_accept_policy(Soup.CookieJarAcceptPolicy.NO_THIRD_PARTY)
            return cookiejar
        except Exception:
            return

    def on_title_changed(self, webview, frame, title):
        self.hbar.set_subtitle(title)

    def ui_home(self, *a, **kw):
        self.webview.load_uri(self.start_url)

    def ui_goto(self, *a, **kw):
        self.popover.show_all()

    def ui_do_goto(self, *a, **kw):
        self.webview.load_uri(self.goto_entry.get_text())
        self.popover.hide()

    def ui_refresh(self, *a, **kw):
        self.webview.reload()

    def ui_scrape(self, *a, **kw):
        try:
            reload(wps)
            ttable, lang = wps.parse_timetable(self.get_page_source(), print_divs=self.print_divs,
                                               print_regex=self.print_regex, print_html=self.print_html)
            if self.print_ttable: print ttable
            ical = wps.gen_timetable_ical(ttable, lang)

            dialog = Gtk.FileChooserDialog("Save generated calendar as...", self, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
            now = datetime.datetime.now()
            dialog.set_current_name(now.strftime("Timetable %Y-%m-%d.ics"))
            dialog.set_do_overwrite_confirmation(True)
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                with open(dialog.get_filename(), "w") as f:
                    f.write(ical)
            dialog.destroy()
        except Exception:
            import traceback
            exc = traceback.format_exc()
            print >> sys.stderr, exc
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, "Unable to scrape the timetable")
            dialog.format_secondary_text(exc)
            dialog.run()
            dialog.destroy()
            return

    def on_load_started(self, webview, frame):
        try:
            self.scrape_btn.set_sensitive(False)
        except AttributeError:
            pass

    def get_page_source(self):
        src = self.webview.get_main_frame().get_data_source().get_data().str
        print "Encoding:", self.webview.get_main_frame().get_data_source().get_encoding()
        return unicode(src, self.webview.get_main_frame().get_data_source().get_encoding(), errors="replace")

    def on_load_finished(self, webview, frame):
        self.goto_entry.set_text(self.webview.get_uri())
        ttt = wps.contains_timetable(self.get_page_source())
        if ttt == "synoptic":
            self.scrape_btn.set_tooltip_text(SCRAPE_SYN_TTIP)
            self.r.get_object("warningicon").show()
        else:
            self.r.get_object("warningicon").hide()
            if ttt == True:
                self.scrape_btn.set_sensitive(True)
                self.scrape_btn.set_tooltip_text(SCRAPE_TXT_TTIP)
            else:
                self.scrape_btn.set_tooltip_text(SCRAPE_TTIP)


        # self.frame = self.webview.get_main_frame().get_data_source().get_data().str

    # def on_icon_loaded(self, webview, url):
    #     try:
    #         f = urllib.urlopen(url)
    #         data = f.read()
    #         pixbuf_loader = GdkPixbuf.PixbufLoader()
    #         pixbuf_loader.write(data)
    #         pixbuf_loader.close()
    #         pixbuf = pixbuf_loader.get_pixbuf()
    #         self.url.set_icon_from_pixbuf(Gtk.EntryIconPosition.PRIMARY, pixbuf)
    #     except:
    #         self.url.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "browser") #applications-internet


    def destroy(self, window):
        Gtk.main_quit()
        sys.exit(0)


class Application(Gtk.Application):
    print_html = False
    print_regex = False
    print_ttable = False
    print_divs = False
    start_url = TTABLE_URI

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, application_id="org.depaulicious.poliscraper", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs)
        self.window = None
        self.add_main_option("debug-divs", ord("d"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Print all relevant \"div\" tags found in the page source", None)
        self.add_main_option("debug-regex", ord("r"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Print debug info for regular expressions", None)
        self.add_main_option("debug-html", ord("m"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Dump the whole page source to stdout", None)
        self.add_main_option("debug-timetable", ord("t"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Dump the raw timetable to stdout", None)
        self.add_main_option("start-url", ord("s"), GLib.OptionFlags.NONE, GLib.OptionArg.FILENAME, "Use URL as the built-in browser start page", "URL")

    def do_startup(self):
        GLib.set_application_name("PoliMi Timetable Scraper")
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        builder = Gtk.Builder.new_from_string(MENU_XML, -1)
        self.set_app_menu(builder.get_object("app-menu"))

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = MainWindow(application=self, title="PoliMi Timetable Scraper",
                                     print_divs=self.print_divs, print_regex=self.print_regex,
                                     print_html=self.print_html, start_url=self.start_url,
                                     print_ttable=self.print_ttable)
        self.window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()

        if options.contains("debug-divs"):
            self.print_divs = True
        if options.contains("debug-regex"):
            self.print_regex = True
        if options.contains("debug-html"):
            self.print_html = True
        if options.contains("debug-timetable"):
            self.print_ttable = True
        if options.contains("start-url"):
            url_variant = options.lookup_value("start-url", GLib.VariantType.new("*"))
            self.start_url = url_variant.get_bytestring()
            if not self.start_url:
                self.start_url = TTABLE_URI

        self.activate()
        return 0

    def on_about(self, action, param):
        aboutdialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        # lists of authors and documenters (will be used later)
        authors = ["Davide Depau"]
        # documenters = ["GNOME Documentation Team"]

        # we fill in the aboutdialog
        aboutdialog.set_program_name("PoliMi Timetable Scraper")
        aboutdialog.set_copyright(
            "Copyright \xc2\xa9 2016 Davide Depau")
        aboutdialog.set_authors(authors)
        # aboutdialog.set_documenters(documenters)
        aboutdialog.set_website("http://davideddu.org")
        aboutdialog.set_website_label("Davide Depau's Website")
        aboutdialog.set_license_type(Gtk.License.GPL_3_0)
	aboutdialog.set_comments("Scrapes the timetable from PoliMi online services and converts it to well-known iCal format")

        # we do not want to show the title, which by default would be "About AboutDialog Example"
        # we have to reset the title of the messagedialog window after setting
        # the program name
        aboutdialog.set_title("")
        aboutdialog.run()
        aboutdialog.destroy()

    def on_quit(self, action, param):
        self.quit()

if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)


# def main():
#     app = Browser()
#     Gtk.main()


# if __name__ == "__main__":
#     main()


