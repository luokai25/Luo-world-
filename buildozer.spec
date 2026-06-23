[app]
title = Luo World
package.name = luoworld
package.domain = com.luokai25

source.dir = .
source.include_exts = py,png,jpg,jpeg,glb,obj,wav,ogg,mp3,ttf,json,txt,kv
source.include_patterns = assets/*,assets/**/*,game/*,engine/*,ui/*,data/*
source.exclude_dirs = tests,bin,.buildozer,.git,.github,__pycache__

version = 0.1.0
# Auto-increment build number
version.regex = __version__ = '([\d\.]+)'
version.filename = %(source.dir)s/main.py

requirements = python3,\
    kivy==2.3.1,\
    numpy,\
    pillow,\
    sdl2,\
    sdl2_image,\
    sdl2_ttf,\
    sdl2_mixer,\
    android

# Orientation: landscape for game
orientation = landscape
fullscreen = 1

# Android config
android.api = 33
android.minapi = 26
android.ndk = 25.2.9519653
android.sdk = 33
android.ndk_api = 26
android.build_tools_version = 33.0.2

# ARM64 = Poco X3 NFC (Snapdragon 732G)
android.archs = arm64-v8a

android.permissions = INTERNET,\
    VIBRATE,\
    READ_EXTERNAL_STORAGE,\
    WRITE_EXTERNAL_STORAGE

android.features = android.hardware.touchscreen

# App icon and presplash
# android.presplash_color = #1a2e1a
# android.icon.filename = assets/icon.png
# android.presplash.filename = assets/splash.png

android.logcat_filters = *:S python:D

# Release signing (debug for now)
android.release_artifact = apk
android.debug_artifact = apk

# Allow backup
android.allow_backup = True

# Gradle extras
android.gradle_dependencies = 

# Enable AndroidX
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
