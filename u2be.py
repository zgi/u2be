from flask import Flask, Response, abort, stream_with_context
from werkzeug.datastructures import Headers
from urllib.request import urlopen
import youtube_dl

ip_addr = '192.168.1.205'  # modify to suit your needs
port = '5000'  # modify to suit your needs


def get_audio_url(video_id):
    with youtube_dl.YoutubeDL() as ydl:
        try:
            info = ydl.extract_info(video_id, download=False)
            formats = info['formats']
            usable_formats = {'171', '140'}
            max_key = None
            max_val = 0
            yt_formats = {key: int(formats[key]['format_id']) for key in range(len(formats)) if
                          formats[key]['format_id'] in usable_formats}
            for key, value in yt_formats.items():
                if value > max_val:
                    max_key = key
                    max_val = value
            print("\nStreaming audio: {}".format(info['title']))
            print("Available formats: {}".format(yt_formats))
            print("Best format index: {}".format(max_key))
            print("Streaming format: {}".format(formats[max_key]['format_id']))
            return urlopen(formats[max_key]['url'])
        except:
            print('Error! Media unavailable. Check URL')
            return abort(400)


def gen_playlist(pl_id):
    ydl_opts = {'extract_flat': True, 'dumpjson': True}
    rem_keys = ['uploader_id', 'uploader', 'uploader_url', 'extractor_key', '_type', 'extractor', 'webpage_url',
               'title', 'webpage_url_basename', 'id']
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(pl_id, download=False)
            for key in rem_keys:
                info.pop(key)
            current_list = {}
            for keys, values in info.items():
                nr = 0
                for item in values:
                    nr += 1
                    current_list.update({nr: {'title': item['title'],
                                             'url': 'http://{}:{}/listen/{}'.format(ip_addr, port, item['url'])}})
                return current_list
    except:
        error = ({'0': {'title': 'ERROR, CHECK URL, "{}" IS NOT A VALID ID'.format(pl_id.upper()),
                        'url': 'empty'}})
        return error


app = Flask(__name__)


@app.route('/listen', defaults={'path': ''})
@app.route('/listen/<path:path>')
def stream_audio(path):
    headers = Headers()
    # headers.add('Accept-Ranges', 'bytes')
    # headers.add('X-Frame-Options', 'SAMEORIGIN')
    # headers.add('X-Content-Type-Options', 'nosniff')
    # headers.add('X-XSS-Protection', '1; mode=block')
    chunk = 1 * 1024
    url = get_audio_url(path)
    def generate():
        stream = url.read(chunk)
        while stream:
            yield stream
            stream = url.read(chunk)
    return Response(stream_with_context(generate()), status=200, headers=headers, mimetype="audio/mp4")


@app.route('/ytPlaylist/<path:path>')
def make_playlist(path):
    if path is not None:
        def generate():
            playlist = gen_playlist(path)
            yield ('#EXTM3U\n')
            for song in playlist:
                yield ('#EXTINF:-1, {}\n{}\n'.format(playlist[song]['title'], playlist[song]['url']))
        return Response(stream_with_context(generate()), status=200, mimetype="text/plain")
    else:
        return abort(400)


if __name__ == "__main__":
    app.run(host=ip_addr, port=port, debug=False)
