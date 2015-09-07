#!/usr/bin/env python
# -*- coding: utf-8

# Created by Bailey Kong

from __future__ import print_function
from __future__ import unicode_literals
import sys, os, glob
from tagsheet import TagSheet
from mutagen.mp3 import MP3
from mutagen.id3 import TPE1, TALB, TDRC, TRCK, TIT2
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC

if len(sys.argv)==1:
    path = '.'
else:
    path = ' '.join(sys.argv[1:])
full_path = os.path.abspath(path)

tag_data = []
cue_files = glob.glob(full_path+os.path.sep+'*.cue')
if len(cue_files)>0:
    if len(cue_files)>1:
        print('WARNING: Multiple cue files detected!')
        print('         Using first cue file found:', cue_files[0])
    # process first cue file
    ts = TagSheet(open(cue_files[0]).read())
    album = ts.tags['TITLE']
    artist = ts.tags['PERFORMER']
    date = ts.tags['DATE']
    year = date[0].split('.')[0]
    for audiofile in ts.audiofiles:
        if len(audiofile.tracks)>1:
            print('WARNING: Multiple tracks for audio file:', audiofile.file_name)
            print('         Falling back on using predetermined filenames.')

            for t in audiofile.tracks:
                track_num = t.track_number
                track_title = t.tags['TITLE']
                if 'PERFORMER' in t.tags:
                    track_artist = t.tags['PERFORMER']
                else:
                    track_artist = artist
                track_fname = '%02d - %s.%s' % (track_num, track_title, audiofile.file_format.lower())
                tag_data.append({'album': album,
                                 'date': date,
                                 'year': year,
                                 'track_artist': track_artist,
                                 'track_num': track_num,
                                 'track_title': track_title,
                                 'track_fname': full_path+os.path.sep+track_fname,
                                 'track_format': audiofile.file_format.lower()})
        else:
            track_fname = audiofile.file_name
            track = audiofile.tracks[0]
            track_num = track.track_number
            track_title = track.tags['TITLE']
            if 'PERFORMER' in track.tags:
                track_artist = track.tags['PERFORMER']
            else:
                track_artist = artist
            tag_data.append({'album': album,
                             'date': date,
                             'year': year,
                             'track_artist': track_artist,
                             'track_num': track_num,
                             'track_title': track_title,
                             'track_fname': full_path+os.path.sep+track_fname,
                             'track_format': audiofile.file_format.lower()})


else:
    d_name = full_path.split(os.path.sep)[-1]
    artist, d_name = d_name.split(' - ')
    album, d_name = d_name.split(' [')
    date = d_name.split(']')[0]
    year = date.split('.')[0]

    for f_name in os.listdir(path):
        idx = f_name.rfind('.')
        ext = f_name[idx+1:].lower()
        name = f_name[:idx]
        if ext not in ['mp3', 'ogg', 'flac']:
            continue

        track_num, track_title = name.split(' - ')
        tag_data.append({'album': album,
                         'date': date,
                         'year': year,
                         'track_artist': artist,
                         'track_num': track_num,
                         'track_title': track_title,
                         'track_fname': full_path+os.path.sep+f_name,
                         'track_format': ext})

# Write the tag data
for t in tag_data:
    if t['track_format'] == 'mp3':
        mp3 = MP3(t['track_fname'])
        mp3.delete()

        mp3['TPE1'] = TPE1(encoding=3, text=t['track_artist'])
        mp3['TALB'] = TALB(encoding=3, text=t['album'])
        mp3['TDRC'] = TDRC(encoding=3, text=t['year'])
        mp3['TRCK'] = TRCK(encoding=3, text=t['track_num'])
        mp3['TIT2'] = TIT2(encoding=3, text=t['track_title'])
        mp3.save()

    elif t['track_format'] == 'ogg':
        ogg = OggVorbis(t['track_fname'])
        ogg.delete()

        ogg['artist'] = t['track_artist']
        ogg['album'] = t['album']
        ogg['date'] = t['date']
        ogg['year'] = t['year']
        ogg['tracknumber'] = t['track_num']
        ogg['title'] = t['track_title']
        ogg.save()

    elif t['track_format'] == 'flac':
        flac = FLAC(t['track_fname'])
        flac.delete()

        flac['artist'] = t['track_artist']
        flac['album'] = t['album']
        flac['date'] = t['date']
        flac['year'] = t['year']
        flac['tracknumber'] = t['track_num']
        flac['title'] = t['track_title']
        flac.save()