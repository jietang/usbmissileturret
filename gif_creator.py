from PIL import Image
from images2gif import writeGif
import os


def create_gif_from_files(fnames, out_path):
    images = []
    for fname in fnames:
        images.append(Image.open(fname))
    writeGif(out_path, images, duration=0.20)

if __name__=="__main__":
    FOLDER = 'pics'
    folder = '1342774052'

    files = ["%s/%s/%s" % (FOLDER, folder, fname) for fname in sorted(os.listdir(FOLDER+'/'+folder), key=lambda x: int(x.split('.')[0]))]

    create_gif_from_files(files, 'out.gif')
