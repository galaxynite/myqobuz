# myqobuz

Get or Set Qobuz playlists and favorites from command line

Use a forked version of [python-qobuz](https://github.com/fdenivac/python-qobuz) module.

The myqobuz script and ""python-qobuz"" library needs a valid APP_ID and APP_SECRET. Both id and secret can be requested from [api@qobuz.com](mailto:api@qobuz.com).
You can also have a look on [Spoofbuz](https://github.com/DashLt/Spoofbuz).<br>


# Installation
- Download [python-qobuz](https://github.com/fdenivac/python-qobuz), 
- Install the "*qobuz*" directory in python *site-packages*, or anywhere and in this case you have to fill "qobuz_module" field of myqobuz "*config.json*"
- Download myqobuz script and install it anywhere
- Prepare config file ''config.json'' :
```
    {
        "login":{
            "app_id": "YOUR_APP_ID",
            "app_secret": "YOUR_APP_SECRET",
            "email": "YOUR_EMAIL",
            "password": "YOUR_PASSWORD"
        },
        "qobuz_module": "D:\\Devs\\python-qobuz\\src"
    }
```

# Usage

Archive personal playlists and favorites :
``` 
myqobuz.py playlists > my_all_playlists.txt
myqobuz.py favorites > all_my_favorites.txt
```

Restore them :
``` 
myqobuz.py playlists-add --replace all_my_playlists.txt
myqobuz.py favorites-add  all_my_favorites.txt
```

Remove some tracks for a playlist :
- copy a previous output (*my_all_playlists*) to '*tracks_to_remove.txt*'
- modify this keeping only tracks to remove
The '*tracks_to_remove.txt*' file (only track id are mandatory):
```
        Playlist: "MyJazz", description: "", public: False, collaborative: False
          13757514 | Jan Garbarek                             | Atmos                                              | Atmos 
          40071709
        Playlist: "MyRock", description: "", public: False, collaborative: False
          23265470
```
And remove tracks:
``` 
myqobuz.py playlists-del tracks_to_remove.txt
```

Create a new playlist :
- Prepare a new file '*myselection.txt*':
```
    Playlist: "A new selection", description: "My preferred song", public: False, collaborative: False
      66370200 | Nils Landgren | 4 Wheel Drive Live | Lobito 
      631787   | Nick Drake  | Five Leaves Left  | River Man 
```
- and create :
``` 
myqobuz.py playlists-add  myselection.txt
```
