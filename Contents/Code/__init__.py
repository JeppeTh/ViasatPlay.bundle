import datetime, re

TITLE  = 'Viasat Play'
PREFIX = '/video/viasatplay'

ART   = "art-default.jpg"
THUMB = 'icon-default.png'

MAX_SEARCH_ITEMS = 50

CHANNELS = [ 
    {
        'title':    'TV3 Play',
        'base_url': 'http://www.tv3play.se',
        'thumb':    R('viasat_tv3.png'),
        'desc':     unicode('TV3 är kanalen med starka känslor och starka karaktärer. Det är en suverän mix av serier, livsstilsprogram, storfilmer, reportage och intressanta program.')
    },
    {
        'title':    'TV6 Play',
        'base_url': 'http://www.tv6play.se',
        'thumb':    R('viasat_tv6.png'),
        'desc':     unicode('TV6 En underhållningskanal för den breda publiken. Actionfilmer och den vassaste humorn.')
    },
    {
        'title':    'TV8 Play',
        'base_url': 'http://www.tv8play.se',
        'thumb':    R('viasat_tv8.png'),
        'desc':     unicode('TV8 är en svensk livsstils- och underhållningskanal med ett brett utbud. Du som gillar bilar, hus och vill veta allt om slottsliv, kommer inte vilja missa våra svenska produktioner i höst.')
    },
    {
        'title':    'TV10 Play',
        'base_url': 'http://www.tv10play.se',
        'thumb':    R('viasat_tv10.png'),
        'desc':     unicode('På TV10 Play ser du alla TV10:s egna program och vissa av våra livesändningar och utländska serier. Vi har dessutom extramaterial till många av våra program. Mer information om våra program finns på TV10.se.')
    }
]

###################################################################################################
def Start():
    DirectoryObject.thumb = R(THUMB)
    ObjectContainer.art   = R(ART)

    HTTP.CacheTime = CACHE_1HOUR  

###################################################################################################
@handler(PREFIX, TITLE, thumb = THUMB, art = ART)
def MainMenu():
    oc = ObjectContainer(title1 = TITLE)
    
    oc.add(
        DirectoryObject(
            key   = Callback(LatestEpisodes, title = "Latest programs"),
            title = "Latest programs",
            thumb = R(THUMB)
            )
        )
    oc.add(
        DirectoryObject(
            key   = Callback(LatestClips, title = "Latest clips"),
            title = "Latest clips",
            thumb = R(THUMB)
            )
        )
    oc.add(
        DirectoryObject(
            key   = Callback(Recommended, title = "Recommended"),
            title = "Recommended",
            thumb = R(THUMB)
            )
        )

    oc.add(
        DirectoryObject(
            key   = Callback(AllShows, title = "All Shows"),
            title = "AllShows",
            thumb = R(THUMB)
            )
        )
    
    oc.add(InputDirectoryObject(key    = Callback(Search),
                                title  = 'Search Program',
                                prompt = 'Search Program'
                                )
           )
    
    return oc

####################################################################################################
@route(PREFIX + '/latestepisodes')
def LatestEpisodes(title):
    oc   = ObjectContainer(title2 = unicode(title))

    for channel in CHANNELS:
        oc = Episodes(oc, title, channel['base_url'], channel['base_url'] + "/mobileapi/featured", 'latest_programs', channel['thumb'])

    oc.objects.sort(key=lambda obj: (obj.originally_available_at,obj.title), reverse=True)

    return oc

####################################################################################################
@route(PREFIX + '/latestclips')
def LatestClips(title):
    oc   = ObjectContainer(title2 = unicode(title))

    for channel in CHANNELS:
        oc = Clips(oc, channel['base_url'], channel['base_url'] + "/mobileapi/featured", title, 'latest_clips', channel['thumb'])

    oc.objects.sort(key=lambda obj: (obj.originally_available_at,obj.title), reverse=True)

    return oc

####################################################################################################
@route(PREFIX + '/recommended')
def Recommended(title):
    oc   = ObjectContainer(title2 = unicode(title))

    for channel in CHANNELS:
        oc = Episodes(oc, title, channel['base_url'], channel['base_url'] + "/mobileapi/featured", 'recommended', channel['thumb'])

    return oc

####################################################################################################
@route(PREFIX + '/allshows')
def AllShows(title):

    oc   = ObjectContainer(title2 = unicode(title))

    for channel in CHANNELS:
        oc = AddShows(oc, channel)

    oc.objects.sort(key = lambda obj: obj.title)
    return oc

####################################################################################################
def AddShows(oc, channel):
    programsInfo = JSON.ObjectFromURL(channel['base_url'] + "/mobileapi/format")
    
    for section in programsInfo['sections']:
        for program in section['formats']:
            # Samsung causes troubles with empty Descriptions...
            mySummary = None
            if program['description'] != "":
                mySummary = unicode(program['description'])
            oc.add(
                TVShowObject(
                    key = 
                        Callback(
                            Seasons,
                            title = unicode(program['title']),
                            summary = mySummary,
                            base_url = channel['base_url'],
                            id = program['id']
                        ),
                    rating_key = program['id'],
                    title = unicode(program['title']),
                    source_title = channel['title'],
                    summary = mySummary,
                    thumb = GetImageURL(program['image']),
                    art = channel['thumb']
                )
             )
  
    return oc

####################################################################################################
def Search(query, offset = 0):
    oc = ObjectContainer(title1 = TITLE, title2 = 'Search Results')

    query   = unicode(query)
    results = []
    counter = 0

    videos = AllShows("Searching").objects

    for video in videos:                
        # In case of single character - only compare initial character.
        if len(query) > 1 and query.lower() in video.title.lower() or \
                len(query) == 1 and query.lower() == video.title[0].lower():
                    
            results.append(
                {
                    'video': video, 
                    'title': video.title, 
                    'channel_title': video.source_title, 
                    'thumb': video.art
                }
            )
    
    results = sorted(results, key = lambda result: result['title'])           
    for result in results:
        counter = counter + 1
            
        if counter <= offset:
            continue
        
        video     = result['video']
        video.art = result['thumb']
                
        oc.add(video)
                    
        if len(oc) >= MAX_SEARCH_ITEMS:
            oc.objects.sort(key = lambda obj: obj.title)
                
            oc.add(
                NextPageObject(
                    key =
                        Callback(
                            Search,
                            query = query,
                            offset = counter
                        ),
                    title = "Next..."
                )
            )
            return oc

    if len(oc) == 0:
        return NoProgramsFound(oc)
    else:
        oc.objects.sort(key = lambda obj: obj.title)
        return oc

####################################################################################################
@route(PREFIX + '/Seasons')
def Seasons(title, summary, base_url, id):
    if summary:
        summary = unicode(summary)
        
    oc = ObjectContainer(title2 = unicode(title))
  
    seasonsInfo = JSON.ObjectFromURL(base_url + "/mobileapi/detailed?formatid=" + id)
    seasonImgUrl = GetImageURL(seasonsInfo['format']['image'])
    for season in seasonsInfo['formatcategories']:
        seasonName   = unicode(season['name'])
        videos_url   = season['videos_call']
        if len(seasonsInfo['formatcategories']) > 1:
            oc.add(
                DirectoryObject(
                    key = 
                    Callback(Episodes, 
                             oc         = None,
                             title      = seasonName,
                             base_url   = base_url, 
                             videos_url = videos_url,
                             id         = 'video_program',
                             art        = seasonImgUrl
                        ), 
                    title   = seasonName, 
                    summary = summary, 
                    thumb   = GetImageURL(season['image']),
                    art     = seasonImgUrl
                    )
                )
        else:
            return Episodes(None,
                            seasonName,
                            base_url,
                            videos_url,
                            'video_program',
                            seasonImgUrl)

    return oc
 
####################################################################################################
@route(PREFIX + '/Episodes')
def Episodes(oc, title, base_url, videos_url, id = None, art = None):
    orgOc = oc
    if not oc:
        oc = ObjectContainer(title2 = unicode(title))
    episodeOc = ObjectContainer(title2 = unicode(title))

    try:
        videosInfo = JSON.ObjectFromURL(videos_url)
    except:
        return NoProgramsFound(oc)

    if id:
        videos = videosInfo[id]
    else:
        videos = videosInfo
    
    if id == 'video_program' and len(videosInfo['video_clip']) > 0:
        oc.add(DirectoryObject(
                key = Callback(Clips,
                               oc         = None,
                               base_url   = base_url,
                               videos_url = videos_url,
                               title      = title,
                               id         = 'video_clip',
                               art        = art
                               ), 
                title = "Klipp", 
                thumb = GetChannelThumb(base_url), 
                art   = art
                )
               )
    if videos:
        for video in videos:
            try:
                duration = int(video['length']) * 1000
            except:
                duration = None
            try:
                season = int(video['season'])
            except:
                season = None
            show = unicode(video['formattitle'])
            summary = unicode(video['summary'].strip())
            title = unicode(video['title'] + " - " + summary)
            if not orgOc and show in title:
                title = re.sub(show+"[ 	-:,]*(S[0-9]+E[0-9]+)*[ 	-:,]*(.+)", "\\2", title)
            episode = int(video['episode'])
            if not video['description'].strip() in summary:
                summary = unicode(video['description'].strip()) + ". " + summary
            if 'expiration' in video and video['expiration'] and len(video['expiration'])>0:
                summary = AddAvailability(int(video['expiration']), summary)
            episodeOc.add(
                EpisodeObject(
                    url = base_url + '/play/' + video['id'],
                    title = title,
                    summary = summary,
                    show = show,
                    art = art,
                    thumb = GetImageURL(video['image']),
                    originally_available_at = Datetime.ParseDate(video['airdate'].split(" ")[0]).date(),
                    duration = duration,
                    season = season,
                    index = episode
                    )
                )

        if id == 'video_program':
            sortOnAirData(episodeOc)
        for ep in episodeOc.objects:
            oc.add(ep)
    elif id == 'video_program' and (videosInfo['video_clip'] == None or len(videosInfo['video_clip']) < 1):
        return NoProgramsFound(oc)

    return oc

####################################################################################################
@route(PREFIX + '/Clips')
def Clips(oc, base_url, videos_url, title, id, art=None):

    orgOc = oc
    if not oc:
        oc = ObjectContainer(title2 = unicode(title))

    videosInfo = JSON.ObjectFromURL(videos_url)

    if id:
        videos = videosInfo[id]
    else:
        videos = videosInfo
    
    for clip in videos:
        try:
            duration = int(clip['length']) * 1000
        except:
            duration = None
        title = unicode(clip['title'])
        show = unicode(clip['formattitle'])
        if not orgOc and show in title:
            title = re.sub(show+"[ 	-:,]*(S[0-9]+E[0-9]+)*[ 	-:,]*(.+)", "\\2", title)
        oc.add(
            VideoClipObject(
                url = addSamsung(base_url + '/play/' + clip['id'], title),
                title = title,
                summary = unicode(clip['summary']),
                thumb = GetImageURL(clip['image']),
                art = art,
                originally_available_at = Datetime.FromTimestamp(int(clip['created'])),
                duration = duration
                )
            )
    sortOnAirData(oc)
    return oc

####################################################################################################
def NoProgramsFound(oc):
    oc.header  = "Sorry"
    oc.message = "No programs found."
     
    return oc

####################################################################################################
def GetImageURL(url):
    return "http://play.pdl.viaplay.com/imagecache/497x280/" + url.replace('\\', '') 

####################################################################################################
def GetChannelThumb(url):
    for channel in CHANNELS:
        if channel['base_url'] in url:
            return channel['thumb']
    return R(THUMB)

####################################################################################################
def AddAvailability(expiration, summary):
    availability = Datetime.FromTimestamp(expiration)-datetime.datetime.now()
    return unicode('Tillgänglig: %i dagar kvar. \n%s' % (availability.days, summary))

####################################################################################################
def sortOnAirData(Objects):
    for obj in Objects.objects:
        if obj.originally_available_at == None:
            Log("JTDEBUG - air date missing for %s" % obj.title)
            return Objects.objects.reverse()
    return Objects.objects.sort(key=lambda obj: (obj.originally_available_at,obj.title))
