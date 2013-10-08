#coding: UTF-8
VERSION="1.07"
import Tkinter as tk
import tkFont
import random
import os
import os.path
import sys
import traceback
import time
import mp3play
import threading



class Playthread(threading.Thread):
    def __init__(self,player):
        threading.Thread.__init__(self)
        self.sema=threading.Semaphore()
        self.inittime=time.time()
        self.player=player
        self.volume=100
        self.tracks=[]
        self.vols=[]
        self.nexttrack=None
        self.nexttrackname=None
        self.currenttrack=None
        self.alttrack=None
        self.pleaseplay=False
        self.pleasealtplay=False
        self.pleasenext=False
        self.pleasestop=False
        self.pleasepause=False
        self.pleaseunpause=False
        self.pleasevolume=False
        self.pleasealt=False
        self.pleaseexit=False
        self.playing=False
        self.paused=False
        self.altplaying=False
        self.exiting=False
        self.idle=True
        self.parallel=False
        self.start()
    def run(self):
        failedloads=0
        while 1:
            time.sleep(.016)
            self.sema.acquire()
            if self.pleaseunpause and self.paused:
                print "unpausing"
                for track in self.tracks:
                    track.unpause()
                self.pleaseunpause=False
                self.playing=True
                self.paused=False
                self.idle=False
            if self.pleasevolume is not False:
                print "setting volume:",self.pleasevolume
                if self.pleasevolume<self.volume:
                    for v in range(1,self.volume-self.pleasevolume+1):
                        for track in self.tracks:
                            track.volume(self.volume-v)
                        if self.alttrack!=None:
                            self.alttrack.volume(self.volume-v)
                        time.sleep(0.01)
                if self.pleasevolume>self.volume:
                    for v in range(1,self.pleasevolume-self.volume+1):
                        for track in self.tracks:
                            track.volume(self.volume+v)
                        if self.alttrack!=None:
                            self.alttrack.volume(self.volume+v)
                        time.sleep(0.01)
                self.volume=self.pleasevolume
                self.pleasevolume=False
            if self.pleasepause and self.playing:
                print "pausing"
                for track in self.tracks:
                    track.pause()
                if self.alttrack!=None:
                    self.alttrack.pause()
                self.pleasepause=False
                self.paused=True
                self.playing=False
                self.idle=False
            if self.pleasestop and self.playing:
                print "stopping"
                for track in self.tracks:
                    track.stop()
                if self.alttrack!=None:
                    self.alttrack.pause()
                self.pleasestop=False
                self.idle=True
                self.playing=False
                self.paused=False
            if self.pleaseplay:
                print "playing",self.pleaseplay
                if self.nexttrackname==self.pleaseplay:
                    self.currenttrack=self.nexttrack
                else:
                    try:
                        self.tracks.append(mp3play.load(self.pleaseplay))
                    except:
                        traceback.print_tb(sys.exc_info()[2])
                        self.sema.release()
                        time.sleep(0.5)
                        failedloads+=1
                        if failedloads>=10:
                            self.player.echo("There was a problem playing back %s."%self.pleaseplay[len(self.player.pwd):])
                            self.player.never(self.pleaseplay)
                            failedloads=0
                        continue
                    self.currenttrack=self.tracks[-1]
                if self.pleasealtplay:
                    try:
                        self.alttrack=mp3play.load(self.pleasealtplay)
                    except:
                        self.player.echo("Loading alternative track (%s) failed."%self.pleasealtplay[len(self.player.pwd):])
                        traceback.print_tb(sys.exc_info()[2])
                        self.sema.release()
                else:
                    self.alttrack=None
                self.vols.append(self.volume)
                self.currenttrack.volume(self.volume)
                if self.alttrack!=None:
                    self.alttrack.volume(0)
                    self.alttrack.play()
                self.currenttrack.play()
                self.pleaseplay=False
                self.pleasealtplay=False
                self.playing=True
                self.altplaying=False
                self.paused=False
                self.idle=False
            if self.pleasealt:
                if self.altplaying:
                    for v in range(1,self.volume+1):
                        self.alttrack.volume(self.volume-v)
                        self.currenttrack.volume(v)
                        time.sleep(0.02)
                else:
                    for v in range(1,self.volume+1):
                        self.currenttrack.volume(self.volume-v)
                        self.alttrack.volume(v)
                        time.sleep(0.02)
                self.altplaying^=True
                self.pleasealt=False
            if self.pleasenext:
                try:
                    self.nexttrack=mp3play.load(self.pleasenext)
                    self.nexttrackname=self.pleasenext
                    self.tracks.append(self.nexttrack)
                    self.vols.append(self.volume)
                    print self.nexttrackname,"appended to self.tracks"
                    self.pleasenext=False
                except:
                    traceback.print_tb(sys.exc_info()[2])
                    self.sema.release()
                    time.sleep(0.5)
                    a+=1
                    if a==10:
                        self.player.echo("There was a problem loading %s."%self.pleaseplay[len(self.player.pwd):])
                        self.player.never(self.pleaseplay)
                        a=0
                    continue
            if self.playing and not self.currenttrack.isplaying():
                self.player.writetrackfile()
                self.sema.release()
                self.player.play()
                self.sema.acquire()
                if not self.pleaseexit and self.player.nowplaying:
                    self.player.echo("Now playing: "+self.player.nowplaying[len(self.player.pwd):])
            if self.pleaseexit:
                self.exiting=True
                self.currenttrack=None
            for i,track in enumerate(self.tracks):
                if track!=self.currenttrack:
                    if not track.isplaying() and track is not self.nexttrack:
                        try:
                            del self.tracks[i]
                            del self.vols[i]
                        except IndexError:
                            continue
                    elif not self.parallel or self.idle or self.exiting:
                        self.vols[i]-=1
                        if self.vols[i]<0:
                            self.vols[i]=0
                        track.volume(self.vols[i])
                        if self.vols[i]==0:
                            track.stop()
            if self.exiting and not any([track.isplaying() for track in self.tracks]):
                self.sema.release()
                break
            self.sema.release()


class TrackdataEntry:
    def __init__(self,tags=[],prob=100):
        self.tags=tags
        self.prob=prob
        self.curprob=prob


class Mush:
    def __init__(self,name=None):
        self.version=VERSION
        self.volume=100
        self.muted=0
        self.playthread=Playthread(self)
        self.orderedplay=False
        self.delconfirm=None
        self.keysuppress=False
        self.window=tk.Tk()
        if name:
            self.window.title(name)
        else:
            self.window.title("mush "+VERSION)
        self.font=tkFont.Font(family="Consolas",size=10)
        self.height=50
        self.width=80
        self.cmdhistlength=16
        self.outputhistlength=512
        self.maxviewpos=self.outputhistlength-self.height
        self.viewpos=self.maxviewpos
        self.cmdhist=[""]*self.cmdhistlength
        self.body=tk.Text(self.window,bg="black",fg="white",width=self.width,height=self.height,font=self.font,insertbackground="black",relief="flat",state="disabled")
        self.body.tag_config("green",foreground="green")
        self.body.tag_config("red",foreground="red")
        self.body.grid(row=0,column=0)
        self.cmdline=tk.Entry(bg="black",fg="white",insertbackground="white",width=self.width,font=self.font,relief="flat")
        self.cmdline.grid(row=1,column=0,columnspan=2,sticky="ew")
        self.cmdline.focus()
        self.cmdline.bind("<KeyPress>",self.cmdlinepress)
        self.cmdline.bind("<KeyRelease>",self.cmdlinerelease)
        self.body.bind("<ButtonRelease>",self.cmdlinefocus)
        self.readtrackfile()
        self.readaltfile()
        self.readcfgfile()
        self.pwd=os.path.expandvars(self.cfgdata["musicfolder"])
        self.playedthissession=[]
        self.tracklist=[]
        self.playlist=[]
        self.dontplaytags=[]
        self.playtags=[]
        self.nowplaying=None
        self.nexttrack=None
        self.choicelist=None
        self.repeat=False
        self.maketracklist()
        self.makeplaylist()
        self.trackindex=0
        self.restrictedplaylist=False
        self.greet()
        self.alive=True
        self.window.mainloop()
    def readtrackfile(self):
        trackfile=open("tracks.dat")
        backupfile=open("#tracks.dat#","w")
        self.trackdata={}
        self.trackdata["#"]=[]
        for line in trackfile.readlines():
            if line[0]!="#" and line[:4]!="\xef\xbb\xbf#":
                path,tags,prob=line.split("|")
                self.trackdata[path]=TrackdataEntry(tags=[tag.lower() for tag in tags.split(";") if tag],prob=int(prob))
            else:
                self.trackdata["#"].append(line)
                if "total played" in line:
                    self.playedtotal=int(line.split(": ")[-1][:-1])
            backupfile.write(line)
        backupfile.close()
        trackfile.close()
    def writetrackfile(self):
        trackfile=open("tracks.dat","w")
        for line in self.trackdata["#"]:
            if "total played" in line:
                line=": ".join(line.split(": ")[:-1]+[str(self.playedtotal)+"\n"])
            trackfile.write(line)
        for track in sorted(self.trackdata.keys()):
            if track!="#" and (self.trackdata[track].tags or self.trackdata[track].prob!=100):
                trackfile.write(track+"|")
                trackfile.write(";".join(self.trackdata[track].tags).encode("latin-1")+"|")
                trackfile.write(str(self.trackdata[track].prob)+"\n")
        trackfile.close()
    def readaltfile(self):
        altfile=open("alts.dat")
        self.altdata={}
        j=1
        lines=[line.strip() for line in altfile.readlines() if line.strip()]
        for i in range(len(lines)):
            self.altdata[lines[i]]=lines[i+j]
            j*=-1
        altfile.close()
    def readcfgfile(self):
        cfgfile=open("mush.cfg")
        self.cfgdata={"musicfolder":"%userprofile%/Music"}
        for line in cfgfile.readlines():
            if ":" in line:
                line=line.split(":")
                self.cfgdata[line[0].strip()]=line[1].strip()
        cfgfile.close()
    def never(self,track):
        self.trackdata[track].prob=0
        self.echo(track[len(self.pwd):]+" will not be played again.")
        self.play()
        self.echo("Now playing: "+self.nowplaying[len(self.pwd):])
    def cmdlinefocus(self,event):
        self.cmdline.focus_set()
    def cmdlinepress(self,event):
        if self.delconfirm:
            if event.keycode==89:
                self.outputhist[-1]+=" y"
                self.keysuppress=True
                self.stop()
                self.never(self.delconfirm)
                self.delconfirm=None
            else:
                self.outputhist[-1]+=" n"
                self.keysuppress=True
                self.echo()
                self.delconfirm=None
        elif event.keycode==13:
            cmd=self.cmdline.get()
            if not cmd:
                return
            self.cmdline.delete(0,len(cmd))
            ret=self.parse(cmd)
            if self.alive:
                if ret=="silent":
                    pass
                elif ret:
                    self.echo(cmd+u" ✔")
                else:
                    self.echo(cmd+u" ✘")
                if self.cmdout:
                    self.echo(self.cmdout)
            self.cmdhist.pop(0)
            if cmd:
                self.cmdhist.append(cmd)
            self.cmdhistpos=0
        elif event.keycode==122:
            exec self.cmdline.get().encode("latin-1")
    def cmdlinerelease(self,event):
        if self.keysuppress:
            self.keysuppress=False
            self.cmdline.delete(-1,1)
    def parse(self,cmd):
        u"""
List of available commands:                                                      ✔
   help      ?          Displays this help                                       ✔
------------------------NAVIGATION-----------------------------------------------✔
             cd         Changes between folders                                  ✔
             pwd        Shows the current folder                                 ✔
             ls         Lists all available music/subfolders here                ✔
------------------------PLAYBACK COMMANDS----------------------------------------✔
   play      p          Plays music randomly from the current folder             ✔
                        (including subfolders)                                   ✔
   play      p -o       Plays music from the current folder in order             ✔
                        (including subfolders)                                   ✔
   play      p  <file>  Plays a specific track by filepath or part of path       ✔
   play      p <index>  Plays a specific track by its index in the playlist      ✔
   pause     p          Stops playing to be resumed later                        ✔
   unpause   p          Resumes playing from pause (play does the same)          ✔
   stop      s          Stops playing entirely                                   ✔
   next      n          Skips the currently playing track and randoms a new one  ✔
   next      n  <file>  Skips the currently playing track and                    ✔
                        goes to the specified one                                ✔
   next      n <number> Skips <number> slots ahead in the playlist               ✔
   nexttrack nt <file>  Sets the next played track without immediately skipping  ✔
   playnext  pn         Alias for nexttrack                                      ✔
   repeat    r   on     Turns on repeat (for just this track)                    ✔
   repeat    r  off     Turns off repeat                                         ✔
   repeat    r          Toggles repeat on/off)                                   ✔
   volume    v          Sets the volume [0-100]                                  ✔
   mute      m          Mutes playback temporarily                               ✔
   unmute    m          Unmutes playback again                                   ✔
   alt                  Switches to alternate version of track if available      ✔
------------------------PLAYLIST MANAGEMENT--------------------------------------✔
   order     o   on     Turns on track ordering                                  ✔
   order     o  off     Turns off track ordering                                 ✔
   order     o          Toggles track ordering on/off                            ✔
   parallel             Enables parallel playing of tracks (current track won't  ✔
                        stop if another one is played)                           ✔
   like      l          Remembers the currently playing track and plays it       ✔
                        more often in the future                                 ✔
   dislike   dl         Remembers the currently playing track and plays it       ✔
                        less often in the future                                 ✔
   never                Remembers the currently playing track and                ✔
                        NEVER FUCKING PLAY IT AGAIN IT SUCKS (with confirmation) ✔
   prob        <number> Sets the Relative Playing Probability of the             ✔
                        currently playing track                                  ✔
   tag       t  <tag>   Sets a tag for the currently playing track               ✔
   untag     ut <tag>   Removes a tag from the currently playing track           ✔
   playtag   pt <tag>   Plays music from among tracks with this tag;             ✔
                        you can specify multiple tags using ";" as delimiter     ✔
   playtag   pt   *     Plays music from among all tagged tracks                 ✔
------------------------INFORMATION----------------------------------------------✔
   tracklist tl         Shows a list of all tracks in the current folder         ✔
                        and its subfolders                                       ✔
   playlist  pl         Shows a list of all tracks currently eligible for play   ✔
   listtags  lt         Shows a list of all available tags                       ✔
   nowplaying np        Shows the currently playing track                        ✔
   info                 Shows some information about the current folder and      ✔
                        track                                                    ✔
   stats                Shows stats about the track database and total           ✔
                        tracks played                                            ✔
   tag       t          Displays all tags for the currently playing track        ✔
   prob                 Displays the Relative Playing Probability of the         ✔
                        currently playing track                                  ✔
   version              Diplays the current version of the player                ✔
   quit      q          Quits the player                                         ✔
     """
        self.cmdout=""
        allcaps=False
        if cmd==cmd.upper() and len(cmd)>3:
            allcaps=True
        if " " in cmd:
            cmd,arg=cmd.split(" ",1)
        else:
            arg=None
        self.playthread.sema.acquire()
        self.paused=self.playthread.paused
        self.playing=self.playthread.playing
        self.idle=self.playthread.idle
        self.parallel=self.playthread.parallel
        self.playthread.sema.release()
        if self.choicelist:
            if cmd in ["1","2","3","4","5","6","7","8","9"]and int(cmd)<len(self.choicelist):
                if self.choicelist[0]=="play":
                    return self.canyouplay(self.choicelist[int(cmd)])
                elif self.choicelist[0]=="next":
                    self.nexttrack=self.choicelist[int(cmd)]
                    self.echo("The next played track will be %s"%self.nexttrack)
                    self.playthread.sema.acquire()
                    self.playthread.pleasenext=self.nexttrack
                    self.playthread.sema.release()
                    return True
                else:
                    self.cmdout="Something weird happened with the choice list :("
            self.choicelist=None
        if allcaps:
            return self.cmd_allcaps(arg)
        try:
            return {"help":       self.cmd_help,       "?":        self.cmd_help,
                    "play":       self.cmd_play,
                    "p":          self.cmd_playpause,
                    "pause":      self.cmd_pause,
                    "unpause":    self.cmd_unpause,
                    "s":          self.cmd_stop,       "stop":     self.cmd_stop,
                    "n":          self.cmd_next,       "next":     self.cmd_next,
                    "nexttrack":  self.cmd_nt,         "nt":       self.cmd_nt,        "playnext":      self.cmd_nt,      "pn": self.cmd_nt,
                    "repeat":     self.cmd_repeat,     "r":        self.cmd_repeat,
                    "mute":       self.cmd_mute,
                    "unmute":     self.cmd_unmute,
                    "m":          self.cmd_muteunmute,
                    "alt":        self.cmd_alt,
                    "volume":     self.cmd_volume,     "v":        self.cmd_volume,
                    "order":      self.cmd_order,      "o":        self.cmd_order,
                    "parallel":   self.cmd_parallel,
                    "like":       self.cmd_like,       "good":     self.cmd_like,      "l":             self.cmd_like,    "+": self.cmd_like,
                    "dislike":    self.cmd_dislike,    "bad":      self.cmd_dislike,   "dl":            self.cmd_dislike, "-": self.cmd_dislike,
                    "never":      self.cmd_never,      "nope":     self.cmd_never,     "--":            self.cmd_never,   "---": self.cmd_never,
                    "prob":       self.cmd_prob,
                    "t":          self.cmd_tag,        "tag":      self.cmd_tag,       "tags":          self.cmd_tag,
                    "untag":      self.cmd_untag,      "ut":       self.cmd_untag,
                    "pt":         self.cmd_playtag,    "playtag":  self.cmd_playtag,
                    "cd":         self.cmd_cd,         "chdir":    self.cmd_cd,
                    "ls":         self.cmd_ls,         "listdir":  self.cmd_ls,
                    "pwd":        self.cmd_pwd,
                    "tracklist":  self.cmd_tracklist,  "tl":       self.cmd_tracklist,
                    "playlist":   self.cmd_playlist,   "pl":       self.cmd_playlist,
                    "taglist":    self.cmd_taglist,    "listtags": self.cmd_taglist,   "lt":            self.cmd_taglist,
                    "newlist":    self.cmd_newlist,    "nl":       self.cmd_newlist,   "listnewtracks": self.cmd_newlist, "newtracks": self.cmd_newlist,
                    "quit":       self.cmd_quit,       "exit":     self.cmd_quit,
                    "q":          self.cmd_quit,
                    "unicorn":    self.cmd_unicorn,
                    "nowplaying": self.cmd_nowplaying, "np":       self.cmd_nowplaying,
                    "stats":      self.cmd_stats,
                    "info":       self.cmd_info}[cmd.lower()](arg)
        except KeyError:
            self.cmdout="I don't know what "+cmd+" means :("
            return False
    def cmd_help(self,arg):
        self.cmdout="\n".join([l[:self.width] for l in self.parse.__doc__.split("\n") if u"✔" in l])
        return True
    def cmd_play(self,arg):
        if self.restrictedplaylist:
            self.makeplaylist()
            self.restrictedplaylist=False
        if arg is not None:
            try:
                arg=int(arg)
                arg%=len(self.playlist)
            except ValueError:
                pass
        elif self.paused:
            self.unpause()
            return True
        return self.play(arg)
    def cmd_playpause(self,arg):
        if (not self.playthread.currenttrack) or arg is not None:
            return self.play(arg)
        elif self.playing:
            self.pause()
        elif self.paused:
            self.unpause()
        else:
            return self.play(arg)
        return True
    def cmd_pause(self,arg):
        if self.playing:
            self.pause()
            return True
        else:
            self.cmdout="I'm not playing at the moment!"
            return False
    def cmd_unpause(self,arg):
        if self.paused:
            self.unpause()
            return True
        else:
            if self.idle:
                self.cmdout="There's nothing to resume!"
            elif self.playing:
                self.cmdout="I'm already playing!"
            return False
    def cmd_stop(self,arg):
        if self.playing:
            self.stop()
            return True
        else:
            self.cmdout="I'm not playing at the moment!"
            return False
    def cmd_next(self,arg):
        if self.playing or self.paused:
            if arg is not None:
                try:
                    arg=int(arg)+self.trackindex
                    arg%=len(self.playlist)
                except ValueError:
                    pass
            return self.play(arg)
        else:
            self.cmdout="I'm not playing at the moment!"
            return False
    def cmd_nt(self,arg):
        if self.restrictedplaylist:
            self.makeplaylist()
            self.restrictedplaylist=False
        if arg is not None:
            if arg=="stop":
                self.nexttrack="stop"
                self.cmdout="Stopping after this track."
                return True
            elif arg=="quit":
                self.nexttrack="quit"
                self.cmdout="Quitting after this track."
                return True
            elif arg=="none":
                if self.nexttrack is not None:
                    self.nexttrack=self.getrandomtrack()
                    self.playthread.sema.acquire()
                    self.playthread.pleasenext=self.nexttrack
                    self.playthread.sema.release()
                    self.cmdout="Preference for next track unset."
                    return True
                else:
                    self.cmdout="There was no plan for the next track to begin with!"
                    return False
            elif arg=="random":
                self.nexttrack=self.getrandomtrack()
                self.playthread.sema.acquire()
                self.playthread.pleasenext=self.nexttrack
                self.playthread.sema.release()
                self.cmdout="Next played track randomized."
                return True
            if type(arg)==str:
                try:
                    arg=int(arg)
                    name=self.strsplit(self.playlist[arg])
                except ValueError:
                    name=self.strsplit(unicode(arg,"latin-1"))
            elif type(arg)==unicode:
                name=self.strsplit(arg)
            else:
                raise TypeError("Nexttrack specification is of type "+str(type(arg))+". This is weird.")
            matches=[]
            for i,track in enumerate(self.playlist):
                track=unicode(track,"latin-1")
                if all([s.lower().replace("_"," ") in track.lower().replace("_"," ") for s in name]):
                    matches.append(track)
            if len(matches)==1:
                self.nexttrack=matches[0]
                self.playthread.sema.acquire()
                self.playthread.pleasenext=self.nexttrack
                self.playthread.sema.release()
                self.cmdout="The next played track will be %s"%self.nexttrack[len(self.pwd):]
                return True
            elif 1<len(matches)<10:
                i=1
                self.echo("%d tracks were found. Press a number to select one of them."%len(matches))
                for match in matches:
                    self.echo(str(i)+" "+match[len(self.pwd):])
                    i+=1
                self.choicelist=["next"]+matches
                return "silent"
            elif len(matches)>=10:
                self.cmdout="Too many matches (%d) were found for your query. Please be more specific."%len(matches)
                return False
            else:
                self.cmdout="I couldn't find "+arg+" in the playlist :("
                return False
        else:
            self.cmdout="The next played track will be "+self.nexttrack[len(self.pwd):]
            return True
    def cmd_repeat(self,arg):
        if arg is None:
            self.repeat^=True
            self.cmdout="Repeat turned %s."%["off","on"][self.repeat]
            return True
        elif arg.lower() in ["on","1","true"]:
            if not self.repeat:
                self.repeat=True
                self.cmdout="Repeat turned on."
                return True
            else:
                self.cmdout="Repeat is already on."
                return False
        elif arg.lower() in ["off","0","false"]:
            if self.repeat:
                self.repeat=False
                self.cmdout="Repeat turned off."
                return True
            else:
                self.cmdout="Repeat is already off!"
                return False
        else:
            self.cmdout="What do you mean by "+arg+"? :("
            return False
    def cmd_mute(self,arg):
        if not self.muted:
            self.mute()
            return True
        self.cmdout="The volume is already at 0!"
        return False
    def cmd_unmute(self,arg):
        if self.muted:
            self.unmute()
            return True
        self.cmdout="You can hear me already!"
        return False
    def cmd_muteunmute(self,arg):
        if self.muted:
            self.unmute()
        else:
            self.mute()
        return True
    def cmd_volume(self,arg):
        if arg is None:
            self.cmdout="Volume is at "+str(self.volume)
            return True
        try:
            vol=int(arg)
        except ValueError:
            self.cmdout=arg+"doesn't look like a volume level to me :("
            return False
        self.volchange(vol)
        return True
    def cmd_alt(self,arg):
        if self.nowaltplaying:
            self.playthread.pleasealt=True
            self.cmdout+="Switching to %s"%[self.nowaltplaying,self.nowplaying][self.playthread.altplaying]
            return True
        else:
            self.cmdout+="No alternate track playing!"
            return False
    def cmd_order(self,arg):
        if arg is None:
            self.orderedplay^=True
            if self.orderedplay:
                self.makeplaylist()
                if self.nowplaying is None:
                    self.trackindex=0
                else:
                    self.trackindex=self.playlist.index(self.nowplaying)
                try:
                    self.nexttrack=self.playlist[self.trackindex+1]
                    print "order nexttrack"
                except IndexError:
                    self.nexttrack=self.playlist[0]
            else:
                self.nexttrack=self.getrandomtrack()
            self.cmdout="Tracks are now played %s order."%["out of","in"][self.orderedplay]
            return True
        elif arg.lower() in ["on","1","true"]:
            if not self.orderedplay:
                self.orderedplay=True
                self.cmdout="Tracks are now played in order."
                self.makeplaylist()
                try:
                    self.trackindex=self.playlist.index(self.nowplaying)
                except AttributeError:
                    self.trackindex=0
                try:
                    self.nexttrack=self.playlist[self.trackindex+1]
                    print "order nexttrack"
                except IndexError:
                    self.nexttrack=self.playlist[0]
                return True
            else:
                self.cmdout="Tracks are already played in order."
                return False
        elif arg.lower() in ["off","0","false"]:
            if self.orderedplay:
                self.orderedplay=False
                self.cmdout="Tracks are now played out of order."
                self.nexttrack=self.getrandomtrack()
                return True
            else:
                self.cmdout="Tracks are already played out of order."
                return False
        else:
            self.cmdout="What do you mean by "+arg+"? :("
            return False
    def cmd_parallel(self,arg):
        if arg is None:
            self.parallel^=True
            self.playthread.sema.acquire()
            self.playthread.parallel=self.parallel
            self.playthread.sema.release()
            self.cmdout="Parallel playing %s."%["disabled","enabled"][parallel]
            return True
        elif arg.lower() in ["on","1","true"]:
            if not self.parallel:
                self.playthread.sema.acquire()
                self.playthread.parallel=True
                self.playthread.sema.release()
                self.cmdout="Parallel playing enabled."
                return True
            else:
                self.cmdout="Parallel playing is already enabled!"
                return False
        elif arg.lower() in ["off","0","false"]:
            if self.parallel:
                self.playthread.sema.acquire()
                self.playthread.parallel=False
                self.playthread.sema.release()
                self.cmdout="Parallel playing disabled."
                return True
            else:
                self.cmdout="Parallel playing is already disabled!"
                return False
        else:
            self.cmdout="What do you mean by "+arg+"? :("
            return False
    def cmd_like(self,arg):
        if self.playing or self.paused:
            if arg is None:
                probinc=20
            else:
                try:
                    probinc=int(arg)
                except ValueError:
                    probinc=20
            self.cmdout="You are liking this track. I will play it more often."
            self.trackdata[self.nowplaying].prob+=probinc
            return True
        else:
            self.cmdout="I'm not currently playing anything!"
            return False
    def cmd_dislike(self,arg):
        if self.playing or self.paused:
            if arg is None:
                probdec=20
            else:
                try:
                    probdec=int(arg)
                except ValueError:
                    probdec=20
            self.trackdata[self.nowplaying].prob-=probdec
            if self.trackdata[self.nowplaying].prob<0:
                self.trackdata[self.nowplaying].prob=0
            self.cmdout="You are disliking this track. I will %s."%["play it less often","not play it anymore"][self.trackdata[self.nowplaying].prob==0]
            return True
        else:
            self.cmdout="I'm not currently playing anything!"
            return False
    def cmd_never(self,arg):
        if self.nowplaying:
            self.cmdout="Do you really want to never hear %s again? [y/n]"%self.nowplaying[len(self.pwd):]
            self.delconfirm=self.nowplaying
            return True
        else:
            self.cmdout="I'm not currently playing anything!"
            return False
    def cmd_prob(self,arg):
        if self.playing or self.paused:
            if arg is not None:
                try:
                    prob=int(arg)
                except ValueError:
                    prob=None
                if prob is not None:
                    self.trackdata[self.nowplaying].prob=prob
                    self.cmdout="Relative Playing Probability for %s set to %s."%(self.nowplaying[len(self.pwd):],prob)
                    return True
                else:
                    self.cmdout="This doesn't look like a number to me :("
                    return False
            else:
                self.cmdout="%s currently has a Relative Playing Probability of %s"%(self.nowplaying[len(self.pwd):],self.trackdata[self.nowplaying].prob)
                return True
        else:
            self.cmdout="I'm not currently playing anything!"
            return False
    def cmd_tag(self,arg):
        if self.playing or self.paused:
            if arg is not None:
                newtags=[]
                deltags=[]
                invalidtags=[]
                for tag in arg.split(";"):
                    if "|" in tag:
                        invalidtags.append(tag)
                    elif tag=="*":
                        invalidtags.append(tag)
                    elif tag and not tag[0]=="-" and tag not in self.trackdata[self.nowplaying].tags:
                        tag=tag.strip()
                        self.trackdata[self.nowplaying].tags.append(tag)
                        newtags.append(tag)
                    elif tag[1:]in self.trackdata[self.nowplaying].tags:
                        tag=tag.strip()
                        self.trackdata[self.nowplaying].tags.remove(tag[1:])
                        deltags.append(tag)
                if newtags:
                    self.cmdout='%s is now tagged %s%s'%(self.nowplaying[len(self.pwd):]," and ".join(['"%s"'%tag for tag in newtags]).replace(" and ",", ",len(newtags)-2),"."*(not deltags))
                    if any([tag in self.dontplaytags for tag in newtags]):
                        self.play()
                if deltags:
                    self.cmdout+='%s is no longer tagged %s.'%([" and",self.nowplaying[len(self.pwd):]][not newtags]," and ".join(['"%s"'%tag[1:] for tag in deltags]).replace(" and ",", ",len(deltags)-2))
                    if self.playtags and not any([tag in self.playtags for tag in self.trackdata[self.nowplaying].tags]):
                        self.play()
                if invalidtags:
                    if "*" in invalidtags:
                        self.cmdout+="\n"*bool(self.cmdout)+"The asterisk symbol is not allowed as a tag (use it to play tracks with any tags!)"
                    self.cmdout+=("\n"*bool(self.cmdout)+["T","Also, t"]["*" in invalidtags]+"he | symbol is not allowed in tags!")*(invalidtags!=["*"])+"\n"*(not bool(self.cmdout))
                if not (newtags+deltags):
                    self.cmdout+="No new tags given!"
                return True
            else:
                if self.trackdata[self.nowplaying].tags:
                    self.cmdout="This track is tagged %s"%(" and ".join(['"%s"'%tag for tag in self.trackdata[self.nowplaying].tags]).replace(" and ",", ",len(self.trackdata[self.nowplaying].tags)-2))
                else:
                    self.cmdout="This track has no tags."
                return True
        else:
            self.cmdout="I'm not currently playing anything!"
            return False
    def cmd_untag(self,arg):
        if self.playing or self.paused:
            if arg is not None:
                if arg in self.trackdata[self.nowplaying].tags:
                    self.trackdata[self.nowplaying].tags.remove(arg)
                    self.cmdout='%s is no longer tagged "%s."'%(self.nowplaying[len(self.pwd):],arg)
                    return True
                else:
                    self.cmdout="""%s doesn't have the tag "%s"!"""%(self.nowplaying[len(self.pwd):],arg)
                    return False
            else:
                self.cmdout="You didn't specify any tags to remove! :("
                return False
        else:
            self.cmdout="I'm not currently playing anything!"
            return False
    def cmd_playtag(self,arg):
        if arg is not None:
            tags=arg.split(";")
            moreplaytags=[]
            moredontplaytags=[]
            lessplaytags=[]
            lessdontplaytags=[]
            invalidtags=[]
            for tag in tags:
                if "|" in tag:
                    invalidtags.append(tag)
                elif tag=="*":
                    break
                elif tag[0]=="-":
                    if tag[1:] not in self.playtags:
                        self.dontplaytags.append(tag[1:])
                        moredontplaytags.append(tag[1:])
                    else:
                        self.playtags.remove(tag[1:])
                        lessplaytags.append(tag[1:])
                else:
                    if tag not in self.dontplaytags:
                        self.playtags.append(tag)
                        moreplaytags.append(tag)
                    else:
                        self.dontplaytags.remove(tag)
                        lessdontplaytags.append(tag)
            if self.makeplaylist():
                newtrack=False
                for tag in set(tags):
                    if tag[0]=="-":
                        tag=tag[1:]
                    if tag in invalidtags:
                        self.cmdout+='The tag "%s" is invalid because the | symbol is not allowed in tags!\n'%tag
                    elif tag=="*":
                        self.cmdout+="Now playing tracks out of the list of all tagged ones.\n"
                        break
                    elif tag in lessdontplaytags:
                        if tag in moreplaytags:
                            self.cmdout+='The tag "%s" is now no longer forbidden, but required.\n'%tag
                            if not newtrack and self.playing:
                                self.cmdout+="    The current track is not tagged with it, therefore I'm playing a new one.\n"
                                newtrack=True
                        else:
                            self.cmdout+='The tag "%s" is now no longer forbidden.\n'%tag
                    elif tag in lessplaytags:
                        if tag in moredontplaytags:
                            self.cmdout+='The tag "%s" is now no longer required, but forbidden.\n'%tag
                            if not newtrack and self.playing:
                                self.cmdout+="    The current track is tagged with it, therefore I'm playing a new one.\n"
                                newtrack=True
                        else:
                            self.cmdout+='The tag "%s" is now no longer required.\n'%tag
                    elif tag in moredontplaytags:
                        self.cmdout+='The tag "%s" is now forbidden for play.\n'%tag
                        if not newtrack and self.playing and tag in self.trackdata[self.nowplaying].tags:
                            self.cmdout+="    The current track is tagged with it, therefore I'm playing a new one.\n"
                            newtrack=True
                    elif tag in moreplaytags:
                        self.cmdout+='The tag "%s" is now required for play.\n'%tag
                        if not newtrack and self.playing and tag not in self.trackdata[self.nowplaying].tags:
                            self.cmdout+="    The current track is not tagged with it, therefore I'm playing a new one.\n"
                            newtrack=True
                    if self.nexttrack and self.nexttrack not in self.playlist:
                        self.nexttrack=self.getrandomtrack()
                if not self.playing or newtrack:
                    self.play()
                return True
            else:
                self.cmdout="There are no tracks with this %s in the playlist :("%["tag","combination of tags"][len(self.playtags)+len(self.dontplaytags)>1]
                return False
        elif self.playtags or self.dontplaytags:
            self.playtags=[]
            self.dontplaytags=[]
            self.cmdout="Playing without restrictions again."
            self.makeplaylist()
            return True
        else:
            self.cmdout="Give me some tags :("
            return False
    def cmd_cd(self,arg):
        if arg is None:
            self.cmdout="I need a folder name :("
            return False
        if arg=="..":
            if "/" in self.pwd:
                pwd=self.pwd
                while pwd[-1]!="/":
                    pwd=pwd[:-1]
                pwd=pwd[:-1]
                self.pwd=pwd
            else:
                self.cmdout="We are already at the top!"
                return False
        elif len(arg)>1 and arg[1]==":":
            try:
                os.listdir(arg)
                self.pwd=arg
            except WindowsError:
                self.cmdout="I don't know of this folder :("
                return False
        else:
            try:
                os.listdir(self.pwd+"/"+arg)
                self.pwd+="/"+arg
            except WindowsError:
                self.cmdout="I don't know of this folder :("
                return False
        self.cmdout="We are now in "+self.pwd
        self.maketracklist()
        return True
    def cmd_pwd(self,arg):
        self.cmdout="We are in "+self.pwd
        return True
    def cmd_ls(self,arg):
        filelist=os.listdir(self.pwd)
        for name in filelist:
            if not os.path.isdir(self.pwd+"/"+name) and not name[-4:]==".mp3":
                filelist.remove(name)
        if len(filelist)>self.height:
            maxlen=len(max(filelist,key=len))
            for i in range(len(filelist)):
                filelist[i]+=" "*(maxlen-len(filelist[i])+1)
            for i in range(self.height):
                for j in range(i,len(filelist),self.height):
                    filelist[i]+=(i!=j)*filelist[j]
        self.cmdout="\n".join(filelist[:self.height])
        return True
    def cmd_tracklist(self,arg):
        self.cmdout+="Tracks currently eligible for play:\n"
        self.cmdout+="\n".join(self.tracklist)
        return True
    def cmd_playlist(self,arg):
        self.cmdout+="Tracks currently eligible for play:\n"
        self.cmdout+="\n".join(self.playlist)
        return True
    def cmd_taglist(self,arg):
        if arg=="all":
            alltags=True
        else:
            alltags=False
        tags={}
        for track in self.playlist:
            if track in self.trackdata:
                for tag in self.trackdata[track].tags:
                    if tag in tags:
                        tags[tag]+=1
                    else:
                        tags[tag]=1
        taglist=sorted([tag for tag in tags.keys() if (tags[tag]>10 or alltags)],key=lambda t:tags[t],reverse=True)
        for tag in taglist:
            self.cmdout+="\n"+tag+" - "+str(tags[tag])
        return True
    def cmd_newlist(self,arg):
        if len(self.newtracks)==0:
            self.cmdout+="All tracks are tagged/rated."
            return True
        elif len(self.newtracks)>=self.height:
            self.echo(cmd+u" ✔")
            self.t=Tracklister(self,list=self.newtracks)
            return "silent"
        else:
            self.cmdout+="Tracks currently not tagged/rated:"
            self.cmdout+="\n".join(self.newtracks)
            return True
    def cmd_unicorn(self,arg):
        self.cmdout="Here, have a unicorn! ♥\n"+self.unicorn()
        return True
    def cmd_quit(self,arg):
        if arg in ["soon","after this song"]:
            self.playthread.sema.acquire()
            self.playthread.quitafterthis=True
            self.playthread.sema.release()
        self.quit()
        return True
    def cmd_nowplaying(self,arg):
        self.cmdout+="Now playing: %s\n"%self.nowplaying
        self.cmdout+="    Relative Playing Probability: %s\n"%self.trackdata[self.nowplaying].prob
        self.cmdout+="    Tags: %s\n"%" and ".join(['"%s"'%tag for tag in self.trackdata[self.nowplaying].tags]).replace(" and ",", ",len(self.trackdata[self.nowplaying].tags)-2)
        self.playthread.sema.acquire()
        length=self.playthread.currenttrack.seconds()
        self.playthread.sema.release()
        self.cmdout+="    Length: %d:%02d"%(length/60,length%60)
        return True
    def cmd_info(self,arg):
        self.cmdout="This is mush %s.\n"%self.version
        self.cmdout+="The current directory out of which I am playing tracks is %s.\n"%self.pwd
        if self.playing or self.paused:
            self.cmdout+="I am currently playing %s.\n"%self.nowplaying[len(self.pwd):]
        if self.paused:
            self.cmdout+="%s is currently on pause.\n"%self.nowplaying[len(self.pwd):]
        if self.idle:
            self.cmdout+="I am currently playing nothing.\n"
        if self.playtags or self.dontplaytags:
            if self.playtags==["*"]:
                self.cmdout+="Playing is currently restricted to tagged tracks with any combination of tags.\n"
            else:
                self.cmdout+="Playing is currently restricted to tracks %s%s%s."%("containing the tag%s %s"%("s"*(len(self.playtags)>1)," and ".join(['"%s"'%tag for tag in self.playtags]).replace(" and ",", ",len(self.playtags)-2))*bool(self.playtags)," and "*bool(self.playtags)*bool(self.dontplaytags)+".\n"*(not bool(self.dontplaytags)),("not containing the tag%s %s.\n"%("s"*(len(self.dontplaytags)>1)," and ".join(['"%s"'%tag for tag in self.dontplaytags]).replace(" and ",", ",len(self.dontplaytags)-2)))*bool(self.dontplaytags))
        self.cmdout+="""Type "help" or "?" for a comprehensive list of commands at your disposal."""
        return True
    def cmd_stats(self,arg):
        if self.trackdata:
            self.cmdout+="The track database currently contains %s tracks with %s total tags."%(len(self.trackdata),sum([len(self.trackdata[track].tags) for track in self.trackdata if track!="#"]))
            self.cmdout+="\n%s of those tracks are forbidden for random play."%[self.trackdata[track].prob for track in self.trackdata if track!="#"].count(0)
            self.cmdout+="\nTotal number of tracks played:"
            self.cmdout+="\n    %s this session"%len(self.playedthissession)
            self.cmdout+="\n    %s total"%self.playedtotal
        else:
            self.cmdout+="There are no tracks in the track database yet."
        if self.newtracks:
            self.cmdout+="\nThere are %s tracks in the current playlist which are not yet tagged and rated."%len(self.newtracks)
        else:
            self.cmdout+="\nAll tracks in the current playlist are tagged and/or rated."
        return True
    def cmd_allcaps(self,arg):
        self.cmdout="PLEASE DO NOT WRITE IN ALLCAPS, IT IS NOT POLITE"
        return False
    def maketracklist(self):
        self.playthread.sema.acquire()
        print "Making tracklist with playtags =",self.playtags,"and dontplaytags =",self.dontplaytags
        if self.playthread.playing:
            np=self.nowplaying
        else:
            np=None
        self.playthread.sema.release()
        dirlist=[self.pwd]
        oldtracklist=[track for track in self.tracklist]
        self.tracklist=[]
        while dirlist:
            for dir in dirlist:
                contents=os.listdir(dir)
                for name in contents:
                    if os.path.isdir(dir+"/"+name):
                        dirlist.append(dir+"/"+name)
                    if name[-4:]==".mp3":
                        track=(dir+"/"+name).lower()
                        self.tracklist.append(track)
                lastvisited=dir
            while dirlist:
                try:
                    dir=dirlist.pop(0)
                except IndexError:
                    break
                if dir==lastvisited:
                    break
        if not self.tracklist:
            self.tracklist=oldtracklist
            return False
        if np in self.tracklist:
            self.trackindex=self.tracklist.index(np)
        print "New tracklist is",len(self.tracklist),"tracks long."
        self.makeplaylist()
        return True
    def makeplaylist(self):
        oldplaylist=[track for track in self.playlist]
        self.playlist=[track for track in self.tracklist if (not self.playtags and not self.dontplaytags) or (track in self.trackdata and (self.playtags=="*" or all([tag in self.trackdata[track].tags for tag in self.playtags]) and all([tag not in self.trackdata[track].tags for tag in self.dontplaytags])))]
        self.newtracks=[]
        for track in self.playlist:
            if track not in self.trackdata:
                self.newtracks.append(track)
        if not self.playlist:
            self.playlist=oldplaylist
            return False
        print "New playlist is",len(self.playlist),"tracks long, with",len(self.newtracks),"new tracks."
        return True
    def play(self,arg=None):
        if arg is None:
            if self.nexttrack:
                if self.nexttrack=="stop":
                    self.stop()
                    self.nexttrack=None
                    return
                if self.nexttrack=="quit":
                    self.playthread.sema.acquire()
                    self.playthread.pleaseexit=True
                    self.playthread.sema.release()
                    self.quit()
                    return
                r=self.canyouplay(self.nexttrack)
                self.nexttrack=None
            elif self.repeat:
                r=self.canyouplay(self.nowplaying)
            elif self.orderedplay:
                self.trackindex+=1
                self.trackindex%=len(self.playlist)
                r=self.canyouplay(self.playlist[self.trackindex])
            else:
                r=self.randomplay()
        elif type(arg)==int:
            r=self.canyouplay(self.playlist[arg])
            self.trackindex=arg
        else:
            if arg[:2]=="-o":
                arg=arg.split(" ",1)
                self.orderedplay=True
                self.echo("Beginning ordered play")
                self.makeplaylist()
                if len(arg[1])==2:
                    self.trackindex=0
                    r=self.canyouplay(self.playlist[0])
                else:
                    r=self.canyouplay(arg)
            else:
                r=self.canyouplay(arg)
        if r and r!="silent":
            self.playedtotal+=1
            self.playedthissession.append(self.nowplaying)
            self.trackdata[self.nowplaying].curprob=0
            if self.trackdata[self.nowplaying].curprob<0:
                self.trackdata[self.nowplaying].curprob=0
        if self.orderedplay:
            self.nexttrack=self.playlist[self.trackindex+1]
            self.playthread.sema.acquire()
            self.playthread.pleasenext=self.nexttrack
            self.playthread.sema.release()
        else:
            self.nexttrack=self.getrandomtrack()
            self.playthread.sema.acquire()
            self.playthread.pleasenext=self.nexttrack
            self.playthread.sema.release()
        return r
    def randomplay(self):
        track=self.getrandomtrack()
        self.playthread.sema.acquire()
        self.playthread.pleaseplay=track
        if track in self.altdata:
            alttrack=self.altdata[track]
            self.playthread.pleasealtplay=alttrack
            self.nowaltplaying=alttrack
        else:
            self.nowaltplaying=None
        self.playthread.sema.release()
        if self.muted:
            self.unmute()
        self.cmdout+="Now playing: "+track[len(self.pwd):]
        self.nowplaying=track
        return True
    def getrandomtrack(self):
        if self.newtracks:
            print "Choosing from",len(self.newtracks),"new tracks"
            track=random.choice(self.newtracks)
            self.trackindex=self.playlist.index(track)
            self.trackdata[track]=TrackdataEntry(tags=[])
            self.newtracks.remove(track)
        else:
            print "Choosing from",len([track for track in self.playlist if self.trackdata[track].curprob]),"tracks"
            totalprob=sum([self.trackdata[track].curprob for track in self.playlist])
            if totalprob==0:
                for track in self.playlist:
                    self.trackdata[track].curprob=self.trackdata[track].prob
            if totalprob>0:
                r=random.randrange(totalprob)
                i=0
                for track in self.playlist:
                    i+=self.trackdata[track].curprob
                    if i>r:
                        break
                self.trackindex=self.playlist.index(track)
            else:
                self.cmdout+="The playlist appears to be empty!"
        return track
    def strsplit(self,string):
        l=[]
        curstr=""
        singlequoted=False
        doublequoted=False
        for char in string:
            if char=='"' and not singlequoted:
                doublequoted^=True
            elif char=="'" and not doublequoted and not curstr:
                singlequoted^=True
            elif char==" "and not (singlequoted or doublequoted):
                l.append(curstr)
                curstr=""
            else:
                curstr+=char
        if curstr:
            l.append(curstr)
        return l
    def canyouplay(self,name):
        if type(name)!=unicode:
            name=unicode(name,"latin-1")
        matches=[]
        exactname=name
        name=self.strsplit(name)
        for i,track in enumerate(self.playlist):
            track=unicode(track,"latin-1")
            if all([s.lower().replace("_"," ") in track.lower().replace("_"," ") for s in name]):
                matches.append(track)
        if len(matches)==1 or exactname in matches:
            if exactname in matches:
                track=exactname
            else:
                track=matches[0]
            enctrack=track.encode("latin-1")
            self.trackindex=self.playlist.index(enctrack)
            self.playthread.sema.acquire()
            self.playthread.pleaseplay=enctrack
            if track in self.altdata:
                alttrack=self.altdata[enctrack]
                self.playthread.pleasealtplay=alttrack
                self.nowaltplaying=alttrack
            else:
                self.nowaltplaying=None
            self.playthread.sema.release()
            if self.muted:
                self.unmute()
            self.cmdout+="Now playing: "+enctrack[len(self.pwd):]
            self.nowplaying=enctrack
            if enctrack in self.newtracks:
                self.trackdata[enctrack]=TrackdataEntry(tags=[])
                self.newtracks.remove(enctrack)
            return True
        elif 1<len(matches)<10:
            i=1
            self.echo("%d tracks were found. Press a number to select one of them."%len(matches))
            for match in matches:
                self.echo(str(i)+" "+match[len(self.pwd):])
                i+=1
            self.choicelist=["play"]+matches
            return "silent"
        elif len(matches)>=10:
            self.playlist=[track.encode("latin-1") for track in matches]
            self.restrictedplaylist=True
            return self.play()
        self.cmdout="Could not find "+" ".join(name)+" in the playlist!"
        return False
    def pause(self):
        self.mute()
        self.playthread.sema.acquire()
        self.playthread.pleasepause=True
        self.playthread.sema.release()
        self.cmdout="Playback paused."
    def unpause(self):
        self.playthread.sema.acquire()
        self.playthread.pleaseunpause=True
        self.playthread.sema.release()
        self.unmute()
        self.cmdout="Playback resumed."
    def stop(self):
        self.mute()
        self.nowplaying=None
        self.playthread.sema.acquire()
        self.playthread.pleasestop=True
        self.playthread.sema.release()
        self.cmdout="Playback stopped."
        return True
    def mute(self):
        if not self.muted:
            self.volchange(0)
            self.cmdout="Muted."
    def unmute(self):
        if self.muted:
            self.volchange(self.muted)
            self.cmdout="Unmuted."
    def volchange(self,vol):
        self.playthread.sema.acquire()
        self.playthread.pleasevolume=vol
        self.playthread.sema.release()
        if vol:
            self.muted=0
        else:
            self.muted=self.volume
        self.volume=vol
        self.cmdout="Volume changed to "+str(vol)
    def write(self,text):
        self.echo(text)
    def echo(self,text=None,update=False):
        if text is not None:
            if type(text)==str:
                text=unicode(text,"latin-1")
            for line in text.split("\n"):
                if line:
                    tags=[]
                    self.body.config(state="normal")
                    if u"✔" in line:
                        self.body.insert("end","\n"+line,"green")
                    elif u"✘" in line:
                        self.body.insert("end","\n"+line,"red")
                    else:
                        self.body.insert("end","\n"+line)
                    self.body.see("end")
                    self.body.config(state="disabled")
        if update:
            self.window.update()
    def unicorn(self):
        #Unicorn shamelessly stolen from GENDICON by Christian Schröder
        return """                                                /
                                              .7
                                   \       , //
                                   |\.--._/|//
                                  /\ ) ) ).'/
                                 /(  \  // /
                                /(    `((_/ \ 
                               / ) |  **    /
                              /|)  \   *    L
                             |  \ L \   L   L
                            /  \  J  `. J   L
                            |  )   L   \/   \ 
                           /  \    J   (\   /
         _....___         |  \      \   \```
  ,.._.-'        '''--...-||\     -. \   \ 
.'.=.'                    `         `.\ [ Y
/   /                                  \]  J
| / Y                                    Y   L
| | |          \                         |   L
| | |           Y                        A  J
|   I           |                       /I\ /
|    \          I             \        ( |]/|
|     \         /._           /        -tI/ |
\      )       /   /'--------J           `'-:.
 J   .'      ,'  ,' ,     \   `'-.__          \ 
  \ T      ,'  ,'   )\    /|        ';'---7   /
   \|    ,'L  |...-' / _.' /         \   /   /
    \   Y  |  |    .'-'   /         ,--.(   /
     |  |  |  |  -'     .'         /  |    /\ 
     |  |. \  \      .-;.-/       |    \ .' / 
     |  | `-J  I ____,.-'`        |  _.-'   |
     L  L   L   \                 ``   J    |
      \  \   |   \                     J    |
       L  \  L    \                    L    \ 
       |   \  ) _.'\                    ) _.'\ 
       L    \('`    \                  ('`    \ 
        ) _.'\`-....'                   `-....'
       ('`    \ 
        `-.___/
"""
    def greet(self):
        [self.echo(line,update=True) for line in ("""This is mush %s. Have a nice day!
"""%self.version+self.unicorn()+"""Type "help" or "?" for help""").split("\n")]
    def quit(self):
        self.playthread.sema.acquire()
        if self.playthread.playing:
            self.playthread.sema.release()
            self.volchange(0)
            self.stop()
        else:
            self.playthread.sema.release()
        self.playthread.sema.acquire()
        self.playthread.pleaseexit=True
        self.playthread.sema.release()
        self.writetrackfile()
        self.window.destroy()
        self.alive=False

if __name__=="__main__":
    Mush()
