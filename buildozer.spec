[app]

# (str) Title of your application
title = 好運自己選

# (str) Package name
package.name = goodluck

# (str) Package domain (needed for android packaging)
package.domain = com.lottotaiwan

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,ttf,json

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*_original.png

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.1,sqlite3,openssl,requests,supabase,httpx,httpcore,anyio,sniffio,h11,postgrest,realtime,gotrue,storage3,urllib3,certifi,idna,charset_normalizer

# (str) Custom source folders for requirements
# It may be useful when he need to add some python-for-android packaging
#custom_source_folders = 

# (str) Application version (method 1)
version = 1.0

# (list) Supported orientations
# Valid values are: landscape, portrait, portrait-reverse, landscape-reverse
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,DEBUG_PORT

#
# Android specific
#

# (bool) Indicate if the XML parsing should be support (for android)
#android.xml_support = True

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
#android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 33

# (str) Android NDK version to use
#android.ndk = 25b

# (bool) Use --private data directory (True, default) or --dir public directory (False)
#android.private_storage = True

# (str) Android NDK directory (if empty, it will be automatically downloaded)
#android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded)
#android.sdk_path =

# (str) ANT directory (if empty, it will be automatically downloaded)
#android.ant_path =

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid any unwanted updates.
#android.skip_update = False

# (bool) If True, then automatically accept SDK licenses
# This is required for clean automated builds.
android.accept_sdk_license = True

# (str) Android entry point, default is to use start.py of bootstrap
#android.entrypoint = default_as_bootstrap

# (list) Pattern to exclude from the image search path
#android.image_exclusions = 

# (str) Type of builds to run (debug or release)
#android.build_mode = debug

# (list) List of Java files to add to the android project
#android.add_src =

# (list) Gradle dependencies to add
#android.gradle_dependencies =

# (list) Packaging options to prevent duplicate files or resources in APK
#android.packaging_options =

# (list) Android meta-data to set in AndroidManifest.xml (AdMob Application ID will go here when official SDK is added)
#android.meta_data = com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-XXXXXXXXXXXXXXXX~YYYYYYYYYY

# (list) Android library project to add (aar)
#android.add_aars =

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a symbolic link
#lib_link = False

# (str) Title for the conceptual app loader (presplash)
#android.presplash_color = #121212

# (list) The Android archs to build for.
# Valid values are: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) Allow service to be ran in foreground
#android.foreground_service = False


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifacts directory (where the finished APK will be placed)
bin_dir = ./bin
