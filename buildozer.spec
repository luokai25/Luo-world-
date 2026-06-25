[app]

# App identity
title = Luo World
package.name = luoworld
package.domain = com.luokai25
version = 0.2.0

# Source
source.dir = .
source.include_exts = py,png,jpg,jpeg,wav,ogg,mp3,ttf,json,txt,kv
source.exclude_dirs = .buildozer,.git,.github,__pycache__,bin,tests,assets/models

# Requirements — ONLY packages p4a has recipes for
# python3 version must match p4a recipe (3.10.10, not 3.10.14)
requirements = python3,kivy==2.2.1,android

# Orientation & display
orientation = landscape
fullscreen = 1

# Android SDK/NDK — match what CI runner has
android.api = 33
android.minapi = 21
android.ndk = 25.2.9519653
android.ndk_api = 21
android.build_tools_version = 33.0.2

# Build BOTH arm64 (modern) and armeabi-v7a (32-bit legacy)
# covers Android 5.0+ on ALL devices
android.archs = arm64-v8a, armeabi-v7a

# Permissions
android.permissions = INTERNET,VIBRATE

# Assets
android.icon.filename = %(source.dir)s/assets/icon.png
android.presplash.filename = %(source.dir)s/assets/splash.png
android.presplash_color = #0a190a

# Gradle / AndroidX
android.enable_androidx = True
android.allow_backup = True
android.gradle_dependencies =

android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
