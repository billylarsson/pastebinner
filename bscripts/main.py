from PyQt5                     import QtCore, QtGui, QtWidgets
from bscripts.database_stuff   import DB, sqlite
from bscripts.gpg_things       import decrypt_text_message, encrypt_message
from bscripts.gpg_things       import get_activated_gpg_keys, get_all_gpg_keys
from bscripts.gpg_things       import sign_message, verify_signed_data
from bscripts.pastebin_api     import api_communicate, get_credentials
from bscripts.pastebin_api     import store_response
from bscripts.pastewidget      import PasteWidget
from bscripts.preset_colors    import *
from bscripts.settings_widgets import Canvas, DragDroper, GLOBALHighLight
from bscripts.settings_widgets import GODLabel, MovableScrollWidget
from bscripts.settings_widgets import create_indikator
from bscripts.tricks           import tech as t
import os, time
import pathlib
import screeninfo
import shutil
import sys

pos = t.pos
style = t.style

BUTTONHEIGHT = t.config('button_height')

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        if 'dev_mode' in sys.argv: sqlite.dev_mode = True
        self.steady = False
        self.gpg_lock = True
        self.verification = False
        super().__init__()
        self.statusbar = self.statusBar()
        signal = t.signals(name='statusbar')
        signal.smoke.connect(self.status_message)
        self.setWindowTitle(os.environ['PROGRAM_NAME'] + ' ' + os.environ['VERSION'])
        get_credentials() # cache them so future threads can bypass sqlite when getting credentials
        self.show()
        t.start_thread(dummy=True, master_fn=self.post_init)

    def status_message(self, smokesignal):
        self.statusbar.showMessage(smokesignal['string'], smokesignal['timer'])

    def post_init(self):
        self.position_mainwindow()
        self.setup_gui()
        self.create_config_button()
        self.create_refresh_button()
        self.create_searchbar()
        self.create_titlebar()
        self.create_privacy_buttons()
        self.create_time_slider()
        self.create_gpg_settings()
        self.create_url_plate()
        self.create_new_post_delete_update()
        self.create_drag_n_drop_label()
        self.create_extract_to_thingey()
        self.create_decrypt_button()
        self.create_btc_button()
        self.steady = True
        self.resizeEvent(None)
        self.slider_btn.set_saved_slider_position()
        self.draw_my_pastes()
        self.show_active_gpg_keys()
        t.signal_highlight()

    class BTCButton(GODLabel, GLOBALHighLight):
        def show_about(self):
            if self.about:
                self.about.show()
                return

            class About(GODLabel):
                def drag_widget(self, ev):
                    if not self.old_position:
                        self.old_position = ev.globalPos()

                    delta = QtCore.QPoint(ev.globalPos() - self.old_position)
                    self.move(self.x() + delta.x(), self.y() + delta.y())
                    self.old_position = ev.globalPos()

                def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
                    self.drag_widget(ev)

                def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                    if ev.button() == 2:
                        self.parent.activation_toggle(force=False)
                        self.hide()
                        return

                    self.raise_()
                    self.old_position = ev.globalPos()

            self.about = About(place=self.main, qframebox=True, parent=self)
            t.style(self.about, background=GRAY, color=BLACK)
            t.pos(self.about, move=[200,100], size=[440,600])
            self.label = GODLabel(place=self.about, qframebox=True)
            self.label.setWordWrap(True)
            t.pos(self.label, inside=self.about, margin=5)
            t.style(self.label, background=WHITE, color=BLACK)

            text = """This is a program that I desperatley needed therefore I created it. This program has'nt been tried outside of my own system therefore I almost excpect it to not start or instantly crash or glitch and ding dong like a broken ambulance if tried.

I assume that if you want to use the GPG features it will become close impossible to do so if you're not running Linux due to Windows and MAC are'nt really supportive when it comes to strong privacy.

One thing that might not be crystal clear is that in the settings you can drag and drop an image onto the different privacy settings to add them into the program it self."""

            a = 'bc1q0g3qmnercc248qkagmv6pvvvw068fheafqjzg9'

            self.label.setText(text)
            self.label.setAlignment(QtCore.Qt.AlignTop)

            qrimg = t.create_qrcode_image()
            if qrimg and os.path.exists(qrimg):
                pixmap = QtGui.QPixmap(qrimg)
                pixmap_label = GODLabel(place=self.about)
                t.pos(pixmap_label, size=pixmap)
                y = self.about.height() - pixmap.height() - 30
                t.pos(pixmap_label, center=[0, self.about.width()], move=[0, y])
                pixmap_label.setPixmap(pixmap)
                btclabel = GODLabel(place=self.about, center=True)
                btclabel.setText(a)
                btclabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                style(btclabel, color=BLACK)
                t.shrink_label_to_text(btclabel, x_margin=10, y_margin=4)
                t.pos(btclabel, below=pixmap_label, center=[0, self.about.width()], height=btclabel, add=4, y_margin=-5)

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.activation_toggle()
            if self.activated:
                self.show_about()
            elif self.about:
                self.about.hide()

    def create_btc_button(self):
        kwargs = dict(
            place=self,
            main=self,
            deactivated_on=dict(background='rgb(55,55,55)', color=BLACK),
            deactivated_off=dict(background='rgb(30,30,30)', color=BLACK),
            activated_on=dict(background='rgb(55,85,155)', color=BLACK),
            activated_off=dict(background='rgb(30,50,130)', color=BLACK),
            qframebox=True,
            mouse=True,
        )
        self.btc_button = self.BTCButton(**kwargs)
        self.btc_button.about = False

    class ExtractBar(Canvas):
        class Button(Canvas.Button):
            def __init__(self, *args, **kwargs):
                super().__init__(center=True, *args, **kwargs)
                self.activated_on = dict(background=YELLOW, color=BLACK)
                self.activated_off = dict(background=ORANGE, color=BLACK)
                self.deactivated_on = dict(background='rgb(55,55,55)', color=BLACK)
                self.deactivated_off = dict(background='rgb(30,30,30)', color=BLACK)
                self.parent.lineedit.setText(t.config(self.parent.type, curious=True) or "")

            def text_changed(self):
                if '-----BEGIN PGP MESSAGE-----' in self.qtextedit.toPlainText():
                    if not self.activated:
                        self.activation_toggle(force=True)
                        t.signal_highlight()
                else:
                    if self.activated:
                        self.activation_toggle(force=False)
                        t.signal_highlight()

            def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
                t.shrink_label_to_text(self, x_margin=10)

            def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                if not self.activated:
                    t.statusbar("Monkey no glasses")
                    return

                tmpfolder = self.lineedit.text().strip()
                if not tmpfolder:
                    t.statusbar("Monkey need tree to put banan in!")
                    return

                if not os.path.exists(tmpfolder):
                    pathlib.Path(tmpfolder).mkdir(parents=True)

                if not os.path.exists(tmpfolder):
                    t.statusbar("Monkey planted tree, but still no tree to put banan in!")
                    return

                text = self.qtextedit.toPlainText()
                self.decrypt_message_into_file(text, tmpfolder=tmpfolder)
                t.save_config(self.parent.type, tmpfolder)

    def create_extract_to_thingey(self):
        self.extractbar = create_indikator(
            place=self,
            type='extractbar',
            lineedit=True,
            tiplabel='DECRYPT TO FOLDER',
            tipfont=6,
            tipwidth=110,
            button=True,
            button_width=BUTTONHEIGHT * 4,
            mouse=True,
            Special=self.ExtractBar,
        )
        style(self.extractbar.lineedit, background=DARK_BACK, color=TITLE_WHITE, font=8)
        self.extractbar.button.setText('DE-STRACT')
        self.extractbar.setToolTip('Treats the contents as if it was a GPG-encrypted ZIP file and unpacks into ->')
        self.extractbar.button.decrypt_message_into_file = self.decrypt_message_into_file
        self.extractbar.button.qtextedit = self.right.qtextedit
        self.extractbar.button.qtextedit.textChanged.connect(self.extractbar.button.text_changed)

    class DecryptButton(GODLabel, GLOBALHighLight):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.activated_on = dict(background=YELLOW, color=BLACK)
            self.activated_off = dict(background=ORANGE, color=BLACK)
            self.deactivated_on = dict(background='rgb(55,55,55)', color=BLACK)
            self.deactivated_off = dict(background='rgb(30,30,30)', color=BLACK)
            self.setText('DECRYPT')

        def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
            t.shrink_label_to_text(self, x_margin=10)

        def text_changed(self):
            if '-----BEGIN PGP MESSAGE-----' in self.qtextedit.toPlainText():
                if not self.activated:
                    self.activation_toggle(force=True)
                    t.signal_highlight()
            else:
                if self.activated:
                    self.activation_toggle(force=False)
                    t.signal_highlight()

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            if not self.activated:
                t.statusbar("Monkey no glasses")
                return

            self.decrypt_contents(honor_global_settings=False)

    def create_decrypt_button(self):
        kwargs = dict(
            place=self,
            parent=self,
            main=self,
            center=True,
            qframebox=True,
            mouse=True,
        )
        self.decrypt_button = self.DecryptButton(**kwargs)
        self.decrypt_button.decrypt_contents = self.decrypt_contents
        self.decrypt_button.qtextedit = self.right.qtextedit
        self.right.qtextedit.textChanged.connect(self.decrypt_button.text_changed)

    class DragDropper(GODLabel, GLOBALHighLight, DragDroper):

        def build_head_and_foot(self, sources, compressed_files):
            def make_lists(sources):
                tmp = []
                for src in sources:
                    if os.path.isdir(src):
                        for walk in os.walk(src):
                            tmp += [t.separate_file_from_folder(walk[0] + '/' + x) for x in walk[2]]
                    else:
                        tmp.append(t.separate_file_from_folder(src))

                files = [x.full_path for x in tmp if os.path.isfile(x.full_path)]
                dirs = [x.full_path for x in tmp if os.path.isdir(x.full_path)]
                size = [os.path.getsize(x) for x in files]
                return tmp, files, dirs, size

            def make_string(files, dirs, size, compressed_files):
                loc = t.separate_file_from_folder(compressed_files)

                nicedicts = []
                nicedicts.append(f"COMPRESSED FILE,{loc.filename}\n")
                nicedicts.append(f"TOTAL FILES,{len(files)}\n")
                nicedicts.append(f"TOTAL DIRS,{len(dirs)}\n")
                nicedicts.append(f"UNPACKED SIZE,{round(sum(size) / 1000)}kb\n")
                nicedicts.append(f"COMPRESSED SIZE,{round(os.path.getsize(compressed_files) / 1000)}kb\n")

                longlen = [len(x) for x in nicedicts]
                longlen.sort()
                string = ""
                for i in nicedicts:
                    extra = longlen[-1] - len(i)
                    headtail = i.split(',')
                    string += headtail[0]
                    string += " " * (extra + 1)
                    string += headtail[1]
                return string

            def make_foot(tmp):
                shortdir = ""
                for folder in [x.folder for x in tmp]:
                    check = [x for x in tmp if len(x.folder) >= len(folder) and x.folder[0:len(folder)] == folder]
                    if len(check) == len(tmp):
                        if not shortdir or len(folder) < len(shortdir):
                            shortdir = folder

                fullpaths = [x.full_path[len(shortdir):] for x in tmp]
                fullpaths.sort()
                foot = '\n'.join(fullpaths)
                return foot

            tmp, files, dirs, size = make_lists(sources)
            string = make_string(files,dirs,size,compressed_files)
            foot = make_foot(tmp)

            return string, foot

        def filesdropped(self, files, *args, **kwargs):
            if not t.config('encryption_message') or not get_activated_gpg_keys():
                t.statusbar('You must enable encryption and choose at least one recipient')
                return False

            tmpfolder = t.tmp_folder()
            tmpfile = t.tmp_file()
            for f in files:
                if os.path.isdir(f):
                    loc = t.separate_file_from_folder(f)
                    loc = t.separate_file_from_folder(tmpfolder + '/' + loc.subfolder)

                    if not os.path.exists(loc.full_path):
                        os.mkdir(loc.full_path)

                    shutil.copytree(f, loc.full_path, dirs_exist_ok=True)
                else:
                    shutil.copy(f, tmpfolder)

            compressed_file = shutil.make_archive(tmpfile, 'zip', tmpfolder, base_dir='./')
            head, foot = self.build_head_and_foot(files, compressed_file)
            shutil.rmtree(tmpfolder)

            with open(compressed_file, 'rb') as f:
                file_stream = f.read()
                self.generate_and_post_paste(text=file_stream, head=head, foot=foot)

            os.remove(compressed_file)

    def create_drag_n_drop_label(self):
        self.drag_n_drop_label = self.DragDropper(
            place=self,
            qframebox=True,
            mouse=True,
            drops=True,
            center=True,
            deactivated_on=dict(background='rgb(55,55,55)', color=BLACK, font=6),
            deactivated_off=dict(background='rgb(30,30,30)', color=BLACK, font=6),
        )
        self.drag_n_drop_label.setToolTip('Drag and drop files/folders here')
        self.drag_n_drop_label.setText("[   O   ]")
        self.drag_n_drop_label.generate_and_post_paste = self.post.generate_and_post_paste

    def decrypt_message_into_file(self, org_content, tmpfolder=None):
        """
        if there are several "--BEGIN PGP MESSAGE--" in the input, the first one will be treated
        and the rest will be thrown, therefore if important a feature that supports multiple blocks
        should be implemented (probably never/not important)
        :param org_content: string
        :param tmpfile: string
        :return:
        """
        if not tmpfolder:
            tmpfolder = t.tmp_folder()

        if '-----BEGIN PGP MESSAGE-----' in org_content:
            rv = decrypt_text_message(org_content)
            if rv:
                tmpfile = t.tmp_file()
                with open(tmpfile, 'wb') as f:
                    f.write(rv[0].data)

                try:
                    shutil.unpack_archive(tmpfile, format='zip', extract_dir=tmpfolder)
                    t.statusbar('Banana planted!')
                    return True
                except shutil.ReadError:
                    t.statusbar('Not real banana!')
                    return False

        t.statusbar('APESHIT!!')
        return False

    def decrypt_contents(self, honor_global_settings=True):
        if honor_global_settings:
            if not t.config('autodecrypt_messages'):
                return

        text = self.right.qtextedit.toPlainText()
        if '-----BEGIN PGP MESSAGE-----' in text:
            rv = decrypt_text_message(text)

            if rv:
                try: [str(x) for x in rv if x]
                except:
                    t.statusbar(message='Banana could be broken, banana could be zipfile!')
                    return False
            elif type(rv) == list and False in rv:
                t.statusbar(message='AT LEAST ONE BAD BANANA!')
            else:
                t.statusbar(message='STEPPED IN APESHIT!!')
                return False

            if rv:
                rv = [str(x) for x in rv if x]
                self.right.qtextedit.setText("\n".join(rv))

    def create_url_plate(self):
        class URLLabel(GODLabel):
            def default_color_and_size(self, default=True, error=False):
                if default and not error:
                    style(self, background='rgb(16, 10, 17)', color='rgb(115, 182, 32)')
                elif error:
                    style(self, color=HIGH_RED)

                pos(self, width=self, add=20)
                t.correct_broken_font_size(self)
                t.shrink_label_to_text(self, x_margin=10)

        self.url_label = URLLabel(place=self, qframebox=True)
        self.url_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.url_label.default_color_and_size()

    def show_active_gpg_keys(self):
        keys = get_activated_gpg_keys()
        if not keys or not t.config('encryption_message') and not t.config('sign_message'):
            self.encryption.setText('GPG ENCRYPTION OFF')
        else:
            self.encryption.setText(keys[0]['user'])

        t.correct_broken_font_size(self.encryption, shorten=True, presize=False)

    def show_verification_status(self):
        def toggle_label(self, on=False, off=False):
            if off and self.verification:
                self.verification.close()
                self.verification = False
            elif on and not self.verification:
                self.verification = GODLabel(place=self, qframebox=True)

        text = self.right.qtextedit.toPlainText()
        v = verify_signed_data(text)
        if v == False:
            toggle_label(self, off=True)
            return

        toggle_label(self, on=True)

        if v.valid:
            self.verification.setText('GOOD SIGNATURE')
            style(self.verification, background='rgb(16, 10, 17)', color=ACTIVE_GREEN)
        else:
            self.verification.setText('BAD SIGNATURE')
            style(self.verification, background='rgb(16, 10, 17)', color=HIGH_RED)

        pos(self.verification, height=self.url_label, after=self.url_label, x_margin=1)
        t.shrink_label_to_text(self.verification, x_margin=10)

    def create_time_slider(self):
        class SliderBTN(GODLabel):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.slider_dicts = [
                    dict(factor=0.2, value='10M', text='10 minutes'),
                    dict(factor=0.3, value='1H', text='1 hour'),
                    dict(factor=0.4, value='1D', text='1 day'),
                    dict(factor=0.5, value='1W', text='1 week'),
                    dict(factor=0.6, value='2W', text='2 weeks'),
                    dict(factor=0.7, value='1M', text='1 month'),
                    dict(factor=0.8, value='6M', text='6 months'),
                    dict(factor=0.9, value='1Y', text='1 year'),
                    dict(factor=1.0, value='N', text='Never expire'),
                ]
                self.current = self.slider_dicts[-1]
                t.style(self, background='darkCyan', color=BLACK, font=6)

            def set_saved_slider_position(self):
                value = t.config('slider_btn')
                max = self.parent.width() - self.width()
                for d in self.slider_dicts:
                    if d['value'] == value:
                        pos(self, move=[max * d['factor'], 3])
                        self.current = d
                        self.setText(d['text'])
                        t.style(self, background='darkCyan', color=BLACK, font=6)
                self.white_label_reach()

            def white_label_reach(self):
                reach = dict(right=dict(left=self))
                pos(self.parent.whiteline, height=1, top=self.parent.blackline, move=[0, 1], reach=reach)

            def drag_widget(self, ev):
                if not self.old_position:
                    self.old_position = ev.globalPos()

                delta = QtCore.QPoint(ev.globalPos() - self.old_position)
                self.move(self.x() + delta.x(), 3)

                if self.geometry().right() > self.parent.width():
                    pos(self, right=self.parent.width())
                elif self.geometry().left() < 0:
                    pos(self, left=0)

                self.old_position = ev.globalPos()
                self.white_label_reach()

            def slider_position_factor(self):
                where = self.pos().x()
                max = self.parent.width() - self.width()
                return where / max

            def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
                factor = self.slider_position_factor()
                for d in self.slider_dicts:
                    if factor < d['factor']:
                        t.save_config('slider_btn', d['value'])
                        self.current = d
                        break

                self.setText(self.current['text'])
                t.style(self, background='darkCyan', color=BLACK)

            def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
                self.drag_widget(ev)
                self.change_text()

            def change_text(self):
                factor = self.slider_position_factor()
                for d in self.slider_dicts:
                    if factor < d['factor']:
                        self.current = d
                        break

                self.setText(self.current['text'])
                t.style(self, background='cyan', color=DARK_BACK)

            def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                self.old_position = ev.globalPos()

        self.slider_label = GODLabel(place=self, main=self)
        self.slider_label.blackline = GODLabel(place=self.slider_label)
        self.slider_label.whiteline = GODLabel(place=self.slider_label)
        style(self.slider_label.blackline, background=BLACK)
        style(self.slider_label.whiteline, background='rgb(60,60,60)')
        pos(self.slider_label.whiteline, move=[1,0])
        self.slider_btn = SliderBTN(
            place=self.slider_label,
            parent=self.slider_label,
            main=self,
            qframebox=True,
            center=True,
        )

    def create_privacy_buttons(self):
        self.privacy_buttons = []
        class Buttons(GODLabel, GLOBALHighLight):
            def toggle_privacy_settings(self, save=True):
                [x.activation_toggle(save=save) for x in self.privacy_buttons if x.activated]
                self.activation_toggle(save=save)
                t.signal_highlight()

            def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                self.toggle_privacy_settings()

        for k,v in dict(PUBLIC=0, SECRET=1, PRIVATE=2).items():
            label = Buttons(
                place=self,
                type=k,
                qframebox=True,
                mouse=True,
                load=True,
                center=True,
                deactivated_on=dict(background=LIGHT_GRAY, color=BLACK),
                deactivated_off=dict(background=GRAY, color=BLACK),
            )
            label.privacy = v
            label.setText(k)
            label.privacy_buttons = self.privacy_buttons
            t.correct_broken_font_size(label, x_margin=6, y_margin=10)
            self.privacy_buttons.append(label)

    def position_mainwindow(self, primary=True):
        """ starts by centering the window on primary screen """
        if primary:
            primary_monitor = [x for x in screeninfo.get_monitors() if x.is_primary]
            if primary_monitor:
                primary = primary_monitor[0]

                x = int(primary.x)
                y = int(primary.y)
                w = int(primary.width * 0.6)
                h = int(primary.height * 0.8)

                self.move(x + int(primary.width * 0.1), y + (int(primary.height * 0.1)))
                self.resize(w, h)
            else:
                self.resize(1000, 700)
                self.move(100,100)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        if not self.steady:
            return
        # CONFIG >
        pos(self.refresh_button, height=BUTTONHEIGHT, left=0, top=self.new)
        pos(self.config_button, after=self.refresh_button, x_margin=1, height=BUTTONHEIGHT)

        # SEARCH/TITLE BAR >
        reach = dict(right=self.width() * 0.50)
        pos(self.searchbar, below=self.refresh_button, y_margin=1, reach=reach, width=self.searchbar, sub=5, height=37)
        reach = dict(right=self.width() - 2)
        pos(self.titlebar_widget, height=self.searchbar, after=self.searchbar, move=[5,0], reach=reach)

        # LEFT
        pos(self.left, below=self.searchbar, width=self.searchbar, reach=dict(bottom=self.height() - 30))

        # GPG ENCRYPTION >
        pos(self.encryption_toggle, size=[BUTTONHEIGHT / 2, BUTTONHEIGHT], left=self.titlebar_widget, bottom=self.left)
        pos(self.sign_toggle, coat=self.encryption_toggle, after=self.encryption_toggle, x_margin=-1)
        pos(self.decryption_toggle, coat=self.sign_toggle, after=self.sign_toggle, x_margin=-1)

        # URL LABEL >
        w = self.left.width() * 0.5
        pos(self.url_label, width=w, height=self.searchbar, above=self.encryption_toggle, y_margin=1)
        if self.verification:
            pos(self.verification, height=self.url_label, after=self.url_label, x_margin=1)


        # GPG RECIPIENTS >
        reach = dict(right=dict(right=self.url_label))
        pos(self.encryption, height=BUTTONHEIGHT, after=self.decryption_toggle, move=[-1,0], reach=reach)
        t.correct_broken_font_size(self.encryption, shorten=True, presize=False)

        # PRIVACY >
        for count, i in enumerate(self.privacy_buttons):
            if count == 0:
                pos(i, after=self.encryption, height=BUTTONHEIGHT, width=BUTTONHEIGHT * 3, x_margin=2)
            else:
                pos(i, coat=self.privacy_buttons[count-1], after=self.privacy_buttons[count-1], x_margin=-1)

        # SLIDER >
        reach = dict(right=dict(right=self.titlebar_widget))
        pos(self.slider_label, height=self.encryption, after=self.privacy_buttons[-1], reach=reach, x_margin=2)
        pos(self.slider_label, width=self.slider_label, sub=5)
        pos(self.slider_label.blackline, width=self.slider_label, height=3, top=self.slider_label.height() * 0.5)
        pos(self.slider_btn, size=self.privacy_buttons[0], sub=5)

        if self.slider_btn.geometry().right() > self.slider_label.width():
            pos(self.slider_btn, left=0)
            self.slider_btn.setText('ouch!')

        reach = dict(right=dict(left=self.slider_btn))
        pos(self.slider_label.whiteline, height=1, top=self.slider_label.blackline, move=[0,1], reach=reach)

        # RIGHT >
        reach=dict(bottom=dict(top=self.url_label))
        pos(self.right, below=self.titlebar_widget, width=self.titlebar_widget, reach=reach)
        pos(self.left.scrollarea, height=self.left, sub=self.left.toolplate.height())
        pos(self.right.scrollarea, height=self.right, sub=self.right.toolplate.height())
        pos(self.right.backplate, height=self.right.scrollarea, sub=self.right.lineWidth() * 4)
        pos(self.right.qtextedit, size=self.right.backplate)

        # NEW / POST / UPDATE / DELETE >
        pos(self.new, height=BUTTONHEIGHT, above=self.titlebar_widget, y_margin=1)
        pos(self.post, height=BUTTONHEIGHT, right=self.width() - 2, top=self.new)

        # DRAG DROP LABEL >
        pos(self.drag_n_drop_label, coat=self.refresh_button, before=self.post, x_margin=1)

        # DECRYPT BUTTON
        pos(self.decrypt_button, size=[BUTTONHEIGHT * 4, BUTTONHEIGHT], after=self.new, x_margin=1)

        # EXTRACTBAR
        reach = dict(right=dict(left=self.drag_n_drop_label))
        pos(self.extractbar, height=self.new, after=self.decrypt_button, x_margin=1, reach=reach)

        # BTC BUTTON
        pos(self.btc_button, height=BUTTONHEIGHT, width=BUTTONHEIGHT / 3, after=self.config_button)

    class LeftScrollWidget(MovableScrollWidget):
        def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
            self.set_positions()
            [pos(x, width=self) for x in self.widgets if x.width() != self.width()]


    def setup_gui(self):
        self.left = self.LeftScrollWidget(place=self, main=self, parent=self, mouse=True, qframebox=True)
        self.right = MovableScrollWidget(place=self, main=self, parent=self, mouse=True, qframebox=True)

        self.right.make_title(text='YOUR CONTENT GOES HERE')
        self.left.make_title(text='YOUR PASTES GOES HERE')
        pos(self.left.title, height=0)
        pos(self.right.title, height=0)

        self.right.qtextedit = QtWidgets.QTextEdit(self.right.backplate)
        self.right.qtextedit.setFont(QtGui.QFont('Monospace', 11, QtGui.QFont.Monospace))
        self.right.qtextedit.activated = False
        self.right.widgets.append(self.right.qtextedit)
        self.right.qtextedit.show()

        self.right.qtextedit.textChanged.connect(self.show_verification_status)
        self.right.qtextedit.textChanged.connect(self.decrypt_contents)

        style(self.left, background=DARK_BACK, color=LIGHT_GRAY)
        style(self.right, background=DARK_BACK, color=LIGHT_GRAY)
        style(self.right.qtextedit, background='rgb(16, 10, 17)', color='rgb(255, 212, 42)')

    class ConfigButton(GODLabel, GLOBALHighLight):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.child = False

        def one_active_paste_same_url_key_check(self):
            """
            while updating everything must match, one active paste, the active paste url must match
            url_label.text() this becuase we dont want to piss on something else when updating than
            just the single thing that is active at the time
            :return: self.widget
            """
            only_active_widget = [x for x in self.left.widgets if x.activated]
            if len(only_active_widget) == 1:
                if only_active_widget[0].data[DB.pastes.paste_url] == self.parent.url_label.text():
                    return only_active_widget[0]

        def create_lineedit_thing(self, tiplabel, type, special=None, *args, **kwargs):
            thing = create_indikator(
                place=self.child.backplate,
                button=True,
                lineedit=True,
                mouse=True,
                tiplabel=tiplabel,
                type=type,
                tipfont=10,
                tipwidth=100,
                lineedit_background=DARK_BACK,
                canvas_background=BLACK,
                load=True,
                Special=special,
                inherit_type=True,
                signal=True,
                *args, **kwargs,
            )
            if not self.child.widgets:
                pos(thing, width=self.child.backplate, height=30)
            else:
                pos(thing, coat=self.child.widgets[-1], below=self.child.widgets[-1])

            self.child.widgets.append(thing)
            self.child.expand_me()

        def create_label_thing(self, type, text, special=None, *args, **kwargs):
            thing = create_indikator(
                place=self.child.backplate,
                button=True,
                label=True,
                mouse=True,
                type=type,
                label_background=DARK_BACK,
                canvas_background=BLACK,
                load=True,
                Special=special,
                inherit_type=True,
                signal=True,
                *args, **kwargs,
            )
            if not self.child.widgets:
                pos(thing, width=self.child.backplate, height=30)
            else:
                pos(thing, coat=self.child.widgets[-1], below=self.child.widgets[-1])

            thing.label.setText(text)
            thing.label.setIndent(3)
            thing.label.mousePressEvent = thing.button.mousePressEvent

            self.child.widgets.append(thing)
            self.child.expand_me()

        def create_child(self, text='SETTINGS'):
            self.child = MovableScrollWidget(
                place=self.main,
                main=self.main,
                parent=self,
                qframebox=True,
                signal=True,
            )
            self.child.signal.killswitch.connect(self.toggle_widget)
            self.child.make_title(text)

        class NormalSetting(Canvas):
            class LineEdit(Canvas.LineEdit):
                def __init__(self, password=False, *args, **kwargs):
                    self.password = password
                    super().__init__(*args, **kwargs)
                    self.signal.activated.connect(self.correct_text)
                    self.signal.deactivated.connect(self.incorrect_text)

                def incorrect_text(self):
                    style(self, color=GRAY)

                    if self.tiplabel:
                        t.swapper(self.type, value=self.tiplabel.text())
                        self.tiplabel.setText('UNSAVED!')

                    if self.button:
                        self.button.orange_button()

                def correct_text(self):
                    style(self, color=WHITE)
                    restore = t.swapper(self.type)

                    if restore and self.tiplabel:
                        self.tiplabel.setText(restore)

                    if self.button:
                        for i in ['activated_on', 'activated_off', 'deactivated_on', 'deactivated_off']:
                            self.button.swap_preset(i, restore=True)

                def text_changed(self, safeword='*****'):
                    text = self.text().strip()
                    if not text:
                        return
                    elif self.password and text == safeword:
                        return
                    elif text != t.config(self.type):
                        self.signal.deactivated.emit()
                        style(self, font=14)
                    else:
                        self.signal.activated.emit()
                        if self.password:
                            style(self, font=8)
                            self.setText(safeword)
                    t.signal_highlight()

            class Button(Canvas.Button):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.signal.activated.connect(lambda: self.activation_toggle(force=True, save=False))
                    self.signal.deactivated.connect(lambda: self.activation_toggle(force=False, save=False))

                def orange_button(self):
                    self.swap_preset(variable='activated_on', new_value=dict(background=YELLOW))
                    self.swap_preset(variable='activated_off', new_value=dict(background=ORANGE))
                    self.swap_preset(variable='deactivated_on', new_value=dict(background=YELLOW))
                    self.swap_preset(variable='deactivated_off', new_value=dict(background=ORANGE))

                def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                    if self.lineedit:
                        text = self.lineedit.text()
                        if text:
                            t.save_config(self.type, text)
                            self.signal.activated.emit()

        class LabelSetting(Canvas):
            class Button(Canvas.Button):
                def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                    self.activation_toggle()

        class IMGSetting(Canvas, DragDroper):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.setToolTip('DRAG AND DROP IMAGE HERE')

            class Button(GODLabel):
                def __init__(self, *args, **kwargs):
                    super().__init__(qframebox=True, *args, **kwargs)
                    style(self, background=LIGHT_GRAY, color=BLACK)
                    signal = t.signals(name='privacy_images')
                    signal.activated.connect(self.load_image)

                def load_image(self):
                    blob = t.config(self.type)
                    if blob:
                        path = t.blob_path_from_blob_object(blob, self.type)
                        if path and os.path.exists(path):
                            self.clear()
                            xy = self.height() - 2
                            pixmap = QtGui.QPixmap(path).scaled(xy, xy, transformMode=QtCore.Qt.SmoothTransformation)
                            self.setPixmap(pixmap)

            class Label(Canvas.Label):
                def filesdropped(self, files, *args, **kwargs):
                    if os.path.exists(files[0]):
                        blob = t.make_image_into_blob(files[0], height=self.height() * 1.5)
                        if blob:
                            t.save_config(self.type, blob)
                            t.tmp_file(self.type, extension='webp', delete=True) # resets old file
                            self.button.load_image()

        def toggle_widget(self):
            self.activation_toggle()
            if self.activated:
                if self.child:
                    self.child.show()
                    self.child.raise_()
                else:
                    kwargs = dict(special=self.NormalSetting, password=True)
                    self.create_child()
                    self.create_lineedit_thing(tiplabel='USERNAME', type='username', special=self.NormalSetting)
                    self.create_lineedit_thing(tiplabel='PASSWORD', type='password', **kwargs)
                    self.create_lineedit_thing(tiplabel='API KEY', type='api_key', **kwargs)
                    [x.lineedit.text_changed() for x in self.child.widgets]
                    self.create_label_thing(text='SHOW EXPIRED', type='show_expired', special=self.LabelSetting)
                    kwargs = dict(special=self.IMGSetting, drops=True)
                    self.create_label_thing(text='PRIVATE IMAGE', type='img_private', **kwargs)
                    self.create_label_thing(text='SECRET IMAGE', type='img_secret', **kwargs)
                    self.create_label_thing(text='PUBLIC IMAGE', type='img_public', **kwargs)
                    self.child.set_positions()
                    pos(self.child, left=self, top=self.main.left, move=[40,20])
                    signal = t.signals(name='privacy_images')
                    signal.activated.emit()


            elif self.child:
                self.child.hide()

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.toggle_widget()
            t.signal_highlight()

    class GPGEncryption(ConfigButton):
        class GPGThing(Canvas):
            def __init__(self, data, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.data = data

            class Label(Canvas.Label):
                def __init__(self, *args, **kwargs):
                    super().__init__(
                        activated_on=dict(color=WHITE),
                        activated_off=dict(color='rgb(225,225,225)'),
                        deactivated_on=dict(color='rgb(180,180,180)'),
                        deactivated_off=dict(color=GRAY),
                        *args, **kwargs
                    )
                    self.setText(self.parent.data['user'])

            def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                self.activation_toggle()
                self.button.activated = self.activated
                self.label.activated = self.activated
                self.show_active_gpg_keys()

        def create_thing(self, special=GPGThing, *args, **kwargs):
            thing = create_indikator(
                place=self.child.backplate,
                button=True,
                label=True,
                mouse=True,
                label_background=DARK_BACK,
                label_foreground=TITLE_WHITE,
                canvas_background=BLACK,
                Special=special,
                inherit_type=True,
                signal=True,
                *args, **kwargs,
            )
            if not self.child.widgets:
                pos(thing, width=self.child.backplate, height=30)
            else:
                pos(thing, coat=self.child.widgets[-1], below=self.child.widgets[-1])

            t.correct_broken_font_size(thing.label, shorten=True, presize=False, x_margin=10, y_margin=4)
            thing.show_active_gpg_keys = self.main.show_active_gpg_keys

            self.child.widgets.append(thing)
            self.child.expand_me()

        def toggle_widget(self):
            keys = get_all_gpg_keys()
            if not keys:
                self.setText('NO GPG KEYS FOUND')
                return

            self.activation_toggle()
            if self.activated:
                if self.child:
                    self.child.show()
                    self.child.raise_()
                else:
                    self.create_child(text='GPG RECIPIENTS')
                    pos(self.child, above=self.parent.right, width=self.parent.right)
                    for i in keys:
                        self.create_thing(data=i, type=i['data']['keyid'], load=True)

                    self.child.set_positions()
                    pos(self.child, top=self.main.right, left=self.main.right, move=[-40,20])

            elif self.child:
                self.child.hide()

    def create_button(self, text=None, Special=ConfigButton):
        button = Special(
            place=self,
            main=self,
            parent=self,
            mouse=True,
            center=True,
            qframebox=True,
            activated_on=dict(background=LIGHT_GRAY, color=BLACK),
            activated_off=dict(background=LIGHT_GRAY, color=BLACK),
            deactivated_on=dict(background=LIGHT_GRAY, color=BLACK),
            deactivated_off=dict(background=GRAY, color=BLACK),
        )

        if text:
            button.setText(text)
            t.shrink_label_to_text(button, x_margin=10, y_margin=4)

        return button

    class Refresh(GODLabel, GLOBALHighLight):
        def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.get_my_pastes(refill=True)

    class NEWButton(ConfigButton):
        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.titlebar.setText("")
            self.qtextedit.setText("")
            self.url_label.setText("")

    class POSTButton(ConfigButton):
        def apply_gpg_signature(self, text):
            if not t.config('sign_message') or not get_activated_gpg_keys():
                return text

            signature = sign_message(text)
            if signature:
                return str(signature)
            else:
                return False

        def apply_gpg_encryption(self, text):
            if not t.config('encryption_message') or not get_activated_gpg_keys():
                return text

            rv = encrypt_message(text)
            if not rv or not rv.ok:
                return False

            if str(rv) != str(text): # we want input to differ from output, else not encrypted
                return str(rv)
            else:
                return False

        def generate_and_post_paste(self, text=None, head=None, foot=None):
            privacy = 0
            expire = self.slider_btn.current['value']
            title = self.titlebar.text().strip()
            if not text: text = self.qtextedit.toPlainText()
            text = self.apply_gpg_encryption(text)
            text = self.apply_gpg_signature(text)
            if head:
                text = head + '\n' + text

            if foot:
                text += '\n' + foot

            if text:
                for k, v in dict(PUBLIC=0, SECRET=1, PRIVATE=2).items():
                    if t.config(k):
                        privacy = v
                response = api_communicate(text=text, title=title, expire=expire, privacy=privacy)
                if response:
                    tmp = response.split('/')
                    response_control = api_communicate(paste_key=tmp[-1])

                    if response_control:
                        if response_control == text or get_activated_gpg_keys():
                            query, values = sqlite.empty_insert_query('pastes')
                            values[DB.pastes.paste_key] = tmp[-1]
                            values[DB.pastes.paste_url] = response
                            values[DB.pastes.paste_title] = title
                            values[DB.pastes.paste_private] = privacy
                            values[DB.pastes.paste_date] = int(time.time())
                            values[DB.pastes.paste_size] = len(text)
                            dbid = sqlite.execute(query, values=values)
                            data = sqlite.execute('select * from pastes where id is (?)', dbid)
                            if data:
                                self.main.draw_my_pastes(data=[data])
                                new = [x for x in self.left.widgets if x.data == data]
                                if len(new) == 1:
                                    new = new[0]
                                    new.toggle_others()
                                    new.activation_toggle(force=True)
                                    new.swap_colors()
                                    new.show_all_but_text()
                            return True

            self.url_label.setText('ERROR!!!')
            self.url_label.default_color_and_size(error=True)

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.generate_and_post_paste()

    def create_new_post_delete_update(self):
        self.new = self.create_button(text='NEW', Special=self.NEWButton)
        self.post = self.create_button(text='PUBLISH', Special=self.POSTButton)
        for i in [self.new, self.post]:
            i.qtextedit = self.right.qtextedit
            for ii in ['titlebar', 'url_label', 'get_my_pastes', 'slider_btn', 'left', 'right']:
                setattr(i, ii, getattr(self, ii))

    def create_searchbar(self):
        self.searchbar = create_indikator(
            place=self,
            lineedit=True,
            tiplabel='SEARCH FREELY...',
            tipfont=8,
            lineedit_background=DARK_BACK,
        )
        self.searchbar.lineedit.returnPressed.connect(self.free_search)

    def create_titlebar(self):
        self.titlebar_widget = create_indikator(
            place=self,
            lineedit=True,
            tiplabel='PASTE TITLE...',
            tipfont=8,
            lineedit_background=DARK_BACK,
        )
        self.titlebar = self.titlebar_widget.lineedit

    def free_search(self):
        text = self.searchbar.text().strip()
        data = sqlite.execute('select * from pastes', all=True)
        data = t.uni_search(data, text, DB.pastes.paste_title)
        if data:
            self.draw_my_pastes(data=data)

    class EncryptionToggle(GODLabel, GLOBALHighLight):
        def __init__(self, *args, **kwargs):
            super().__init__(
                activated_on=dict(background=HIGH_GREEN, color=BLACK),
                activated_off=dict(background=ACTIVE_GREEN, color=BLACK),
                deactivated_on=dict(background=YELLOW, color=BLACK),
                deactivated_off=dict(background=ORANGE, color=BLACK),
                *args, **kwargs
            )
            self.show_active_gpg_keys = self.main.show_active_gpg_keys

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.activation_toggle()
            self.show_active_gpg_keys()
            t.signal_highlight()

    def create_gpg_settings(self):
        self.encryption = self.create_button(text='GPG ENCRYPTION OFF', Special=self.GPGEncryption)
        self.encryption.deactivated_on = dict(background=WHITE, color=BLACK)
        self.encryption.deactivated_off = dict(background=LIGHT_GRAY, color=BLACK)

        self.encryption_toggle = self.EncryptionToggle(
            place=self,
            type='encryption_message',
            mouse=True,
            qframebox=True,
            load=True,
            main=self,
        )
        self.encryption_toggle.setToolTip('GPG ENCRYPTION ON/OFF')
        self.sign_toggle = self.EncryptionToggle(
            place=self,
            type='sign_message',
            mouse=True,
            qframebox=True,
            load=True,
            main=self,
        )
        self.sign_toggle.setToolTip('SIGN MESSAGES ON/OFF')
        self.decryption_toggle = self.EncryptionToggle(
            place=self,
            type='autodecrypt_messages',
            mouse=True,
            qframebox=True,
            load=True,
            main=self,
        )
        self.decryption_toggle.setToolTip('AUTODECRYPT MESSAGES ON/OFF')

    def create_config_button(self):
        self.config_button = self.create_button(text='SETTINGS')

    def create_refresh_button(self):
        self.refresh_button = self.create_button(text='REFRESH', Special=self.Refresh)
        self.refresh_button.get_my_pastes = self.get_my_pastes

    def get_my_pastes(self, refill=False, highlight=None):
        def thread_gather_response(self):
            self._tmp_response = api_communicate(headers=True)
        def store_gathered_data(self):
            if self._tmp_response: store_response(self._tmp_response)
        def refill_new_data(self):
            data = sqlite.execute('select * from pastes', all=True)
            tmp = [x.data[DB.pastes.paste_key] for x in self.left.widgets]
            refilldata = [x for x in data if x[DB.pastes.paste_key] not in tmp]
            if refilldata:
                self.draw_my_pastes(data=refilldata)

        def highlight_this_pastekey(self):
            tmp = [x for x in self.left.widgets if x.data[DB.pastes.paste_key] == highlight]
            [(x.activation_toggle(), x.swap_colors()) for x in tmp]

        self._tmp_response = None

        master_fns = [store_gathered_data]
        if refill: master_fns.append(refill_new_data)
        if highlight: master_fns.append(highlight_this_pastekey)
        t.start_thread(thread_gather_response, self, master_fn=master_fns, master_args=self)

    def draw_my_pastes(self, data=None):
        if not data:
            t.close_and_pop(self.left.widgets)
            data = sqlite.execute('select * from pastes', all=True)
            if not data:
                return False

        if not t.config('show_expired'):
            epoch = time.time()
            data = [x for x in data if not x[DB.pastes.paste_expire_date] or x[DB.pastes.paste_expire_date] > epoch]

        for i in data:
            paste = PasteWidget(place=self.left.backplate, main=self, parent=self, data=i)
            self.left.widgets.append(paste)

        self.left.widgets.sort(key=lambda x:x.data[DB.pastes.paste_date])

        for count in range(len(self.left.widgets)-1,-1,-1):
            paste = self.left.widgets[count]

            if paste == self.left.widgets[-1]:
                pos(paste, left=0, top=0, width=self.left, height=30)
            else:
                pos(paste, coat=self.left.widgets[count+1], below=self.left.widgets[count+1], y_margin=1)

            paste.right = self.right
            paste.left = self.left
            paste.widgets = self.left.widgets
            paste.titlebar = self.titlebar
            paste.url_label = self.url_label
            paste.privacy_buttons = self.privacy_buttons
            paste.show_verification_status = self.show_verification_status
            paste.decrypt_contents = self.decrypt_contents
            paste.post_init()

        self.left.expand_me(backplate_only=True)