"""
copyright (c) 2021  pritam20ps05(Pritam Das)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
"""
import gdown
from os import environ as env

class GdriveDownloadError(Exception):
    def __init__(self, id):
        super().__init__(f'Error downloading file -> {id} from google drive')

def getCookieFile(id_insta=None, id_yt=None):
    """
    CookieFile Fetcher
    -------------------
    A function that just downloads the credential files from G-drive whenever invoked
    """
    if not id_insta:
        id_insta = env['INSTA_COOKIEFILE_ID']
    if not id_yt:
        id_yt = env['YT_COOKIEFILE_ID']
    output_insta = 'insta_cookies.txt'
    output_yt = 'yt_cookies.txt'
    f1 = gdown.download(output=output_insta, id=id_insta, quiet=False)
    if not f1: raise GdriveDownloadError(id_insta)
    f2 = gdown.download(output=output_yt, id=id_yt, quiet=False)
    if not f2: raise GdriveDownloadError(id_yt)