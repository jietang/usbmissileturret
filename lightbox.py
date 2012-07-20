import urllib2

def get_lightbox_url(dbtt_url, fname):
    f = urllib2.urlopen(dbtt_url)
    real_url = f.geturl()
    
    return real_url + "#f:" + fname.replace(' ', '%20').replace(':', '%3A')

if __name__=="__main__":
    TEST_URL = 'http://db.tt/YT9dLQ0b'
    TEST_FNAME = 'July 20 2012 03:04AM.gif'

    print get_lightbox_url(TEST_URL, TEST_FNAME)
