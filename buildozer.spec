[app]
title = Luo World
package.name = luoworld
package.domain = com.luokai25

source.dir = .
source.include_exts = py,png,jpg,jpeg,wav,ogg,mp3,ttf,json,txt,kv
source.include_patterns = assets/*,game/*,engine/*,ui/*,data/*
source.exclude_dirs = tests,bin,.buildozer,.git,.github,__pycache__,assets/models,engine/__pycache__,game/__pycache__,ui/__pycache__

version = 0.2.0

requirements = python3==3.10.14,kivy==2.2.1,android

orientation = landscape
fullscreen = 1

android.api = 33
android.minapi = 26
android.ndk = 25.2.9519653
android.ndk_api = 26
android.build_tools_version = 33.0.2
android.archs = arm64-v8a

android.permissions = INTERNET,VIBRATE

android.icon.filename = %(source.dir)s/assets/icon.png
android.presplash.filename = %(source.dir)s/assets/splash.png
android.presplash_color = #0a190a

android.enable_androidx = True
android.allow_backup = True

android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
