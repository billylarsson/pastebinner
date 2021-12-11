from bscripts.database_stuff import DB, sqlite
from bscripts.pastebin_api import api_communicate, store_response
from bscripts.tricks import tech as t
from bscripts.gpg_things import encrypt_message
import sys, time

def api_calls(self):
    orders = sys.argv[1:]

    def output_found_one_match(header, pastes):
        text = f'\n\nSearching for "{header}" ...\nFOUND 1 MATCH!\n\nINPUT: {pastes[0][0]}\nURL: '
        text += f'{pastes[0][DB.pastes.paste_url]}\nTITLE/HEADER: {pastes[0][DB.pastes.paste_title]}\n'
        for k, v in dict(PUBLIC=0, SECRET=1, PRIVATE=2).items():
            if v == pastes[0][DB.pastes.paste_private]:
                text += f'PRIVACY: {k}'
        text += f'LAST UPDATED: {t.timeconverter(pastes[0][DB.pastes.paste_date], long=True)}\n'
        print(text)

    def get_refreshed_widget_from_title(self, orders):
        for count, i in enumerate(orders[0:-1]):
            if i == '--header':
                print("REFRESING ALL PASTES FROM SERVER ...")
                tmp = api_communicate(headers=True)  # fully updates headers to avoid stepping in apeshit
                if tmp:
                    print("GOT RESPONSE, STORING ...")
                    store_response(tmp)
                else:
                    print('Dooooooooooh!')

                epoch = time.time()
                header = orders[count + 1]
                data = sqlite.execute('select * from pastes where paste_title is not null', all=True)
                data = [x for x in data if x[DB.pastes.paste_title].lower().find(header.lower()) > -1]
                data = [x for x in data if not x[DB.pastes.paste_expire_date] or x[DB.pastes.paste_expire_date] > epoch]

                if len(data) == 0 and '-n' in orders:
                    # todo this is an ugly hack, not sure how/if its urgent to fix >

                    print("GENERATING A FAKE PASTE TO BUILD ON! // -n switch")

                    class FAKE:
                        query, data = sqlite.empty_insert_query('pastes')

                    fakewidget = FAKE()
                    fakewidget.data[DB.pastes.paste_private] = 2
                    fakewidget.data[DB.pastes.contents] = ""
                    fakewidget.update_button = fakewidget
                    fakewidget.update_button.generate_and_post_paste = self.post.generate_and_post_paste

                    self.titlebar.setText(header)

                    return fakewidget

                if len(data) == 1:
                    output_found_one_match(header, data)
                    t.close_and_pop(self.left.widgets)
                    self.draw_my_pastes(data=data, accept_unders=True)
                    if len(self.left.widgets) == 1:
                        print(f"\nSYNCRONIZING {data[0][DB.pastes.paste_url]} WITH PASTEBIN SEVERS ...")
                        widget = self.left.widgets[0]
                        tmp = api_communicate(paste_key=widget.data[DB.pastes.paste_key])

                        if tmp:
                            print("SYNCRONIZATION COMPLETED")
                            query = 'update pastes set contents = (?) where id is (?)'
                            sqlite.execute(query, values=(tmp, widget.data[0],))
                            widget.data = sqlite.refresh_db_input('pastes', db_input=widget.data)
                            return widget
                        else:
                            print("SYNCRONIZATION FAILED!")
                else:
                    print(f"FOUND {len(data)} CANDIDATES FOR {header} ... I HAS NO CLUE WHAT TO DO!!")
                break


    def make_paste_from_args(self, orders, widget):
        for count, i in enumerate(orders[0:-1]):
            if i == '--text':

                if '-e' in orders:
                    print("ENCRYPTING TEXT ... ")
                    text = encrypt_message(orders[count + 1]) or orders[count + 1]
                    if text:
                        text = str(text)
                        print("ENCRYPTION OK")
                    else:
                        print('ENCRYPTION FAILED!')
                        return False
                else:
                    text = orders[count + 1]

                if '-a' in orders:
                    print('ADDING TEXT TO PRESENT TEXT')
                    text += '\n\n' + widget.data[DB.pastes.contents]
                elif '-r' in orders:
                    print('REPLACING PRESENT TEXT WITH CURRENT TEXT ONLY')

                self.right.qtextedit.setText(text)
                print('PASSING POST REQUEST TO PASTEBIN SEVERS ...')
                kwargs = dict(ask_for_encryption=False, ask_for_signature=False, expire='N')
                response_url = widget.update_button.generate_and_post_paste(**kwargs)
                if response_url:
                    print("PASTE OK")
                    return response_url
                else:
                    print("PASTE FAILED")

    def update_widget_add_args_text(self, orders, widget):
        widget.show_all_but_text()
        widget.show_deletebutton()
        widget.show_update_button()
        return make_paste_from_args(self, orders, widget)

    if '-a' or '-r' in orders and '--header' in orders and '--text' in orders:
        widget = get_refreshed_widget_from_title(self, orders)
        if widget and widget.data[0]: # todo ugly hack
            response_url = update_widget_add_args_text(self, orders, widget)
            if response_url:
                print("DELETING OLD PASTE")
                widget.update_button.delete_paste_remote_and_locally()
                print(f'\n{response_url}\n\nJOBS DONE!')

        elif widget and not widget.data[0]: # todo ugly hack
            response_url = make_paste_from_args(self, orders, widget)
            if response_url:
                print(f'\n{response_url}\n\nJOBS DONE!')

def api_help_print():
    longlen = 0
    d = []
    d.append(dict(key='USAGE', text='python3 pastebinner.py -a -e --header="reddit/r/nintendo" --text "#switch-hacks"'))
    d.append(dict(key='-a', text='Appends text'))
    d.append(dict(key='-n', text='If none exists, create new'))
    d.append(dict(key='-e', text='Encrypt this text (doesnt touch present text)'))
    d.append(dict(key='-r', text='Replace present text with current text only'))
    d.append(dict(key='--header', text='Header that must match present headers (titles)'))
    d.append(dict(key='--text', text='Text that you want to append/update/replace'))

    for dd in d:
        if len(dd['key']) >= longlen:
            longlen = len(dd['key']) + 1

    for dd in d:
        print(dd['key'], " " * (longlen - len(dd['key'])), dd['text'])