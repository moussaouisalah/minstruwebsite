import youtube_dl
from spleeter.separator import Separator
import os
import shutil


def downloadvideo(song_id, song_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'temporary/{}.%(ext)s'.format(song_id),
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([song_url])


def gettitlefromyoutube(url):
    try:
        with youtube_dl.YoutubeDL() as ydl:
            return ydl.extract_info(url, download=False)['title']
    except:
        return None


def mainfunction(song_id, song_url, db, app):
    downloadvideo(song_id, song_url)
    separator = Separator('spleeter:2stems')
    separator.separate_to_file('./temporary/{}.mp3'.format(song_id), './songs')
    os.remove(os.path.join('temporary', '{}.mp3'.format(song_id)))
    count = db.engine.execute("SELECT COUNT() FROM song WHERE url='{}'".format(song_url)).first()[0]
    if count == 0:
        try:
            shutil.rmtree(os.path.join(app.root_path, 'songs', str(song_id)))
        except:
            pass
    else:
        db.engine.execute("UPDATE song SET status='ready' WHERE id={}".format(song_id))
        db.session.commit()

