from flask import Flask, Response, redirect, render_template, request, abort, stream_with_context
from werkzeug.datastructures import Headers
from requests import get
from urllib.request import urlopen
import requests
import youtube_dl

ip_addr = '192.168.1.9' #modify to suit your needs
port = '5000'		#modify to suit your needs

class u2be():
	def __init__(self, youtubeLink):
		self.ydl_opts = {'format': 'bestaudio/best'}
		self.youtubeLink = youtubeLink
	def getAudioUrl(self):
		with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
			info = ydl.extract_info(self.youtubeLink, download=False)
			num = 0
			for key in range(len(info['formats'])):
				if info['formats'][num]['format_id'] == '251':
					format = info['formats'][num]['url']
					print('Format: 251')
					return format
					break
				elif info['formats'][num]['format_id'] == '171':
					format = info['formats'][num]['url']
					print('Format: 171')
					return format
					break
				elif info['formats'][num]['format_id'] == '140':
					format = info['formats'][num]['url']
					print('Format: 140')
					return format
					break
				num += 1

	def genPlaylist(self):
		ydl_opts = {'extract_flat': True, 'dumpjson': True}
		remKeys =['uploader_id', 'uploader', 'uploader_url', 'extractor_key', '_type', 'extractor', 'webpage_url', 'title', 'webpage_url_basename', 'id']
		try:
			with youtube_dl.YoutubeDL(ydl_opts) as ydl:
				info = ydl.extract_info(self.youtubeLink, download=False)
				for key in remKeys:
					info.pop(key)
				currentList = {}
				for keys,values in info.items():
					nr = 0
					for item in values:
						nr += 1
						currentList.update({nr:{'title':item['title'], 'url':'http://{}:{}/listen/{}'.format(ip_addr, port, item['url'])}})
					return currentList
		except:
			error = ({'0':{'title':'ERROR, CHECK URL, "{}" IS NOT A VALID URL'.format((self.youtubeLink).upper()), 'url':'empty'}})
			return error

app = Flask(__name__)
@app.route('/listen', defaults={'path': ''})
@app.route('/listen/<path:path>')
def getAudio(path):
	headers = Headers()
	#headers.add('Accept-Ranges', 'bytes')
	#headers.add('X-Frame-Options', 'SAMEORIGIN')
	#headers.add('X-Content-Type-Options', 'nosniff')
	#headers.add('X-XSS-Protection', '1; mode=block')
	chunk = 10*1024
	ytSource = urlopen(u2be(path).getAudioUrl())
	def generate():
		stream = ytSource.read(chunk)
		while stream:
			yield stream
			stream = ytSource.read(chunk)
	return Response(stream_with_context(generate()),status=200, headers=headers, mimetype="audio/mp4")

@app.route('/ytPlaylist/<path:path>')
def getPlaylist(path):
	if path != None:
		def generate():
			playlista = u2be(path).genPlaylist()
			yield('#EXTM3U\n')
			for key in playlista:
				yield('#EXTINF:-1, {}\n{}\n'.format(playlista[key]['title'],playlista[key]['url']))
		return Response(stream_with_context(generate()),status=200, mimetype="text/plain")
	else:
		return(403)

if __name__ == "__main__":
	app.run(host=ip_addr, port=port, debug=False)
