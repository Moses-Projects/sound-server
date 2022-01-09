#!/usr/bin/env python3.7
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import pygame
import random
import re
import time

hostName = "192.168.14.48"
serverPort = 8080
BaseHTTPRequestHandler.server_version = "Monkeyness Sounds Server 1.0"
BaseHTTPRequestHandler.sys_version = ""

base_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'sounds')
master_volume = 100
pygame.mixer.pre_init(buffer=3096)
pygame.init()
pygame.mixer.init()

class MyServer(BaseHTTPRequestHandler):
	def do_GET(self):
		def send_web_page(self, code, contents):
			self.send_response(code)
			self.send_header("Content-type", "text/plain")
			self.end_headers()
			self.wfile.write(bytes(contents, "utf-8"))
			self.wfile.write(bytes("\n", "utf-8"))
			return True
		
		def send_sound_list(self, path, listing):
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			contents = '<html>\n<head>\n<title>Sounds server</title>\n</head>\n<body>\n'
			
			# Folder hierarchy
			contents += 'Folder: <a href="/">/</a>'
			paths = path.split('/')
			full_path = ''
			for item in paths:
				if not len(item):
					continue
				full_path += '/' + item
				contents += ' <a href="{}/">{}/</a>'.format(full_path, item)
			contents += '\n\n<ul>\n'
			
			# Sound list
			listing.sort()
			for item in listing:
				contents += '<li><a href="{}">{}</a></li>\n'.format(item, item)
			contents += '</ul>\n</body></html>'.format(item, item)
			self.wfile.write(bytes(contents, "utf-8"))
			self.wfile.write(bytes("\n", "utf-8"))
			return True
		
		def convert_volume(volume):
			global master_volume
			master_base = master_volume - 70
			new_volume = int(master_base * volume /100) + 70
			return new_volume
		
		def play_mpg123(sound_file, volume=None):
			global master_volume
			if type(volume) is None:
				volume = master_volume
			os.system('sudo amixer cset numid=1 {}%'.format(convert_volume(volume)))
			os.system('mpg123 -q ' + sound_path)
			os.system('sudo amixer cset numid=1 {}%'.format(master_volume))
			
		def play_pygame(sound_file, volume=None):
			global master_volume
			if type(volume) is None:
				volume = master_volume / 100
			else:
				volume = convert_volume(volume) / 100
			pygame.mixer.music.set_volume(volume)
			pygame.mixer.music.load(sound_file)
			pygame.mixer.music.play()
			
		
		# Parse URI
		original_path = re.sub(r'\?.*$', '', self.path)
		query_string = ''
		args = {}
		if re.search(r'\?', self.path):
			query_string = re.sub(r'^.*?\?', '', self.path)
			query_parts = query_string.split('&')
			for pair in query_parts:
				pair_parts = pair.split('=', 1)
				if pair_parts[0] and pair_parts[1]:
					args[pair_parts[0]] = pair_parts[1]
		
		# Set master volume
		global master_volume
		path_parts = re.match(r'/volume/(\d+)$', original_path)
		if path_parts:
			new_volume = int(path_parts[1])
			if new_volume >= 0 and new_volume <= 100:
				master_volume = 0
				if new_volume > 0:
					master_volume = int(new_volume * .3 + 70)
				play_mpg123('/opt/sounds-server/sounds/apple/tink.mp3')
				return send_web_page(self, 200, "Volume set to {}".format(new_volume))
			else:
				return send_web_page(self, 403, "Invalid volume value: {}".format(new_volume))
		
		# Fail invalid requests
		elif re.search(r'(^\.|\.\.|[^a-zA-Z0-9_./](-(all|\d+))?)$', original_path):
			return send_web_page(self, 403, "Unauthorized request: {}".format(original_path))
		
		# Good requests
		else:
			arg_path = original_path
			arg_path = re.sub(r'(^/|/$)', '', arg_path)
			
			# Find list of sounds
			path = []
				
			if re.search(r'/', arg_path):
				dir_path = re.sub(r'/[a-zA-Z0-9_.\-]*$', '', arg_path)
				arg_path = re.sub(r'^.*/', '', arg_path)
				dir_path = base_dir + '/' + dir_path
			else:
				# Top level
				dir_path = base_dir
			
			# If dir, return sound list
			if not arg_path or os.path.isdir(dir_path + '/' + arg_path):
				dir_list = os.listdir(dir_path + '/' + arg_path)
				listing = []
				for item in dir_list:
					if re.search(r'\.mp3$', item):
						name = re.sub(r'\.mp3$', '', item)
						listing.append(name)
					elif os.path.isdir(dir_path + '/' + arg_path + '/' + item):
						listing.append(item + '/')
				
				return send_sound_list(self, original_path + '/', listing)
			
			# Get directory listing
			if not os.path.isdir(dir_path):
				return send_web_page(self, 404, "Sound not found: {}".format(original_path))
			files = os.listdir(dir_path)
			
			file_name = re.sub(r'^.*/', '', arg_path)
			for sound_file in files:
				file_match = re.compile(file_name + '(-\d+)?.mp3')
				if re.match(file_match, sound_file):
					path.append(dir_path + '/' + sound_file)
			
			if not len(path):
				return send_web_page(self, 404, "Sound not found: {}".format(original_path))
			
			# Pick random sound
# 			print("path:", path)
			sound_path = path[random.randint(0, len(path)-1)]
# 			print("sound_path:", sound_path)
		
			# Play existing sounds
			if os.path.exists(sound_path):
# 				print("Trying to play {}".format(sound_path))
				volume = master_volume
				volume_message = ''
				if 'volume' in args:
					volume = int(args['volume'])
					if volume < 0 or volume > 100:
						return send_web_page(self, 403, "Invalid volume value: {}".format(volume))
					volume_message = ' at volume {}'.format(volume)
				send_web_page(self, 200, "Playing sound{}: {}".format(volume_message, original_path))
# 				play_mpg123(sound_path, volume)
				play_pygame(sound_path, volume)
				return
		
			# Sound not found
			else:
# 				print("404 on {}".format(sound_path))
				send_web_page(self, 404, "Sound not found: {}".format(original_path))
				return
	

if __name__ == "__main__":		  
	webServer = HTTPServer((hostName, serverPort), MyServer)
	print("Server started http://%s:%s" % (hostName, serverPort))
# 	os.system('sudo amixer cset numid=1 {}%'.format(master_volume))
	
	try:
		webServer.serve_forever()
	except KeyboardInterrupt:
		pass

	webServer.server_close()
	print("Server stopped.")
