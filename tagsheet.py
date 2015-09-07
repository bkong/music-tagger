#!/usr/bin/env python
# -*- coding: utf-8

# Created by Eriks Dobelis
# Source: https://bitbucket.org/lazka/mutagen/issues/138/parse-cuesheet
# Modified by Bailey Kong

from __future__ import print_function
from __future__ import unicode_literals
from io import StringIO
import re

TITLE_RE = re.compile('[A-Z]* ["]?([^"]+)["]?$')
FILE_RE = re.compile('[A-Z]* ["]?([^"]+)["]? (.+)$')
TRACK_RE = re.compile('[A-Z]* ([0-9]+) (.+)$')
INDEX_RE = re.compile('[A-Z]* ([0-9]+) ([0-9]{2}:[0-9]{2}:[0-9]{2})$')
GAP_RE = re.compile('[A-Z]* ([0-9]{1,3}:[0-9]{1,2}:[0-9]{1,2})$')
GENRE_RE = re.compile('REM GENRE ["]?([^;"]+)(;([^;"]+))*["]?$')
REM_RE = re.compile('REM [A-Z]+ (.*)$')
REMTAGS = [ "GENRE", "DATE", "DISCID", "COMMENT", "ARTISTSORT", "ALBUMSORT", "ALBUMREPLAYGAIN", "YEAR" ]
STRINGTAGS = ["PERFORMER", "TITLE", "FLAGS", "ISRC", "SONGWRITER"]

def time2frames(timestamp_string):
    s = timestamp_string.split(':')
    return int(s[0])*60*75 + int(s[1])*60 + int(s[2])

def frames2time(frames):
    minutes = frames // (60*75)
    t = frames % (60*75)
    seconds = t // 75
    frames = t % 75
    return "%02d:%02d:%02d" % (minutes, seconds, frames)

class TagSheetException(Exception):
    pass
class TagSheetIndex(object):
    def __init__(self, number, timestamp):
        self.index_number = number
        self.index_offset = time2frames(timestamp)
class TagSheetTrack(object):
    def __init__(self, number, datatype):
        self.indices = []
        self.track_number = number
        self.track_datatype = datatype
        self.tags = {}
    def __repr__(self):
        return "%02d %s" % (self.track_number, self.tags["TITLE"])
class TagSheetAudioFile(object):
    def __init__(self, name, ext):
        self.file_name = name
        self.file_format = ext
        self.tracks = []
class TagSheet(object):
    def __init__(self, data):
        self.audiofiles = []
        self.tags = {}
        self.load(data)
    def load(self, data):
        lines  = StringIO(data).readlines()
        track = None
        for line in lines:
            line = line.strip()
            if line == "":
                continue
            split_line = line.split(" ")
            command = split_line[0]
            if command == "REM":
                if split_line[1] in REMTAGS:
                    if split_line[1] == "GENRE":
                        if 'GENRE' not in self.tags:
                            self.tags['GENRE'] = []
                        match = GENRE_RE.match(line)
                        i = 1
                        try:
                            self.tags['GENRE'].append(match.group(i))
                            i+=2
                        except:
                            pass
                    else:
                        match = REM_RE.match(line)
                        if split_line[1] not in self.tags:
                            self.tags[split_line[1]] = []
                        self.tags[split_line[1]].append(match.group(1))
                else:
                    if 'REM' not in self.tags:
                        self.tags[command] = []
                    self.taggs[command].append(line[4:].strip())
            elif command in ["CATALOG", "CDTEXTFILE"]:
                match = TITLE_RE.match(line)
                if match:
                    #print(command, match.group(1))
                    if command not in self.tags:
                        self.tags[command] = []
                    self.tags[command].append(match.group(1))
                else:
                    raise TagSheetException("%s command did not match, line: %s" % (command, line))
            elif command in STRINGTAGS:
                match = TITLE_RE.match(line)
                if match:
                    if track is None:
                        if command not in self.tags:
                            self.tags[command] = []
                        self.tags[command].append(match.group(1))
                    else:
                        if command not in track.tags:
                            track.tags[command] = []
                        track.tags[command].append(match.group(1))
                else:
                    raise TagSheetException("%s command did not match, line: %s" % (command, line))
            elif command in ["FILE"]:
                match = FILE_RE.match(line)
                if match:
                    self.audiofiles.append(TagSheetAudioFile(match.group(1), match.group(2)))
                else:
                    raise TagSheetException("%s command did not match, line: %s" % (command, line))
            elif command in ["TRACK"]:
                match = TRACK_RE.match(line)
                if match:
                    #print(command, match.group(1), match.group(2))
                    track = TagSheetTrack(int(match.group(1)),match.group(2))
                    self.audiofiles[-1].tracks.append(track)
                else:
                    raise TagSheetException("%s command did not match, line: %s" % (command, line))
            elif command in ["INDEX"]:
                match = INDEX_RE.match(line)
                if match:
                    #print(command, match.group(1), match.group(2), match.group(3), match.group(4))
                    index = TagSheetIndex(int(match.group(1)), match.group(2))
                    track.indices.append(index)
                else:
                    raise TagSheetException("%s command did not match, line: %s" % (command, line))
            elif command in ["POSTGAP", "PREGAP"]:
                match = GAP_RE.match(line)
                if match:
                    if track is None:
                        raise TagSheetException("%s before TRACK" % command)
                    if command not in track.tags:
                        track.tags[command] = []
                    track.tags[command] = time2frames(match.group(1))
                    #print(command, match.group(1), match.group(2), match.group(3))
                else:
                    raise TagSheetException("%s command did not match, line: %s" % (command, line))
            else:
                raise TagSheetException("Unknown command %s" % command)
    def __str__(self):
        cue = StringIO()
        if "CATALOG" in self.tags:
            for i in self.tags["CATALOG"]:
                print("CATALOG %s" % i, file = cue)
        if "CDTEXTFILE" in self.tags:
            for i in self.tags["CDTEXTFILE"]:
                print("CDTEXTFILE %s" % i, file = cue)
        if "REM" in self.tags:
            for i in self.tags["REM"]:
                print("REM %s" % i, file = cue)
        for i in REMTAGS:
            if i in self.tags:
                if i == 'GENRE':
                    print('REM GENRE "%s"' % ";".join(self.tags[i]))
                else:
                    for j in self.tags[i]:
                        print("REM %s %s" % (i, j), file = cue)
        for i in STRINGTAGS:
            if i in self.tags:
                for j in self.tags[i]:
                    if i in ["TITLE", "PERFORMER", "SONGWRITER"]:
                        print('%s "%s"' % (i, j), file = cue)
                    else:
                        print("%s %s" % (i, j), file = cue)
        for a in self.audiofiles:
            print('FILE "%s" %s' % (a.file_name, a.file_format), file = cue)
            for t in a.tracks:
                print('  TRACK %d %s' % (t.track_number, t.track_datatype), file = cue)
                for i in t.tags:
                    for j in t.tags[i]:
                        if i not in ["PREGAP", "POSTGAP"]:
                            print('    %s "%s"' % (i, j), file = cue)
                        else:
                            print('    %s %s' % (i, frames2time(j)), file = cue)
                for i in t.indices:
                    print('    INDEX %02d %s' % (i.index_number, frames2time(i.index_offset)), file = cue)
        s = cue.getvalue()
        cue.close()
        return s
    def __unicode__(self):
        return str(self)

if __name__ == "__main__":
    import argparse
    from mutagen.flac import FLAC
    parser = argparse.ArgumentParser(description = "Tagsheet library demo. Use with FLAC audiofile, which has cuesheet embedded as tag.")
    parser.add_argument('flacaudio')
    args = parser.parse_args()
    audio = FLAC(args.flacaudio)
    print("Original cuesheet:")
    print(audio["cuesheet"][0])
    ts = TagSheet(audio["cuesheet"][0])
    print("Album tags:")
    print(ts.tags)
    print("Album tracks:")
    print(ts.tracks)
    print("Regenerated cuesheet:")
    print(ts)
    ts.tags["TITLE"][0] = "Another title"
    ts.tracks[1].tags["TITLE"][0] = "Changed track title"
    print("Modified cuesheet:")
    print(ts)

#for i in audio["cuesheet"]:
#	print(i)
#	print(audio["cuesheet"][i])
