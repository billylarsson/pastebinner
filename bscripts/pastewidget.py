from PyQt5                     import QtCore, QtGui
from bscripts.database_stuff   import DB, sqlite
from bscripts.pastebin_api     import api_communicate
from bscripts.preset_colors    import *
from bscripts.settings_widgets import GODLE, GODLabel, GLOBALHighLight
from bscripts.tricks           import tech as t
import time,os

pos = t.pos
style = t.style

class PasteWidget(GODLabel):
    def __init__(self, data, *args, **kwargs):
        self.steady = False
        self.delete_button = False
        self.update_button = False
        self.syntax = False
        super().__init__(*args, **kwargs)
        self.data = data

    def post_init(self):
        self.set_privacy_image()
        self.make_title()
        self.set_time()
        self.set_size()
        self.make_random_label()
        self.set_syntax()
        self.make_time_left_label()
        self.swap_colors()
        self.steady = True

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        if not self.steady:
            return

        w = self.width() * 0.5
        pos(self.title, height=self.privacy_image, after=self.privacy_image, width=w, x_margin=1)
        self.set_time(create=False)
        pos(self.size_or_views, height=self.title, after=self.time, x_margin=1)
        pos(self.random_label, coat=self.time, after=self.size_or_views, x_margin=1, reach=dict(right=self.width()))
        if self.syntax: pos(self.syntax, height=self.title, width=100, right=self.width() - 10)
        self.make_time_left_label(create=False)
        if self.delete_button and self.update_button:
            pos(self.delete_button, height=self, width=self.height() / 2, right=self.width())
            pos(self.update_button, height=self, before=self.delete_button, x_margin=-1)

    def make_random_label(self):
        """ currently no real use """
        self.random_label = GODLabel(place=self, monospace=True)
        pos(self.random_label, coat=self.time, after=self.size_or_views, x_margin=1, reach=dict(right=self.width()))

    def make_time_left_label(self, create=True):
        """ theres a colored label in the background to indicate the time left of the paste """
        expire = self.data[DB.pastes.paste_expire_date]

        if expire:
            if create:
                self.expire = GODLabel(place=self, monospace=True)
                self.expire.lower()
                style(self.expire, background='rgba(140, 10, 10, 140)')

            total_time = self.data[DB.pastes.paste_expire_date] - self.data[DB.pastes.paste_date]
            life_span = time.time() - self.data[DB.pastes.paste_date]

            progress = life_span / total_time
            w = self.width() * progress
            if w > self.width(): w = self.width()
            pos(self.expire, inside=self, width=w)

    def make_title(self):
        """ lineedit, later on maybe we'll change the title from within this label """
        self.title = GODLE(place=self, monospace=True)
        self.title.setAlignment(QtCore.Qt.AlignVCenter)
        self.title.setText(self.data[DB.pastes.paste_title])
        w = self.width() * 0.5
        pos(self.title, height=self.privacy_image, after=self.privacy_image, width=w, x_margin=1)

    def set_syntax(self):
        """ shows current syntax, Python, C, C++, currently very low/none usage for this """
        if self.data[DB.pastes.paste_format_long]:
            self.syntax = GODLabel(place=self, center=True)
            self.syntax.setText(self.data[DB.pastes.paste_format_long])
            pos(self.syntax, height=self.title, width=100, right=self.width() - 10)
            t.correct_broken_font_size(self.syntax, shorten=True, presize=False)

    def set_privacy_image(self):
        """
        QLabel with a QPixmap
        each pricavy level has its onw image which it will try first if not present, use background color
        """
        self.privacy_image = GODLabel(place=self)
        xy = self.height() - 2
        pos(self.privacy_image, size=[xy,xy], move=[1,1])

        def generate_path_and_background(self):
            if self.data[DB.pastes.paste_private] == 2:
                privacy_type = 'img_private'
                background = 'rgb(40,40,50)'

            elif self.data[DB.pastes.paste_private] == 1:
                privacy_type = 'img_secret'
                background = 'rgb(50,50,50)'

            else:
                privacy_type = 'img_public'
                background = 'rgb(70,70,70)'

            blob = t.config(privacy_type)

            if blob: path = t.blob_path_from_blob_object(blob, type=privacy_type)
            else: path = None

            return path, background

        path, background = generate_path_and_background(self)

        if path and os.path.exists(path):
            pixmap = QtGui.QPixmap(path).scaled(xy, xy, transformMode=QtCore.Qt.SmoothTransformation)
            self.privacy_image.setPixmap(pixmap)
        else:
            style(self.privacy_image, background=background)

    def set_time(self, create=True):
        """ time that the paste was pasted, somewhere somehow i belive its a few minutes of """
        if create:
            self.time = GODLabel(place=self, center=True, monospace=True)
            style(self.time, color=BLACK)

        long_date = t.timeconverter(self.data[DB.pastes.paste_date], long=True)
        self.time.setText(long_date)
        pos(self.time, height=self.title, after=self.title, x_margin=1)
        t.shrink_label_to_text(self.time)

        if self.width() - self.time.geometry().right() < 200:
            short_date = t.timeconverter(self.data[DB.pastes.paste_date])
            self.time.setText(short_date)
            t.shrink_label_to_text(self.time)


    def set_size(self):
        """ contents size """
        self.size_or_views = GODLabel(place=self, monospace=True)
        self.size_or_views.setIndent(3)
        self.size_or_views.setText('#####')
        t.shrink_label_to_text(self.size_or_views, x_margin=6)
        self.size_or_views.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        pos(self.size_or_views, height=self.title, after=self.time, x_margin=1)
        size = self.get_size_and_views_string(size=True)
        style(self.size_or_views, color=BLACK)
        if size not in {0,'0'}:
            self.size_or_views.setText(size)
        else:
            self.size_or_views.setText('')
            self.size_or_views.setToolTip('Relaxing user experience applied...')


    def set_views(self):
        """ currently not used, not even in the tooltips """
        views = self.get_size_and_views_string(views=True)
        self.size_or_views.setText(views)

    def get_size_and_views_string(self, size=False, views=False):
        """
        sucks i know, reusing something from pastebinner v1 when i was a noob
        :return: string
        """
        cycle = {
            999999: {'divide': 100000, 'letter': 'M'},
            9999: {'divide': 1000, 'letter': 'K'},
        }

        clist = [self.data[DB.pastes.paste_size] or 0, self.data[DB.pastes.paste_hits] or 0]
        for c in range(len(clist)-1,-1,-1):
            for above in cycle:
                if clist[c] > above:
                    clist[c] = f"{round(clist[c] / cycle[above]['divide'])}{cycle[above]['letter']}"
                    if cycle[above]['letter'] == 'M':
                        clist[c] = f'{clist[c][0:-2]}.{clist[c][-2:len(clist[c])]}'
                    break
        if size:
            return str(clist[0])
        elif views:
            return str(clist[1])

    def show_my_contents(self, *args, **kwargs):
        """ shows title, content, privacy settings, forgotten why args,kwargs... """
        text = self.data[DB.pastes.contents]
        paste_url = self.data[DB.pastes.paste_url]
        if not text or not paste_url:
            return

        self.right.qtextedit.setText(text)
        self.url_label.setText(paste_url)
        self.url_label.default_color_and_size()

        if self.data[DB.pastes.paste_title]:
            self.titlebar.setText(self.data[DB.pastes.paste_title])
        else:
            self.titlebar.setText("")

        for i in self.privacy_buttons:
            if i.privacy == self.data[DB.pastes.paste_private]:
                i.toggle_privacy_settings(save=False)

        self.show_verification_status()
        self.decrypt_contents()

    def swap_colors(self):
        """ when you click one paste it changes color and change all others 'back' """
        if not self.activated:
            for i in [self, self.size_or_views, self.time, self.random_label]:
                style(i, background='rgb(38, 7, 15)', color='rgb(255, 244, 190)')

            style(self.title, background='rgba(28, 7, 15, 200)', color='rgb(245, 234, 180)')
        else:
            for i in [self, self.size_or_views, self.time, self.random_label]:
                style(i, background=GRAY, color=BLACK)

            style(self.title, background='rgba(78, 57, 55, 200)', color='rgb(255,255,130)')

    class DeleteButton(GODLabel, GLOBALHighLight):
        """
        deletebutton shows first when you click the widget and hides when click another
        deletes from server first, then from local database and finally close/pop widget
        """
        def delete_paste_remote_and_locally(self):
            rv = api_communicate(self.data[DB.pastes.paste_key], delete=True)
            sqlite.execute('delete from pastes where id is (?)', self.data[0])
            self.left.widgets = [x for x in self.left.widgets if x != self.parent]
            self.parent.close()
            if rv == 'Paste Removed':
                t.statusbar("Gone banana!")
                return True

            t.statusbar("There's just to many monkeys here, but maybe I killed a spare monkey!")

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.delete_paste_remote_and_locally()

    def show_deletebutton(self):
        if self.delete_button:
            self.delete_button.show()
            self.delete_button.raise_()
            return

        self.delete_button = self.DeleteButton(place=self, mouse=True, qframebox=True, main=self.main, parent=self)
        self.delete_button.data = self.data
        self.delete_button.url_label = self.url_label
        self.delete_button.left = self.left
        self.delete_button.setToolTip('PERMANENTLY DELETE!')
        pos(self.delete_button, height=self, width=self.height() / 2, right=self.width())

    class UpdateButton(GODLabel, GLOBALHighLight):
        def update_delete_overwrite(self):
            self.generate_and_post_paste()
            self.delete_paste_remote_and_locally()

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.update_delete_overwrite()

    def show_update_button(self):
        if self.update_button:
            self.update_button.show()
            self.update_button.raise_()
            return

        kwargs = dict(
            place=self,
            mouse=True,
            qframebox=True,
            main=self.main,
            parent=self,
            center=True,
            activated_on=dict(background=HIGH_GREEN, color=BLACK),
            activated_off=dict(background=ACTIVE_GREEN, color=BLACK),
            deactivated_on=dict(background=YELLOW, color=BLACK),
            deactivated_off=dict(background=ORANGE, color=BLACK),
        )
        self.update_button = self.UpdateButton(**kwargs)
        self.update_button.data = self.data
        self.update_button.url_label = self.url_label
        self.update_button.left = self.left
        self.update_button.setToolTip('WILL DELETE THIS ONE, THEN GIVE YOU A NEW ONE!')
        self.update_button.setText('UPDATE')
        self.update_button.generate_and_post_paste = self.main.post.generate_and_post_paste
        t.shrink_label_to_text(self.update_button, x_margin=10)
        self.show_deletebutton()
        self.update_button.delete_paste_remote_and_locally = self.delete_button.delete_paste_remote_and_locally
        pos(self.update_button, height=self, before=self.delete_button, x_margin=-1)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        """
        when clicking one paste all others are toggled off and this one highlights, if
        contents are'nt locally avaible, it will get them from the Pastebin API.

        if you rightclick a widget the text wont be shown or downloaded, this is beacuse
        it can be an unnessesary experience when just clicking a paste to delete it
        """
        self.toggle_others()
        self.activation_toggle()
        self.swap_colors()

        if ev.button() == 1:
            if not self.data[DB.pastes.contents]:

                def thread_gather_response(self):
                    self._tmp_response = api_communicate(paste_key=self.data[DB.pastes.paste_key])

                def store_contents(self):
                    if self._tmp_response:
                        query = 'update pastes set contents = (?) where id is (?)'
                        sqlite.execute(query, values=(self._tmp_response, self.data[0],))
                        self.data = sqlite.refresh_db_input('pastes', db_input=self.data)

                self._tmp_response = None
                masterfn = [store_contents, self.show_my_contents]
                t.start_thread(slave_fn=thread_gather_response, slave_args=self, master_fn=masterfn, master_args=self)
            else:
                self.show_my_contents()

        elif ev.button() == 2:
            self.show_all_but_text()

        if self.activated:
            self.show_deletebutton()
            self.show_update_button()
            t.signal_highlight()

    def toggle_others(self):
        [x.delete_button.hide() for x in self.widgets if x.delete_button]
        [x.update_button.hide() for x in self.widgets if x.update_button]
        [(x.activation_toggle(), x.swap_colors(),) for x in self.widgets if x.activated]

    def show_all_but_text(self):
        self.url_label.setText(self.data[DB.pastes.paste_url])
        self.url_label.default_color_and_size()

        if self.data[DB.pastes.paste_title]:
            self.titlebar.setText(self.data[DB.pastes.paste_title])
        else:
            self.titlebar.setText("")

        for i in self.privacy_buttons:
            if i.privacy == self.data[DB.pastes.paste_private]:
                i.toggle_privacy_settings(save=False)