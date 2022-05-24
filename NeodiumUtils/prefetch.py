import gdown
from os import environ as env

def getCookieFile():
    """
    CookieFile Fetcher
    -------------------
    A function that just downloads the credential files from G-drive whenever invoked
    """
    id_insta = env['INSTA_COOKIEFILE_ID']
    id_yt = env['YT_COOKIEFILE_ID']
    output_insta = 'insta_cookies.txt'
    output_yt = 'yt_cookies.txt'
    gdown.download(output=output_insta, id=id_insta, quiet=False)
    gdown.download(output=output_yt, id=id_yt, quiet=False)