from bscripts.database_stuff import DB, sqlite
from bscripts.tricks         import tech as t
import copy
import urllib.parse
import urllib.request

def store_response(response):
    """
    stores the response into local database, updates previous entries, keeping same sqlitedb id
    """

    end = '</paste>'
    cycle = [
        'paste_date',
        'paste_expire_date',
        'paste_format_long',
        'paste_format_short',
        'paste_hits',
        'paste_key',
        'paste_private',
        'paste_size',
        'paste_title',
        'paste_url',
    ]

    query, values = sqlite.empty_insert_query('pastes')
    _values = copy.copy(values)
    _values[DB.pastes.username] = t.config('username')
    execute_many = []

    response = response.split('\n')
    for row in response:
        row = row.strip().strip('\t')
        if row == end:
            execute_many.append(tuple(_values))
            _values = copy.copy(values)
            _values[DB.pastes.username] = t.config('username')
            continue

        for c in range(len(cycle)):
            cycle_string_start = f'<{cycle[c]}>'
            cycle_string_end = f'</{cycle[c]}>'
            if len(row) > len(cycle_string_start) + len(cycle_string_end):
                if row[0:len(cycle_string_start)] == cycle_string_start:
                    if row[-(len(cycle_string_end)):] == cycle_string_end:
                        add_string = row[len(cycle_string_start): -(len(cycle_string_end))]
                        if len(add_string) > 0 and str(add_string).lower() != 'none':
                            _values[getattr(DB.pastes, cycle[c])] = add_string
                        break

    for c in range(len(execute_many) - 1, -1, -1):
        checkdata = sqlite.execute('select * from pastes where paste_key = (?)', execute_many[c][DB.pastes.paste_key])
        if checkdata:
            execute_many[c] = list(execute_many[c])
            execute_many[c][0] = checkdata[0]
            execute_many[c] = tuple(execute_many[c])
            sqlite.execute('delete from pastes where id = (?)', (checkdata[0],))

    sqlite.execute(query, execute_many)

def provide_url(url):
    if url == 'post':
        return 'https://pastebin.com/api/api_post.php'
    elif url == 'login':
        return 'https://pastebin.com/api/api_login.php'
    elif url == 'raw':
        return 'https://pastebin.com/api/api_raw.php'

def get_credentials():
    class creds:
        status = True
        apikey = t.config('api_key')
        username = t.config('username')
        password = t.config('password')
        if not apikey: status = False
        if not username: status = False
        if not password: status = False

    return creds()

def login_session():
    """
    eastablishes a login session from pastebin.com
    :return: login session
    """
    creds = get_credentials()
    if not creds.status:
        return False

    login_params = dict(
        api_dev_key=creds.apikey,
        api_user_name=creds.username,
        api_user_password=creds.password,
    )

    data = urllib.parse.urlencode(login_params).encode("utf-8")
    req = urllib.request.Request(provide_url('login'), data)

    try:
        with urllib.request.urlopen(req) as _:
            return req
    except urllib.error.HTTPError:
        return False

def api_communicate(
                    paste_key=None,
                    headers=False,
                    limit=1000,
                    text=None,
                    title=None,
                    privacy=None,
                    expire=None,
                    delete=False,
                    ):
    req = login_session()
    if not req:
        return False

    creds = get_credentials()
    if not creds.status:
        return False

    with urllib.request.urlopen(req) as req_response:
        if delete:
            pastebin_vars = dict(
                api_option='delete',
                api_dev_key=creds.apikey,
                api_user_key=req_response.read(),
                api_paste_key=paste_key,
            )
        elif headers:
            pastebin_vars = dict(
                api_option='list',
                api_dev_key=creds.apikey,
                api_user_key=req_response.read(),
                api_results_limit=limit,
            )
        elif paste_key:
            pastebin_vars = dict(
                api_option='show_paste',
                api_dev_key=creds.apikey,
                api_user_key=req_response.read(),
                api_paste_key=paste_key,
            )
        elif text:
            pastebin_vars = dict(
                api_dev_key=creds.apikey,
                api_option='paste',
                api_paste_code=text,
                api_paste_expire_date=expire,
                api_paste_name=title,
                api_paste_private=privacy,
                api_user_key=req_response.read(),
            )

        params = urllib.parse.urlencode(pastebin_vars).encode('utf8')
        try: response = urllib.request.urlopen(provide_url('post'), params)
        except urllib.error.HTTPError: return False
        except: return False

        if response:
            response = response.read()
            response = response.decode('utf8')
            return response

