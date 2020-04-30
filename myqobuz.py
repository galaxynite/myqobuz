# -*- coding: utf-8 -*-
#!python
# pylint: disable=line-too-long, too-many-lines

"""
Around my qobuz :
    - get playlists, favorites
    - search for artists, albums and tracks

Need module "qobuz" modified for raw mode, list of performers

"""

import sys
import os
import logging
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import datetime, timedelta
import json
import re
import requests

# read config file for login and preferences
try:
    with open('config.json') as fconf:
        MYCONFIG = json.load(fconf)
except FileNotFoundError:
    sys.exit('FAILED to load config file')

# the qobuz module can be located in a specific path
try:
    if MYCONFIG['qobuz_module']:
        sys.path.insert(0, MYCONFIG['qobuz_module'])
except KeyError:
    pass
import qobuz



def seconds_tostring(seconds):
    '''
    convert seconds to string
    format returned :
        [H:]MM:SS
    '''
    stime = []
    if seconds // 3600 > 0:
        stime.append('{}:'.format(seconds // 3600))
    stime.append('{:02d}:'.format((seconds // 60) % 60))
    stime.append('{:02d}'.format(seconds % 60))
    return ''.join(stime)


def timestamp_tostring(timestamp, fmt='%d/%m/%Y'):
    '''
    convert timestamp (negative or not) to date string
    '''
    if timestamp < 0:
        return (datetime(1970, 1, 1) + timedelta(seconds=timestamp)).strftime(fmt)
    else:
        return datetime.fromtimestamp(timestamp).strftime(fmt)


def print_header(fmt, elements):
    '''
    print header for table
    '''
    #print('Favorites Albums')
    header = fmt % elements
    print(len(header) * '=')
    print(header)
    print(len(header) * '=')



def smart_bio(bio, size):
    '''
    process qobuz artist biography
        remove html tags
        split in lines of max size, on word
    '''
    lines = list()
    if not bio:
        return lines
    # remove html tag
    re_clean = re.compile('<.*?>')
    bio = re.sub(re_clean, '', bio)
    # split on a word
    while len(bio) > size:
        bioline = bio[:size]
        pos = bioline.rfind(' ')
        if pos > 0:
            lines.append(bioline[:pos])
            bio = bio[pos:]
        else:
            lines.append(bioline)
            bio = bio[size:]
    if len(bio) > 0:
        lines.append(bio)
    return lines



def download_album_image(album):
    '''
    download album image
    '''
    filename = '{} - {}.{}.jpg'.format(album.artist.name, album.title, album.id)
    filename = filename.replace(':', '-').replace('/', '-')
    filename = '{}\\{}'.format(MYCONFIG['album']['cover_dir'], filename)
    if os.path.exists(filename):
        return
    resp = requests.get(album.images[MYCONFIG['album']['cover_size']], allow_redirects=True)
    open(filename, 'wb').write(resp.content)


def get_user_playlists(user, ptype, raw=False):
    '''
    Returns all user playlists

    Parameters
    ----------
    user: qobuz.User object
    '''
    limit = 50
    offset = 0
    playlists = list()
    while True:
        pls = user.playlists_get(filter=ptype, limit=limit, offset=offset, raw=raw)
        if raw:
            if len(pls["playlists"]["items"]) == 0:
                break
            playlists.append(pls["playlists"])
            offset += limit
            continue
        if not pls:
            break

        playlists += pls
        offset += limit
    return playlists



def get_user_favorites(user, fav_type, raw=False):
    '''
    Returns all user favorites

    Parameters
    ----------
    user: dict
        returned by qobuz.User
    fav_type: str
        favorites type: 'tracks', 'albums', 'artists'
    limi
    '''
    limit = 50
    offset = 0
    favorites = list()
    while True:
        favs = user.favorites_get(fav_type=fav_type, limit=limit, offset=offset, raw=raw)
        if not raw:
            if not favs:
                break
        else:
            count = len(favs[fav_type]["items"])
            if count == 0:
                break

        if raw:
            for _f in favs[fav_type]["items"]:
                favorites.append(_f)
        else:
            favorites += favs
        offset += limit
    return favorites



def get_all_tracks(playlist):
    '''
    Returns all tracks for a playlist

    Parameters
    ----------
    user: qobuz.User object
    '''
    limit = 50
    offset = 0
    tracks = list()
    while True:
        trks = playlist.get_tracks(limit=limit, offset=offset)
        if not trks:
            break
        tracks += trks
        offset += limit
    return tracks



def qobuz_myplaylists(user, args, log):
    '''
    Get and displays my playlists
    '''
    log.info('get all playlists...')
    if args.type == 'all':
        args.type = 'owner,subscriber'
    playlists = get_user_playlists(user, args.type, args.raw)
    log.info('... done')
    if args.raw:
        print(json.dumps(playlists, indent=4))
        return
    for playlist in playlists:
        if args.name and args.name.lower() != playlist.name.lower():
            log.info('skip playlist "%s"', playlist.name)
            continue

        log.info('get playlist tracks...')
        tracks = playlist.get_tracks()
        log.info('...done')

        log.info('compute total duration...')
        duration = 0
        for track in tracks:
            duration += track.duration
        log.info('...done')

        print('Playlist: "{}", description: "{}", public: {}, collaborative: {}, duration: {}, id: {}'.\
            format(playlist.name, playlist.description, playlist.public, playlist.collaborative, seconds_tostring(playlist.duration), playlist.id))

        if args.no_tracks:
            continue

        log.info('display playlist tracks...')
        fmt = '    %8s | %-40s | %-50s | %-50s | %10s | %s'
        print_header(fmt, ('#idTrack', 'Artist', 'Album', 'Title', 'Track', 'Duration'))
        if args.sort:
            tracks.sort(key=lambda x: x.artist.name + x.album.title)
        for track in tracks:
            log.info('display track')
            print(fmt % (track.id, track.artist.name, track.album.title, track.title, '%s/%s' % (track.track_number, track.album.tracks_count), seconds_tostring(track.duration)))
            if args.performers:
                for performer in track.performers:
                    print('        -> {}'.format(performer))
        log.info('... done')
        print()



def qobuz_myfavorites(user, args, log):
    '''
    Get and displays favorites
    '''
    if args.type in ['tracks', 'all']:
        print('Favorites Tracks')
        fmt = '    %8s | %-40s | %-50s | %-50s | %10s | %10s'
        print_header(fmt, ('#idTrack', 'Artist', 'Album', 'Title', 'Track', 'Duration'))
        log.info('get all favorites...')
        tracks = get_user_favorites(user, 'tracks', args.raw)
        log.info('... done')
        if args.raw:
            print(json.dumps(tracks, indent=4))
        else:
            tracks.sort(key=lambda x: x.artist.name + x.album.title)
            for track in tracks:
                log.info('display track')
                print(fmt % (track.id, track.artist.name, track.album.title, track.title, '%s/%s' % (track.track_number, track.album.tracks_count), seconds_tostring(track.duration)))
                if args.performers:
                    for performer in track.performers:
                        print('        -> {}'.format(performer))
                if args.cover:
                    download_album_image(track.album)
            log.info('display done')
        print()

    if args.type in ['albums', 'all']:
        print('Favorites Albums')
        fmt = '    %13s | %-40s | %-50s | %10s | %10s'
        print_header(fmt, ('#idAlbum', 'Artist', 'Album', 'Tracks', 'Parution'))
        log.info('get all favorites albums...')
        albums = get_user_favorites(user, 'albums', args.raw)
        log.info('... done')
        if args.raw:
            print(json.dumps(albums, indent=4))
        else:
            albums.sort(key=lambda x: x.artist.name)
            for album in albums:
                log.info('display album')
                print(fmt % (album.id, album.artist.name, album.title, '%s tracks' % album.tracks_count, timestamp_tostring(album.released_at)))
                if args.cover:
                    download_album_image(album)
            log.info('display done')
        print()

    if args.type in ['artists', 'all']:
        print('Favorites Artists')
        fmt = '    %9s | %-40s | %10s'
        print_header(fmt, ('#idArtist', 'Artist', 'Albums'))
        log.info('get all favorites artists...')
        artists = get_user_favorites(user, 'artists', args.raw)
        log.info('... done')
        if args.raw:
            print(json.dumps(artists, indent=4))
        else:
            artists.sort(key=lambda x: x.name)
            for artist in artists:
                log.info('display artist')
                print(fmt % (artist.id, artist.name, artist.albums_count))
        print()



def qobuz_mod_playlist(user, args, log):
    '''
    Modify playlist(s)
    '''
    # Before creating a playlist we need to check if the name already exists.
    # This avoid to have several playlist with the same name
    # So load our playlists :
    log.info('get current playlists')
    current_playlists = {p.name.lower():p.id for p in get_user_playlists(user, 'owner')}
    log.info('current playlists : %s', current_playlists)

    # read playlist source file
    #
    if not os.path.isfile(args.track_file):
        print('FAILED: file "{}" not found'.format(args.track_file))
        return
    # use regular expressions conform to qobuz_myplaylists output
    re_pldesc = re.compile(r'^Playlist: "(.+)", description: "(.+)", public: (\w+), collaborative: (\w+)')
    re_idtrk = re.compile(r'^ *(\d+)')
    playlists = dict()
    playlist_name = None
    for line in open(args.track_file, encoding='utf8'):
        #print(line)
        match = re_pldesc.match(line)
        if match:
            playlist_name = match.group(1)
            playlists[playlist_name] = {
                'description': match.group(2),
                'public': match.group(3) == 'True',
                'collaborative' :match.group(4) == 'True',
                'tracks': list()
            }
            continue
        match = re_idtrk.match(line)
        if match:
            if not playlist_name:
                print('ERROR : id found without playlist declared')
            playlists[playlist_name]['tracks'].append(int(match.group(1)))
    log.info('playlist file "%s" loaded', args.track_file)

    # finally create, modify playlists
    #
    for name, playlist in playlists.items():
        log.info('Add playlist "%s" : %s', name, playlist)
        if name.lower() in current_playlists.keys():
            if args.recreate:
                # delete and re-create
                done = user.playlist_delete(current_playlists[name.lower()])
                if not done:
                    print('FAILED to delete playlist "{}"'.format(name))
                    continue
                id_playlist = user.playlist_create(name, playlist['description'], int(playlist['public']), int(playlist['collaborative'])).id
            else:
                print('Add track to existing playlist "{}"'.format(name))
                id_playlist = current_playlists[name.lower()]
                #print('FAILED: a playlist "{}" already exists'.format(name))
        else:
            # create new playlist
            id_playlist = user.playlist_create(name, playlist['description'], int(playlist['public']), int(playlist['collaborative'])).id

        # add tracks not already in playlist
        playlist_work = qobuz.Playlist.from_id(id_playlist, user)
        current_tracks = [t.id for t in get_all_tracks(playlist_work)]
        tracks_to_add = list()
        for track in playlist['tracks']:
            if not track in current_tracks:
                tracks_to_add.append(track)
        log.info('Add tracks %s', tracks_to_add)
        playlist_work.add_tracks(tracks_to_add, user)



def qobuz_mod_favorites(user, action, args, log):
    '''
    Modify favorites(s)
    '''
    # read playlist source file
    #
    log.info('Favorites %s', action)
    if not os.path.isfile(args.fav_file[0]):
        print('FAILED: file "{}" not found'.format(args.fav_file[0]))
        return
    #
    # use regular expression for simple id at the begin of line
    re_section = re.compile(r'^Favorites (\w+)')
    re_idfav = re.compile(r'^ *([\d\w]+)')
    section = None
    favorites = {'Artists':list(), 'Albums':list(), 'Tracks':list()}
    for line in open(args.fav_file[0], encoding='utf8'):
        match = re_section.match(line)
        if match:
            if not match.group(1) in ['Artists', 'Albums', 'Tracks']:
                print('ERROR : favorites section unkwown : "{}"'.format(match.group(1)))
                return
            section = match.group(1)
            continue
        match = re_idfav.match(line)
        if match:
            if not section:
                print('ERROR : missing favorites section')
            favorites[section].append(match.group(1))
    log.info('Favorites fromfile "%s" to %s : %s', args.fav_file[0], action, favorites)

    result = False
    if action == 'add':
        result = user.favorites_add(albums=favorites['Albums'], tracks=favorites['Tracks'], artists=favorites['Artists'])
    elif action == 'del':
        result = user.favorites_del(albums=favorites['Albums'], tracks=favorites['Tracks'], artists=favorites['Artists'])
    if not result:
        print('FAILED')





def main():
    ''' Main program entry '''
    #
    # commands parser
    #
    parser = ArgumentParser(description='Various commands around Qobuz catalog',\
                                     formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--log', help='log on file')

    # create subparsers
    subparsers = parser.add_subparsers(help=': availables commands', dest='command')

    # parser get playlists
    subparser = subparsers.add_parser(
        'playlists',
        description='Retrieves user playlists',
        help=': retrieves and displays user playlists')
    subparser.add_argument('--name', help='Filter playlists on this name')
    subparser.add_argument('--type', choices=['owner', 'subscriber', 'all'], help='Type of playlist : "owner", "subscriber" or "all". (default=%(default)s)', default='owner')
    subparser.add_argument('--sort', action='store_true', help='Sort tracks on "artist" and "album"')
    subparser.add_argument('--performers', action='store_true', help='Displays performers for tracks')
    subparser.add_argument('--no-tracks', action='store_true', help='Don\'t display tracks')
    subparser.add_argument('--raw', action='store_true', help='Displays json structure only')

    # parser set playlists
    subparser = subparsers.add_parser(
        'playlists-set',
        description='modify (add tracks) or create playlist(s) from a source file.\n'\
            'Source files have same format as the outputs of commands "favorites" or "playlist"',
        help=': modify (add tracks) or create playlist(s) from a source file',
        formatter_class=RawDescriptionHelpFormatter)
    subparser.add_argument('--recreate', action='store_true', help='Recreate playlist if name already exists (means delete/create steps)')
    subparser.add_argument('track_file', nargs='?', help='File source for tracks to add. Contains playlist name, and, at least track id')

    # parser get favorites
    subparser = subparsers.add_parser(
        'favorites',
        description='Retrieves user favorites',
        help=': retrieves and displays user favorites')
    subparser.add_argument('--type', help='Type of favorites to retrieve', \
                    choices=['tracks', 'albums', 'artists', 'all',], default='all')
    subparser.add_argument('--cover', action='store_true', help='Download album cover image. Destination and size is specified in "config.json"')
    subparser.add_argument('--performers', action='store_true', help='Displays performers for tracks')
    subparser.add_argument('--raw', action='store_true', help='Print json structure')

    # parser add favorites
    subparser = subparsers.add_parser(
        'favorites-add',
        description='Add favorites',
        help=': add favorites',
        formatter_class=RawDescriptionHelpFormatter)
    subparser.add_argument('fav_file', nargs=1, help='File source for favorites to add')

    # parser del favorites
    subparser = subparsers.add_parser(
        'favorites-del',
        description='Delete favorites',
        help=': delete favorites',
        formatter_class=RawDescriptionHelpFormatter)
    subparser.add_argument('fav_file', nargs=1, help='File source for favorites to add')

    # parse arguments
    args = parser.parse_args()

    # logging
    if args.log:
        # basicConfig doesn't support utf-8 encoding yet (?)
        #   logging.basicConfig(filename=args.log, level=logging.INFO, encoding='utf-8')
        # use work-around :
        log = logging.getLogger()
        log.setLevel(logging.INFO)
        handler = logging.FileHandler(args.log, 'a', 'utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        log.addHandler(handler)
    log = logging.getLogger()
    log.info('myqobuz start')

    # register qobuz app
    qobuz.api.register_app(MYCONFIG['login']['app_id'], MYCONFIG['login']['app_secret'])

    # prepare qobuz authentification
    log.info('login...')
    user = qobuz.User(MYCONFIG['login']['email'], MYCONFIG['login']['password'])
    log.info('... done')


    if args.command == 'favorites':
        qobuz_myfavorites(user, args, log)

    if args.command == 'favorites-add':
        qobuz_mod_favorites(user, 'add', args, log)

    if args.command == 'favorites-del':
        qobuz_mod_favorites(user, 'del', args, log)

    if args.command == 'playlists':
        qobuz_myplaylists(user, args, log)

    if args.command == 'playlists-set':
        qobuz_mod_playlist(user, args, log)

    log.info('myqobuz end')



if __name__ == '__main__':
    # protect main from IOError occuring with a pipe command
    try:
        main()
    except IOError as _e:
        if _e.errno not in [22, 32]:
            raise _e
