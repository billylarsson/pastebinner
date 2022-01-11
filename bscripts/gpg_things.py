from bscripts.tricks import tech as t
import gnupg
import os
import time
import subprocess

def return_gpg_state():
    homedir = os.path.expanduser('~')
    gpgdir = homedir + '/.gnupg'
    loc = t.separate_file_from_folder(gpgdir)

    if not os.path.exists(loc.full_path):
        return False

    cs_gpg_options = ['--pinentry-mode loopback'] # dont know why V2 had this

    try: gpg_connection = gnupg.GPG(homedir=loc.full_path, options=cs_gpg_options)
    except: gpg_connection = gnupg.GPG(gnupghome=loc.full_path, options=cs_gpg_options)

    gpg_connection.encoding = 'utf-8'

    return gpg_connection

def get_all_gpg_keys():
    gpg = return_gpg_state()
    if gpg:

        all_keys = gpg.list_keys()

        sorter = {}
        for c in range(len(all_keys)):
            thiskey = all_keys[c]
            if thiskey['expires'] == "" or time.time() < float(thiskey['expires']):

                recipient = ' + '.join(thiskey['uids'])
                if thiskey['uids'][0] in sorter:
                    sorter[thiskey['uids'][0]]['data'].append(thiskey)
                    sorter[thiskey['uids'][0]]['recipient'].append(recipient)
                else:
                    sorter[thiskey['uids'][0]] = dict(data=[thiskey], recipient=[recipient])

        if sorter:

            temp = {k: v for k, v in sorted(sorter.items(), key=lambda item: item[0])}

            gpg_keys = []

            count = -1
            for user in temp:
                for cc in range(len(temp[user]['recipient'])):
                    recipients = temp[user]['recipient'][cc]
                    data = temp[user]['data'][cc]
                    count += 1
                    gpg_keys.append({'data': data, 'recipients': recipients, 'user': user})

            return gpg_keys

def get_activated_gpg_keys():
    keys = get_all_gpg_keys()
    if not keys:
        return False

    return [x for x in keys if t.config(x['data']['keyid'])]

def arch_linux_fix(contents, fingerprints):
    tmpfile_input = t.tmp_file('fuck_duck_input', hash=True, delete=True, extension='asc')
    tmpfile_output = t.tmp_file('fuck_duck_output', hash=True, delete=True, extension='asc')

    if type(contents) == str:
        flag = 'w'
    else:
        flag = 'wb'

    with open(tmpfile_input, flag) as f:
        f.write(contents)

    query = ['gpg', '-se', '-a']
    for i in fingerprints:
        query.append('-r')
        query.append(i)

    query += ['-o', tmpfile_output, '--trust-model', 'always', tmpfile_input]

    subprocess.run(query)
    with open(tmpfile_output, 'r') as f:
        data = f.read()
    
    os.remove(tmpfile_output)
    os.remove(tmpfile_input)

    return data

def encrypt_message(contents, fingerprints=None):

    def just_encrypt(file_or_text, list_with_fingerprints):
        encrypted_data = gpg.encrypt(file_or_text, list_with_fingerprints, always_trust=True, armor=True)
        return encrypted_data

    if not fingerprints:
        fingerprints = get_activated_gpg_keys()
        fingerprints = [x['data']['fingerprint'] for x in fingerprints]

    if not fingerprints:
        return False

    gpg = return_gpg_state()
    if gpg:
        encrypted_contents = just_encrypt(contents, fingerprints)
        if len(encrypted_contents.data) == 0:
            good_fingers = []
            for i in fingerprints:
                encrypted_contents = just_encrypt(contents, [i])

                if len(encrypted_contents.data) > 0:
                    good_fingers.append(i)

            if good_fingers:
                encrypted_contents = just_encrypt(contents, good_fingers)

        if len(encrypted_contents.data) > 0:
            return encrypted_contents

    rv = arch_linux_fix(contents=contents, fingerprints=fingerprints)
    
    return rv

def sign_message(text):
    gpg = return_gpg_state()
    if gpg:
        keys = get_activated_gpg_keys()
        if keys:
            signature = gpg.sign(text, keyid=keys[0]['data']['keyid'])
            return signature

    return text

def verify_signed_data(content):
        sign_string = '-----BEGIN PGP SIGNATURE-----'
        if sign_string not in content:
            return False

        gpg = return_gpg_state()
        if gpg:
            verification = gpg.verify(content)
            return verification

        return False


def decrypt_text_message(org_content):
    gpg_state = return_gpg_state()
    rv_text = []
    while gpg_state:

        str1 = '-----BEGIN PGP MESSAGE-----'
        str2 = '-----END PGP MESSAGE-----'
        cut1 = org_content.find(str1)

        if cut1 < 0:
            break

        org_content = org_content[cut1:]
        cut2 = org_content.find(str2)

        if cut2 < 0:
            break

        encrypted_text = org_content[0:cut2 + len(str2)]
        decrypted_text = gpg_state.decrypt(encrypted_text)

        try:
            if type(decrypted_text.data) == bytes:
                rv_text.append(decrypted_text)
            else:
                try: 
                    rv_text.append(str(decrypted_text))
                except: 
                    rv_text.append(False)
        except:
            rv_text.append(False)

        org_content = org_content[cut2 + len(str2):]

    return rv_text