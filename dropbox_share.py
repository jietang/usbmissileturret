import datetime
import os
import pickle
import time

from dropbox import client, rest, session

from mail import send_mail_with_link
from lightbox import get_lightbox_url
from gif_creator import create_mp4_in_dir

FOLDER = 'pics'


APP_KEY = 'igzwf6cwio3j5vm'
APP_SECRET = '3se8ns9l8hrpb6x'

ACCESS_TYPE = 'app_folder'

def get_access_token():
    if not os.path.exists('dbturret_token'):
        sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
        request_token = sess.obtain_request_token()
     
        url = sess.build_authorize_url(request_token)
        print "url:", url
        print "Please visit this website and press the 'Allow' button, then hit 'Enter' here."
        raw_input()
     
        access_token = sess.obtain_access_token(request_token)
     
        with open("dbturret_token", 'w') as f:
            f.write(access_token.key+chr(0)+access_token.secret)
     
    with open("dbturret_token") as f:
        key, secret = f.read().strip().split(chr(0))
        access_token = session.OAuthToken(key, secret)
        return access_token

def get_turret_client():
    access_token = get_access_token()
    sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
    sess.set_token(access_token.key, access_token.secret)
    return client.DropboxClient(sess)


cl = get_turret_client()
print "linked account:", cl.account_info()



# on load, get metadata, maintain list of ts (top level folders)
seen_folders = set()
meta = cl.metadata('/')
for data in meta['contents']:
    if data['is_dir']:
        seen_folders.add(data['path'][1:])

# every so often poll the pics folder, for every new folder, add it
while True:
    folders_to_add = set(os.listdir(FOLDER))
    folders_to_add = folders_to_add.difference(seen_folders)

    for folder in folders_to_add:

        # convert timestamp to human readable
        out_fname = datetime.datetime.fromtimestamp(int(folder)).strftime('%B %d %Y %I:%M%p.mp4')

        local_path = '%s/%s/%s' % (FOLDER, folder, out_fname)
        local_dir = '%s/%s' % (FOLDER, folder)
        create_mp4_in_dir(local_dir, out_fname)
        # create_gif_from_files(files, local_path)

        remote_folder_path = "/%s" % "saycheeseanddie"
        remote_path="/%s/%s" % ("saycheeseanddie", out_fname)
        with open(local_path) as f:
            try:
                upload_data = cl.put_file(full_path=remote_path,
                                          file_obj=f,
                                          )
                share_dict = cl.share(remote_folder_path)
                send_mail_with_link(get_lightbox_url(share_dict['url'], out_fname))
            except rest.ErrorResponse:
                pass
        seen_folders.add(folder)

    time.sleep(3)



# monitor the pics folder
