from PIL import Image
from images2gif import writeGif
import os
from subprocess import call

def create_gif_from_files(fnames, out_path):
    images = []
    for fname in fnames:
        images.append(Image.open(fname))
    writeGif(out_path, images, duration=0.20)

def create_mp4_in_dir(dir_name, out_path):
    call(['ffmpeg', '-r', '5', '-sameq', '-i', '%s/%%d.jpg' % (dir_name), '%s/%s' % (dir_name, out_path)])

if __name__=="__main__":
    FOLDER = 'pics'
    folder = '1342816438'

    # files = ["%s/%s/%s" % (FOLDER, folder, fname) for fname in sorted(os.listdir(FOLDER+'/'+folder), key=lambda x: int(x.split('.')[0]))]

    # create_gif_from_files(files, 'out.gif')
    create_mp4_in_dir("%s/%s" % (FOLDER, folder), 'out.mp4')
