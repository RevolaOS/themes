# Bitmaps

Every bitmap of Apple's 2.0.5 firmware a theme can replace, from the
[catalog](catalog.md) `rvt/data/osos-2.0.5.json`, grouped by the part of the
name before the first underscore (`No_Content` counts as one). Size is width x height in pixels; Palette is
the native palette's entries, none for masks, RGB565 and BGRA8888; Tintable
says whether `[<appearance>.tint]` may name it (masks, paletted and BGRA8888
bitmaps yes, RGB565 no). Appears says where the iPod draws it and is filled in by hand.

Regenerate with `python3 tools/bitmaps_doc.py`; the Appears column survives.

## Calendar

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `Calendar_Active_Cell` | 41x30 | indexed8 | 120 | yes | Calendar, days of the shown month |
| `Calendar_Alarm` | 18x18 | bgra8888 | - | yes | Calendar |
| `Calendar_Flag` | 11x12 | indexed8 | 19 | yes | Calendar |
| `Calendar_Hilite_Cell` | 41x30 | bgra8888 | - | yes | Calendar, the selected day |
| `Calendar_Inactive_Cell` | 41x30 | indexed8 | 40 | yes | Calendar, days of the neighbouring months |
| `Calendar_Small_Alarm` | 11x11 | bgra8888 | - | yes | Calendar |

## CapacityView

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `CapacityView_Detailed_AudioCenter_Image` | 1x30 | bgra8888 | - | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_AudioLeft_Image` | 16x30 | indexed8 | 95 | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_AudioRight_Image` | 16x30 | indexed8 | 104 | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_Edge_Image` | 2x30 | indexed8 | 3 | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_EmptyCenter_Image` | 1x30 | bgra8888 | - | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_EmptyLeft_Image` | 16x30 | indexed8 | 76 | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_EmptyRight_Image` | 16x30 | indexed8 | 76 | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_OtherCenter_Image` | 1x30 | bgra8888 | - | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_OtherLeft_Image` | 16x30 | indexed8 | 101 | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_OtherRight_Image` | 16x30 | indexed8 | 97 | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_PhotosCenter_Image` | 1x30 | bgra8888 | - | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_PhotosLeft_Image` | 16x30 | indexed8 | 92 | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_PhotosRight_Image` | 16x30 | indexed8 | 107 | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_VideoCenter_Image` | 1x30 | bgra8888 | - | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_VideoLeft_Image` | 16x30 | indexed8 | 92 | yes | Settings > About, the capacity bars |
| `CapacityView_Detailed_VideoRight_Image` | 16x30 | indexed8 | 97 | yes | Settings > About, the capacity bars |
| `CapacityView_Simple_EmptyCenter_Image` | 1x13 | bgra8888 | - | yes | Settings > About, the capacity bars |
| `CapacityView_Simple_EmptyLeft_Image` | 9x13 | bgra8888 | - | yes | Settings > About, the capacity bars |
| `CapacityView_Simple_EmptyRight_Image` | 9x13 | bgra8888 | - | yes | Settings > About, the capacity bars |
| `CapacityView_Simple_FillCenter_Image` | 1x13 | bgra8888 | - | yes | Settings > About, the capacity bars |
| `CapacityView_Simple_FillLeft_Image` | 7x13 | bgra8888 | - | yes | Settings > About, the capacity bars |
| `CapacityView_Simple_FillRight_Image` | 7x13 | bgra8888 | - | yes | Settings > About, the capacity bars |

## Caption

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `Caption_LeftEndcapBottom_Image` | 9x9 | mask4 | - | yes | Pane captions |
| `Caption_LeftEndcapTop_Image` | 9x9 | mask4 | - | yes | Pane captions |
| `Caption_RightEndcapBottom_Image` | 9x9 | mask4 | - | yes | Pane captions |
| `Caption_RightEndcapTop_Image` | 9x9 | mask4 | - | yes | Pane captions |

## ChargingMode

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `ChargingMode_Image_Critical` | 205x163 | indexed16 | 5552 | yes | Charging screen |
| `ChargingMode_Image_Empty_CapLeft` | 38x142 | indexed16 | 1243 | yes | Charging screen |
| `ChargingMode_Image_Empty_CapRight` | 45x142 | indexed16 | 1497 | yes | Charging screen |
| `ChargingMode_Image_Empty_Middle` | 8x142 | indexed8 | 225 | yes | Charging screen |
| `ChargingMode_Image_Green_CapLeft` | 38x142 | indexed16 | 1380 | yes | Charging screen |
| `ChargingMode_Image_Green_CapRight` | 45x142 | indexed16 | 1619 | yes | Charging screen |
| `ChargingMode_Image_Green_Middle` | 8x142 | bgra8888 | - | yes | Charging screen |
| `ChargingMode_Image_Green_Middle_Cap` | 8x142 | bgra8888 | - | yes | Charging screen |
| `ChargingMode_Image_ToggleCharged` | 47x29 | mask4 | - | yes | Charging screen |
| `ChargingMode_Image_ToggleCharging` | 23x57 | mask4 | - | yes | Charging screen |

## Clock

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `Clock_CenterCap_Image` | 73x73 | indexed8 | 9 | yes | Clock faces |
| `Clock_Hours_Image_0` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_1` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_2` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_3` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_4` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_5` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_6` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_7` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_8` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_9` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_10` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_11` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_12` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_13` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_14` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_15` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_16` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_17` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_18` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_19` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_20` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_21` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_22` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_23` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_24` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_25` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_26` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_27` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_28` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Hours_Image_29` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Large_Image` | 132x145 | indexed16 | 1781 | yes | Clock faces |
| `Clock_Mins_Image_0` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_1` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_2` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_3` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_4` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_5` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_6` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_7` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_8` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_9` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_10` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_11` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_12` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_13` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_14` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Mins_Image_15` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_0` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_1` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_2` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_3` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_4` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_5` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_6` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_7` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_8` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_9` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_10` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_11` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_12` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_13` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_14` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Secs_Image_15` | 73x73 | mask4 | - | yes | Clock faces |
| `Clock_Shadow_Image` | 8x26 | indexed8 | 27 | yes | Clock faces |
| `Clock_Small_Image` | 73x73 | indexed16 | 533 | yes | Clock faces |
| `Clock_Small_Night_Image` | 73x73 | indexed16 | 369 | yes | Clock faces |

## DiskModeImage

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `DiskModeImage_ConnectedIcon` | 113x113 | indexed8 | 64 | yes | Disk Mode |
| `DiskModeImage_DisconnectIcon` | 112x112 | indexed8 | 95 | yes | Disk Mode |
| `DiskModeImage_Progress_Empty_Fill` | 1x12 | indexed8 | 4 | yes | Disk Mode |
| `DiskModeImage_Progress_Empty_LeftCap` | 8x12 | indexed8 | 38 | yes | Disk Mode |
| `DiskModeImage_Progress_Empty_RightCap` | 8x12 | bgra8888 | - | yes | Disk Mode |
| `DiskModeImage_Progress_Full_Fill` | 1x12 | bgra8888 | - | yes | Disk Mode |
| `DiskModeImage_Progress_Full_LeftCap` | 7x12 | bgra8888 | - | yes | Disk Mode |
| `DiskModeImage_Progress_Full_RightCap` | 7x12 | bgra8888 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow1` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow3` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow5` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow7` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow9` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow11` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow13` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow15` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow17` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow19` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow21` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow23` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow25` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow27` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow29` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow31` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow33` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncArrow35` | 76x76 | mask4 | - | yes | Disk Mode |
| `DiskModeImage_SyncIcon` | 112x112 | indexed16 | 1708 | yes | Disk Mode |

## Genius

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `Genius_Slider_Endcap_Image` | 6x34 | bgra8888 | - | yes | Genius |
| `Genius_Slider_Fill_Image` | 1x34 | bgra8888 | - | yes | Genius |
| `Genius_Slider_Icon_Image` | 18x21 | indexed8 | 137 | yes | Genius |
| `Genius_Slider_Image` | 75x34 | indexed8 | 118 | yes | Genius |

## Media

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `Media_AlbumsProxy_Image` | 55x55 | indexed8 | 202 | yes | Music lists, the proxy icons |
| `Media_AllAlbumsProxy_Image` | 55x55 | indexed16 | 576 | yes | Music lists, the proxy icons |
| `Media_ArtistsProxy_Image` | 55x55 | indexed8 | 203 | yes | Music lists, the proxy icons |
| `Media_AudioBooksProxy_Image` | 55x55 | indexed8 | 230 | yes | Music lists, the proxy icons |
| `Media_AudioProxy_Image` | 55x55 | indexed8 | 240 | yes | Music lists, the proxy icons |
| `Media_DocumentsProxy_Image` | 55x55 | indexed16 | 295 | yes | Music lists, the proxy icons |
| `Media_Genius_Large_Image` | 114x114 | indexed16 | 4069 | yes | Music lists, the proxy icons |
| `Media_Genius_Normal_Image` | 18x18 | bgra8888 | - | yes | Music lists, the proxy icons |
| `Media_Genius_Refresh_Hi_Image` | 15x18 | indexed8 | 90 | yes | Music lists, the proxy icons |
| `Media_Genius_Refresh_Image` | 15x18 | indexed8 | 90 | yes | Music lists, the proxy icons |
| `Media_Genius_Selected_Image` | 18x18 | bgra8888 | - | yes | Music lists, the proxy icons |
| `Media_MusicVideosProxy_Image` | 55x55 | indexed8 | 234 | yes | Music lists, the proxy icons |
| `Media_NowPlayingIcon_Black_Image` | 24x14 | indexed8 | 65 | yes | Music lists, the proxy icons |
| `Media_NowPlayingIcon_Playlist_Black_Image` | 17x14 | indexed8 | 65 | yes | Music lists, the proxy icons |
| `Media_NowPlayingIcon_Playlist_White_Image` | 17x16 | indexed8 | 64 | yes | Music lists, the proxy icons |
| `Media_NowPlayingIcon_White_Image` | 24x16 | indexed8 | 64 | yes | Music lists, the proxy icons |
| `Media_OTGPlaylist_Image` | 46x57 | indexed8 | 103 | yes | Music lists, the proxy icons |
| `Media_PhotosProxy_Image` | 55x55 | indexed16 | 309 | yes | Music lists, the proxy icons |
| `Media_PlaylistsProxy_Image` | 55x55 | indexed8 | 197 | yes | Music lists, the proxy icons |
| `Media_PodcastsProxy_Image` | 55x55 | indexed8 | 231 | yes | Music lists, the proxy icons |
| `Media_SearchProxy_Image` | 55x55 | indexed8 | 185 | yes | Music lists, the proxy icons |
| `Media_TVShowsProxy_Image` | 55x55 | indexed8 | 169 | yes | Music lists, the proxy icons |
| `Media_VideoStatusIcon_Image` | 23x29 | indexed8 | 4 | yes | Music lists, the proxy icons |
| `Media_VideoStatusIcon_White_Image` | 23x29 | indexed8 | 3 | yes | Music lists, the proxy icons |
| `Media_VideosProxy_Image` | 55x55 | indexed8 | 186 | yes | Music lists, the proxy icons |

## No_Content

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `No_Content_Albums_Small_Image` | 55x55 | rgb565 | - | no | Empty lists |
| `No_Content_AudioBooks_Small_Image` | 55x55 | rgb565 | - | no | Empty lists |
| `No_Content_Audiobooks_Preview_Image` | 119x119 | mask8 | - | yes | Empty lists |
| `No_Content_Contacts_Preview_Image` | 200x145 | mask4 | - | yes | Empty lists |
| `No_Content_Movies_Preview_Image` | 119x119 | mask8 | - | yes | Empty lists |
| `No_Content_MusicVideos_Small_Image` | 55x55 | rgb565 | - | no | Empty lists |
| `No_Content_Music_Preview_Image` | 119x119 | mask8 | - | yes | Empty lists |
| `No_Content_Music_Video_Preview_Image` | 119x119 | mask8 | - | yes | Empty lists |
| `No_Content_Notes_Preview_Image` | 161x145 | mask4 | - | yes | Empty lists |
| `No_Content_Photo_Preview_Image` | 119x119 | mask8 | - | yes | Empty lists |
| `No_Content_Playlist_Preview_Image` | 119x119 | mask8 | - | yes | Empty lists |
| `No_Content_Podcast_Preview_Image` | 119x119 | mask8 | - | yes | Empty lists |
| `No_Content_Podcasts_Small_Image` | 55x55 | rgb565 | - | no | Empty lists |
| `No_Content_TVShow_Preview_Image` | 119x119 | mask8 | - | yes | Empty lists |
| `No_Content_TVShows_Small_Image` | 55x55 | rgb565 | - | no | Empty lists |
| `No_Content_Videos_Small_Image` | 55x55 | rgb565 | - | no | Empty lists |
| `No_Content_iTunesU_Preview_Image` | 119x119 | mask8 | - | yes | Empty lists |
| `No_Content_iTunesU_Small_Image` | 55x55 | rgb565 | - | no | Empty lists |

## NowPlaying

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `NowPlaying_Black_FF_Image` | 14x16 | indexed8 | 12 | yes | Now Playing |
| `NowPlaying_Black_Pause_Image` | 14x16 | indexed8 | 3 | yes | Now Playing |
| `NowPlaying_Black_Play_Image` | 14x16 | indexed8 | 18 | yes | Now Playing |
| `NowPlaying_Black_Record_Image` | 13x13 | indexed8 | 73 | yes | Now Playing |
| `NowPlaying_Black_Rew_Image` | 14x16 | indexed8 | 12 | yes | Now Playing |
| `NowPlaying_Black_Volume_Locked_Image` | 19x17 | indexed8 | 10 | yes | Now Playing |
| `NowPlaying_Blue_Dot_Image` | 16x17 | indexed8 | 14 | yes | Now Playing |
| `NowPlaying_Blue_Star_Image` | 16x17 | indexed8 | 92 | yes | Now Playing |
| `NowPlaying_Chaptermark_Image` | 1x14 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_Classic_Repeat_Image` | 19x15 | indexed8 | 25 | yes | Now Playing |
| `NowPlaying_Classic_Repeat_Once_Image` | 19x15 | indexed8 | 59 | yes | Now Playing |
| `NowPlaying_Classic_Shuffle_Image` | 18x14 | indexed8 | 68 | yes | Now Playing |
| `NowPlaying_Dot_Image` | 22x26 | indexed8 | 15 | yes | Now Playing |
| `NowPlaying_Genius_Icon` | 28x28 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_Idle_Battery_0_Image` | 72x40 | indexed8 | 4 | yes | Now Playing, the idle battery |
| `NowPlaying_Idle_Battery_1_Image` | 72x40 | indexed8 | 2 | yes | Now Playing, the idle battery |
| `NowPlaying_Idle_Battery_2_Image` | 72x40 | indexed8 | 2 | yes | Now Playing, the idle battery |
| `NowPlaying_Idle_Battery_3_Image` | 72x40 | indexed8 | 2 | yes | Now Playing, the idle battery |
| `NowPlaying_Idle_Battery_4_Image` | 72x40 | indexed8 | 2 | yes | Now Playing, the idle battery |
| `NowPlaying_Idle_Battery_5_Image` | 72x40 | indexed8 | 2 | yes | Now Playing, the idle battery |
| `NowPlaying_Idle_Battery_6_Image` | 72x40 | indexed8 | 2 | yes | Now Playing, the idle battery |
| `NowPlaying_Idle_Battery_7_Image` | 72x40 | indexed8 | 2 | yes | Now Playing, the idle battery |
| `NowPlaying_Idle_Colon_Image` | 15x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Digit_0_Image` | 38x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Digit_1_Image` | 27x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Digit_2_Image` | 39x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Digit_3_Image` | 38x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Digit_4_Image` | 38x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Digit_5_Image` | 38x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Digit_6_Image` | 38x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Digit_7_Image` | 38x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Digit_8_Image` | 38x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Digit_9_Image` | 38x76 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Lock_Image` | 25x38 | indexed8 | 6 | yes | Now Playing |
| `NowPlaying_Idle_Play_Image` | 41x43 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Idle_Radio_Image` | 67x40 | indexed8 | 2 | yes | Now Playing |
| `NowPlaying_Large_Blue_Star_Image` | 22x26 | indexed8 | 226 | yes | Now Playing |
| `NowPlaying_Large_Shuffle_Image` | 25x19 | indexed8 | 91 | yes | Now Playing |
| `NowPlaying_Overlay_Image` | 8x37 | indexed8 | 38 | yes | Now Playing |
| `NowPlaying_Paused_Image` | 72x71 | indexed16 | 914 | yes | Now Playing |
| `NowPlaying_ProgressBar_Active_Background_Image` | 8x28 | indexed8 | 36 | yes | Now Playing |
| `NowPlaying_ProgressBar_Active_Fill_Image` | 8x28 | indexed8 | 29 | yes | Now Playing |
| `NowPlaying_ProgressBar_Active_Fill_Orange_Image` | 8x28 | indexed8 | 34 | yes | Now Playing |
| `NowPlaying_ProgressBar_Growth_Image` | 5x7 | indexed8 | 9 | yes | Now Playing |
| `NowPlaying_ProgressBar_Inactive_Background_Image` | 8x24 | indexed8 | 33 | yes | Now Playing |
| `NowPlaying_ProgressBar_Inactive_Fill_Image` | 8x24 | indexed8 | 37 | yes | Now Playing |
| `NowPlaying_ProgressBar_LeftEndcap_Image` | 12x7 | indexed8 | 35 | yes | Now Playing |
| `NowPlaying_ProgressBar_RightEndcap_Image` | 12x7 | indexed8 | 35 | yes | Now Playing |
| `NowPlaying_ProgressBar_Scrub_Image` | 13x28 | indexed8 | 129 | yes | Now Playing |
| `NowPlaying_ProgressFill_Growth_Image` | 2x7 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_ProgressFill_LeftEndcap_Image` | 3x7 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_ProgressFill_RightEndcap_Image` | 4x7 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_Rental_Warning_Overlay_Fill` | 1x104 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_Rental_Warning_Overlay_Left` | 9x104 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_Rental_Warning_Overlay_Right` | 9x104 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_Repeat_Image` | 20x14 | indexed8 | 28 | yes | Now Playing |
| `NowPlaying_Repeat_Once_Image` | 24x16 | indexed8 | 93 | yes | Now Playing |
| `NowPlaying_Scrub_Image` | 14x9 | indexed8 | 25 | yes | Now Playing |
| `NowPlaying_Shuffle_Image` | 18x16 | indexed8 | 68 | yes | Now Playing |
| `NowPlaying_Small_Grey_Star_Image` | 13x13 | indexed8 | 28 | yes | Now Playing |
| `NowPlaying_Small_White_Star_Image` | 13x13 | indexed8 | 28 | yes | Now Playing |
| `NowPlaying_Star_Image` | 13x13 | indexed8 | 28 | yes | Now Playing |
| `NowPlaying_StatusBar_Image` | 320x24 | indexed8 | 41 | yes | Stopwatch and Charging header |
| `NowPlaying_White_FF_Image` | 15x16 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_White_Pause_Image` | 14x16 | indexed8 | 72 | yes | Now Playing |
| `NowPlaying_White_Play_Image` | 14x16 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_White_Rew_Image` | 15x16 | bgra8888 | - | yes | Now Playing |
| `NowPlaying_White_Volume_High_Image` | 19x17 | indexed8 | 51 | yes | Now Playing |
| `NowPlaying_White_Volume_Locked_Image` | 19x17 | indexed8 | 11 | yes | Now Playing |
| `NowPlaying_White_Volume_Low_Image` | 9x17 | indexed8 | 25 | yes | Now Playing |

## OptionBar

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `OptionBar_Black_Thumb_Center_Image` | 1x26 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_Black_Thumb_LeftCap_Image` | 6x26 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_Black_Thumb_RightCap_Image` | 6x26 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_Black_Well_Center_Image` | 1x26 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_Black_Well_LeftCap_Image` | 6x26 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_Black_Well_RightCap_Image` | 6x26 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_NowPlaying_Thumb_Center_Image` | 1x27 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_NowPlaying_Thumb_LeftCap_Image` | 8x27 | indexed8 | 48 | yes | Search letter strip and option bars |
| `OptionBar_NowPlaying_Thumb_RightCap_Image` | 8x27 | indexed8 | 48 | yes | Search letter strip and option bars |
| `OptionBar_NowPlaying_Well_Center_Image` | 1x27 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_NowPlaying_Well_LeftCap_Image` | 8x27 | indexed8 | 70 | yes | Search letter strip and option bars |
| `OptionBar_NowPlaying_Well_RightCap_Image` | 8x27 | indexed8 | 70 | yes | Search letter strip and option bars |
| `OptionBar_White_Thumb_Center_Image` | 1x29 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_White_Thumb_LeftCap_Image` | 8x29 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_White_Thumb_RightCap_Image` | 8x29 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_White_Well_Center_Image` | 1x29 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_White_Well_LeftCap_Image` | 8x29 | bgra8888 | - | yes | Search letter strip and option bars |
| `OptionBar_White_Well_RightCap_Image` | 8x29 | bgra8888 | - | yes | Search letter strip and option bars |

## Playlist

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `Playlist_Folder_Icon` | 23x24 | bgra8888 | - | yes | Playlists |
| `Playlist_Genius_Icon` | 23x25 | bgra8888 | - | yes | Playlists |
| `Playlist_Genius_Icon_Hi` | 23x25 | bgra8888 | - | yes | Playlists |
| `Playlist_Regular_Icon` | 23x24 | bgra8888 | - | yes | Playlists |
| `Playlist_Saved_Genius_Icon` | 23x24 | bgra8888 | - | yes | Playlists |
| `Playlist_Smart_Icon` | 23x24 | bgra8888 | - | yes | Playlists |

## Podcasts

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `Podcasts_new_item_Image` | 13x29 | indexed8 | 46 | yes | Podcasts |
| `Podcasts_new_item_video_Image` | 13x29 | indexed8 | 47 | yes | Podcasts |
| `Podcasts_new_item_video_white_Image` | 13x29 | indexed8 | 32 | yes | Podcasts |
| `Podcasts_new_item_white_Image` | 13x29 | indexed8 | 31 | yes | Podcasts |
| `Podcasts_spacer_Image` | 13x29 | indexed8 | 1 | yes | Podcasts |
| `Podcasts_video_solo_Image` | 13x29 | indexed8 | 4 | yes | Podcasts |
| `Podcasts_video_white_solo_Image` | 13x29 | indexed8 | 3 | yes | Podcasts |

## Radio

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `Radio_Bottom_Background_Image` | 8x36 | indexed8 | 118 | yes | Radio |
| `Radio_Bottom_Bar_Image` | 320x5 | indexed8 | 150 | yes | Radio |
| `Radio_Current_Image` | 2x36 | bgra8888 | - | yes | Radio |
| `Radio_Digit_0_Image` | 42x98 | indexed8 | 90 | yes | Radio |
| `Radio_Digit_1_Image` | 32x98 | indexed8 | 70 | yes | Radio |
| `Radio_Digit_2_Image` | 39x98 | indexed8 | 83 | yes | Radio |
| `Radio_Digit_3_Image` | 39x98 | indexed8 | 93 | yes | Radio |
| `Radio_Digit_4_Image` | 39x98 | indexed8 | 79 | yes | Radio |
| `Radio_Digit_5_Image` | 39x98 | indexed8 | 92 | yes | Radio |
| `Radio_Digit_6_Image` | 39x98 | indexed8 | 93 | yes | Radio |
| `Radio_Digit_7_Image` | 39x98 | indexed8 | 79 | yes | Radio |
| `Radio_Digit_8_Image` | 39x98 | indexed8 | 90 | yes | Radio |
| `Radio_Digit_9_Image` | 39x98 | indexed8 | 88 | yes | Radio |
| `Radio_Digit_Period_Image` | 18x98 | indexed8 | 44 | yes | Radio |
| `Radio_Icon_Image` | 146x110 | indexed16 | 4401 | yes | Radio |
| `Radio_MHz_Image` | 63x44 | indexed8 | 84 | yes | Radio |
| `Radio_Preset_Image` | 11x11 | indexed8 | 19 | yes | Radio |
| `Radio_Scanning_1_Image` | 19x15 | indexed8 | 6 | yes | Radio |
| `Radio_Scanning_2_Image` | 19x15 | indexed8 | 7 | yes | Radio |
| `Radio_Scanning_3_Image` | 19x15 | indexed8 | 7 | yes | Radio |
| `Radio_Scanning_4_Image` | 19x15 | indexed8 | 7 | yes | Radio |
| `Radio_Scanning_5_Image` | 19x15 | indexed8 | 7 | yes | Radio |
| `Radio_Scanning_6_Image` | 19x15 | indexed8 | 7 | yes | Radio |
| `Radio_Scanning_7_Image` | 19x15 | indexed8 | 7 | yes | Radio |
| `Radio_Signal_Indicator_Dark_Image` | 20x16 | indexed8 | 35 | yes | Radio |
| `Radio_Signal_Indicator_Light_Image` | 20x16 | indexed8 | 101 | yes | Radio |
| `Radio_Ticks_Image` | 320x36 | mask4 | - | yes | Radio |
| `Radio_Ticks_Japan_Image` | 320x36 | mask4 | - | yes | Radio |

## Settings

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `Settings_About_Band_Image` | 320x39 | indexed16 | 512 | yes | Settings pane previews |
| `Settings_About_Bubble_Deselected_Image` | 6x6 | indexed8 | 4 | yes | Settings pane previews |
| `Settings_About_Bubble_Selected_Image` | 6x6 | indexed8 | 4 | yes | Settings pane previews |
| `Settings_About_Capacity_AudioLegend_Image` | 12x12 | indexed8 | 36 | yes | Settings pane previews |
| `Settings_About_Capacity_Fill_Image` | 1x30 | bgra8888 | - | yes | Settings pane previews |
| `Settings_About_Capacity_LeftCap_Image` | 16x30 | indexed8 | 76 | yes | Settings pane previews |
| `Settings_About_Capacity_OtherLegend_Image` | 12x12 | indexed8 | 34 | yes | Settings pane previews |
| `Settings_About_Capacity_PhotosLegend_Image` | 12x12 | indexed8 | 26 | yes | Settings pane previews |
| `Settings_About_Capacity_RightCap_Image` | 16x30 | indexed8 | 76 | yes | Settings pane previews |
| `Settings_About_Capacity_VideoLegend_Image` | 12x12 | indexed8 | 34 | yes | Settings pane previews |
| `Settings_About_Logo_Image` | 64x72 | indexed16 | 906 | yes | Settings pane previews |
| `Settings_Accessory_TitleBand_Image` | 296x20 | indexed8 | 5 | yes | Settings pane previews |
| `Settings_AppleLogoPreview_Image` | 77x80 | mask8 | - | yes | Settings pane previews |
| `Settings_AppleLogo_Image` | 119x119 | mask8 | - | yes | Settings pane previews |
| `Settings_Audiobooks_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_Backlight_2s_Image` | 78x121 | mask8 | - | yes | Settings > Backlight |
| `Settings_Backlight_5s_Image` | 78x121 | mask8 | - | yes | Settings > Backlight |
| `Settings_Backlight_10s_Image` | 78x121 | mask8 | - | yes | Settings > Backlight |
| `Settings_Backlight_20s_Image` | 78x121 | mask8 | - | yes | Settings > Backlight |
| `Settings_Backlight_30s_Image` | 78x121 | mask8 | - | yes | Settings > Backlight |
| `Settings_Backlight_Image` | 78x122 | mask4 | - | yes | Settings > Backlight |
| `Settings_Backlight_off_Image` | 78x121 | mask8 | - | yes | Settings > Backlight |
| `Settings_Backlight_on_Image` | 78x121 | mask8 | - | yes | Settings > Backlight |
| `Settings_BasePanelWide_Image` | 130x105 | indexed16 | 409 | yes | Settings pane previews |
| `Settings_BasePanel_Image` | 78x121 | indexed16 | 546 | yes | Settings pane previews |
| `Settings_Brightness_Image` | 78x121 | mask8 | - | yes | Settings > Brightness |
| `Settings_ClickerOff_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_ClickerOn_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_DateTime_Calendar_Image` | 130x128 | indexed16 | 298 | yes | Settings pane previews |
| `Settings_DateTime_Capsule_Hilite` | 40x37 | indexed8 | 141 | yes | Settings pane previews |
| `Settings_DateTime_Capsule_Image` | 167x57 | indexed16 | 540 | yes | Settings pane previews |
| `Settings_DateTime_TimeZonePin_Image` | 19x24 | indexed8 | 171 | yes | Settings pane previews |
| `Settings_EQ_Acoustic_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_BassBooster_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_BassReducer_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Classical_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Dance_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Deep_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Electronic_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Flat_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_HipHop_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Jazz_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Latin_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Loudness_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Lounge_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Piano_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Pop_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_RandB_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_Rock_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_SmallSpeakers_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_SpokenWord_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_TrebleBooster_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_TrebleReducer_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_EQ_VocalBooster_Image` | 130x79 | mask4 | - | yes | Settings > EQ, the preset previews |
| `Settings_Language_Image` | 159x240 | indexed8 | 30 | yes | Settings pane previews |
| `Settings_Legal_Image` | 20x25 | indexed8 | 17 | yes | Settings pane previews |
| `Settings_MainMenu_CheckmarkBlack_Image` | 14x12 | indexed8 | 4 | yes | Settings pane previews |
| `Settings_MainMenu_CheckmarkWhite_Image` | 14x12 | indexed8 | 22 | yes | Settings pane previews |
| `Settings_MainMenu_Image` | 78x121 | mask4 | - | yes | Settings pane previews |
| `Settings_Radio_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_RepeatAll_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_RepeatOff_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_RepeatOne_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_Reset_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_ShuffleOff_Image` | 78x121 | mask4 | - | yes | Settings pane previews |
| `Settings_ShuffleSongs_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_SortBy_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_SoundCheckOff_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_SoundCheckOn_Image` | 78x121 | mask8 | - | yes | Settings pane previews |
| `Settings_VolumeLimitArrow_Image` | 9x5 | indexed8 | 6 | yes | Settings pane previews |
| `Settings_VolumeLimit_Image` | 78x121 | mask8 | - | yes | Settings pane previews |

## StatusBarBlack

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `StatusBarBlack_Background_Image` | 320x24 | indexed8 | 79 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_0` | 26x13 | indexed8 | 27 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_1` | 26x13 | indexed8 | 27 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_2` | 26x13 | indexed8 | 27 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_3` | 26x13 | indexed8 | 5 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_4` | 26x13 | indexed8 | 6 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_5` | 26x13 | indexed8 | 5 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_6` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_7` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_8` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_9` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_10` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_11` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_12` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_13` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_14` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_15` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_16` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_17` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_18` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_19` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_20` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_21` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_22` | 26x13 | indexed8 | 4 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_Charge` | 26x13 | indexed8 | 41 | yes | Status bar on dark screens |
| `StatusBarBlack_Battery_Image_Plug` | 26x13 | indexed8 | 34 | yes | Status bar on dark screens |
| `StatusBarBlack_Lock_Image` | 11x16 | indexed8 | 14 | yes | Status bar on dark screens |

## StatusBarWhite

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `StatusBarWhite_Background_Image` | 320x20 | indexed8 | 20 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_0` | 26x13 | indexed8 | 62 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_1` | 26x13 | indexed8 | 84 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_2` | 26x13 | indexed8 | 85 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_3` | 26x13 | indexed8 | 87 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_4` | 26x13 | indexed8 | 88 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_5` | 26x13 | indexed8 | 91 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_6` | 26x13 | indexed8 | 90 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_7` | 26x13 | indexed8 | 92 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_8` | 26x13 | indexed8 | 89 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_9` | 26x13 | indexed8 | 92 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_10` | 26x13 | indexed8 | 95 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_11` | 26x13 | indexed8 | 89 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_12` | 26x13 | indexed8 | 93 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_13` | 26x13 | indexed8 | 91 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_14` | 26x13 | indexed8 | 90 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_15` | 26x13 | indexed8 | 88 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_16` | 26x13 | indexed8 | 89 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_17` | 26x13 | indexed8 | 90 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_18` | 26x13 | indexed8 | 85 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_19` | 26x13 | indexed8 | 87 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_20` | 26x13 | indexed8 | 88 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_21` | 26x13 | indexed8 | 78 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_22` | 26x13 | indexed8 | 68 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_Charge` | 26x13 | indexed8 | 55 | yes | Status bar on light screens |
| `StatusBarWhite_Battery_Image_Plug` | 26x13 | indexed8 | 45 | yes | Status bar on light screens |
| `StatusBarWhite_Lock_Image` | 13x16 | indexed8 | 41 | yes | Status bar on light screens |
| `StatusBarWhite_PlayStatus_Image` | 14x16 | bgra8888 | - | yes | Status bar on light screens |

## Stopwatch

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `Stopwatch_Caps_Image` | 123x123 | indexed8 | 42 | yes | Stopwatch |
| `Stopwatch_Clock_Image` | 145x181 | indexed16 | 2895 | yes | Stopwatch |
| `Stopwatch_Mins_Image_0` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_1` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_2` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_3` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_4` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_5` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_6` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_7` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_8` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_9` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_10` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_11` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_12` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_13` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_14` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_15` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_16` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_17` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_18` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_19` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_20` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_21` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_22` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_23` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_24` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_25` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_26` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_27` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_28` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Mins_Image_29` | 18x18 | mask4 | - | yes | Stopwatch |
| `Stopwatch_PlayPause_Image` | 104x76 | indexed16 | 897 | yes | Stopwatch |
| `Stopwatch_Secs_Image_0` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_1` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_2` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_3` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_4` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_5` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_6` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_7` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_8` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_9` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_10` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_11` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_12` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_13` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_14` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_15` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_16` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_17` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_18` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_19` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_20` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_21` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_22` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_23` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_24` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_25` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_26` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_27` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_28` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_Secs_Image_29` | 124x124 | mask4 | - | yes | Stopwatch |
| `Stopwatch_SmallPause_Image` | 23x17 | indexed8 | 5 | yes | Stopwatch |
| `Stopwatch_SmallPlay_Image` | 23x17 | indexed8 | 22 | yes | Stopwatch |

## System

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `System_ActiveButtonFill_Image` | 1x22 | bgra8888 | - | yes |  |
| `System_ActiveButtonLeftCap_Image` | 5x22 | bgra8888 | - | yes |  |
| `System_ActiveButtonRightCap_Image` | 5x22 | bgra8888 | - | yes |  |
| `System_Input_Field_Left_Image` | 10x26 | indexed8 | 49 | yes |  |
| `System_Input_Field_Middle_Image` | 10x26 | indexed8 | 14 | yes | Search, the text typed into the box |
| `System_Input_Field_Right_Image` | 10x26 | indexed8 | 52 | yes |  |
| `System_NormalButtonFill_Image` | 1x26 | bgra8888 | - | yes |  |
| `System_NormalButtonLeftCap_Image` | 6x26 | bgra8888 | - | yes |  |
| `System_NormalButtonRightCap_Image` | 6x26 | bgra8888 | - | yes |  |
| `System_Overlay_BrightnessLess_Image` | 12x13 | indexed8 | 20 | yes |  |
| `System_Overlay_BrightnessMore_Image` | 17x17 | indexed8 | 14 | yes |  |
| `System_Overlay_Left_Image` | 8x80 | indexed8 | 188 | yes |  |
| `System_Overlay_Middle_Image` | 9x80 | indexed8 | 41 | yes |  |
| `System_Overlay_Right_Image` | 8x80 | indexed8 | 188 | yes |  |
| `System_Overlay_VolumeLeft_Image` | 15x13 | indexed8 | 32 | yes |  |
| `System_Overlay_VolumeRight_Image` | 19x17 | indexed8 | 63 | yes |  |
| `System_QuickScroll_123_Image` | 74x70 | mask4 | - | yes |  |
| `System_QuickScroll_Image` | 74x70 | indexed8 | 168 | yes |  |
| `System_ScrollbarBottom_Image` | 6x9 | indexed8 | 7 | yes |  |
| `System_ScrollbarCenter_Image` | 6x8 | indexed8 | 2 | yes |  |
| `System_ScrollbarTop_Image` | 6x10 | indexed8 | 7 | yes |  |
| `System_Submenu_Image` | 10x15 | indexed8 | 34 | yes |  |

## TVOut

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `TVOut_30_Pin_Connector_Image` | 86x98 | indexed16 | 295 | yes | TV Out |
| `TVOut_Background_LeftCap_Image` | 24x48 | indexed8 | 181 | yes | TV Out |
| `TVOut_Background_Middle_Image` | 1x48 | indexed8 | 10 | yes | TV Out |
| `TVOut_Background_RightCap_Image` | 24x48 | indexed8 | 176 | yes | TV Out |
| `TVOut_Charge_Image_Clear_Middle` | 4x50 | indexed8 | 12 | yes | TV Out |
| `TVOut_Charge_Image_Left` | 20x50 | indexed8 | 132 | yes | TV Out |
| `TVOut_Charge_Image_Right` | 20x50 | indexed8 | 135 | yes | TV Out |
| `TVOut_Charge_Image_Set_Middle` | 4x50 | indexed8 | 12 | yes | TV Out |
| `TVOut_Duration_Center_Image` | 1x22 | indexed8 | 3 | yes | TV Out |
| `TVOut_Duration_RightCap_Image` | 10x22 | indexed8 | 52 | yes | TV Out |
| `TVOut_Duration_Scrub_Image` | 20x22 | indexed8 | 9 | yes | TV Out |
| `TVOut_Duration_White_Center_Image` | 1x22 | indexed8 | 4 | yes | TV Out |
| `TVOut_Duration_White_LeftCap_Image` | 10x22 | indexed8 | 67 | yes | TV Out |
| `TVOut_Duration_White_RightCap_Image` | 10x22 | indexed8 | 16 | yes | TV Out |
| `TVOut_FF_Image` | 70x50 | indexed16 | 363 | yes | TV Out |
| `TVOut_Pause_Image` | 70x50 | indexed16 | 303 | yes | TV Out |
| `TVOut_Rew_Image` | 70x50 | indexed16 | 373 | yes | TV Out |
| `TVOut_Volume_Full_Image` | 40x39 | indexed8 | 129 | yes | TV Out |
| `TVOut_Volume_Off_Image` | 42x39 | indexed8 | 70 | yes | TV Out |

## VoiceMemosImage

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `VoiceMemosImage_Colon` | 7x33 | indexed8 | 28 | yes | Voice Memos |
| `VoiceMemosImage_Meter` | 127x167 | indexed16 | 4454 | yes | Voice Memos |
| `VoiceMemosImage_Microphone` | 110x190 | indexed16 | 2852 | yes | Voice Memos |
| `VoiceMemosImage_Pause` | 86x145 | indexed16 | 796 | yes | Voice Memos |
| `VoiceMemosImage_Reflect_0` | 20x50 | indexed8 | 73 | yes | Voice Memos |
| `VoiceMemosImage_Reflect_1` | 20x50 | indexed8 | 56 | yes | Voice Memos |
| `VoiceMemosImage_Reflect_2` | 20x50 | indexed8 | 66 | yes | Voice Memos |
| `VoiceMemosImage_Reflect_3` | 20x50 | indexed8 | 77 | yes | Voice Memos |
| `VoiceMemosImage_Reflect_4` | 20x50 | indexed8 | 62 | yes | Voice Memos |
| `VoiceMemosImage_Reflect_5` | 20x50 | indexed8 | 70 | yes | Voice Memos |
| `VoiceMemosImage_Reflect_6` | 20x50 | indexed8 | 72 | yes | Voice Memos |
| `VoiceMemosImage_Reflect_7` | 20x50 | indexed8 | 61 | yes | Voice Memos |
| `VoiceMemosImage_Reflect_8` | 20x50 | indexed8 | 74 | yes | Voice Memos |
| `VoiceMemosImage_Reflect_9` | 20x50 | indexed8 | 73 | yes | Voice Memos |

## Other

| Name | Size | Format | Palette | Tintable | Appears |
|---|---|---|---|---|---|
| `AddressViewer_NoContactPict_Image` | 55x55 | indexed8 | 216 | yes | Contacts |
| `AddressViewer_NoGroupPict_Image` | 55x55 | indexed16 | 274 | yes | Contacts |
| `AddressViewer_Preview_Image` | 130x146 | indexed16 | 4177 | yes | Contacts |
| `Alarms_Clock_Static_Image` | 127x135 | indexed16 | 5199 | yes | Clock > Alarms |
| `Alarms_Timer_Time_Panel` | 163x53 | indexed16 | 485 | yes | Clock > Alarms |
| `Alarms_Timer_Time_Panel_Focus` | 40x37 | indexed8 | 141 | yes | Clock > Alarms |
| `Background_LightBlue_Image` | 320x240 | indexed16 | 1530 | yes | Background behind the Settings previews |
| `BigDaisyPetal0` | 3x12 | mask4 | - | yes | Activity spinner |
| `BigDaisyPetal1` | 9x13 | mask4 | - | yes | Activity spinner |
| `BigDaisyPetal2` | 12x9 | mask4 | - | yes | Activity spinner |
| `BigDaisyPetal3` | 12x3 | mask4 | - | yes | Activity spinner |
| `BigDaisyPetal4` | 12x9 | mask4 | - | yes | Activity spinner |
| `BigDaisyPetal5` | 9x13 | mask4 | - | yes | Activity spinner |
| `CoverFlow_Backside_Top_Image` | 8x43 | indexed8 | 69 | yes | Cover Flow, the track list behind a cover |
| `CoverFlow_Proxy_Image` | 128x128 | rgb565 | - | no | Cover Flow |
| `CoverFlow_Proxy_Image_iTunesU` | 128x128 | rgb565 | - | no | Cover Flow |
| `DateTimePicker_Bar` | 167x57 | indexed16 | 361 | yes | Date and time picker |
| `DateTimePicker_Selection` | 40x37 | indexed8 | 141 | yes | Date and time picker, the selected value |
| `DateTimePicker_Well` | 40x41 | indexed8 | 211 | yes | Date and time picker, the values |
| `DemoMode_Icon` | 97x97 | indexed16 | 869 | yes |  |
| `Extras_Games_Preview_Image` | 142x87 | indexed16 | 5662 | yes |  |
| `Games_Proxy_Image` | 55x55 | indexed16 | 519 | yes |  |
| `GeniusMixes_Background_Image` | 8x240 | indexed8 | 47 | yes | Genius |
| `LockScreen_Padlock_Image` | 116x165 | indexed16 | 3250 | yes | Screen Lock |
| `LockScreen_TumblerBgnd_Image` | 182x57 | indexed16 | 372 | yes | Screen Lock and Volume Limit, the combination digits |
| `LockScreen_TumblerFocus_Image` | 26x54 | indexed8 | 174 | yes | Screen Lock and Volume Limit, the focused digit |
| `Lozenge_Left_White_Image` | 15x58 | indexed8 | 182 | yes | Lozenges |
| `Lozenge_Middle_White_Image` | 16x58 | indexed8 | 97 | yes | Lozenges |
| `Lozenge_Right_White_Image` | 15x58 | indexed8 | 177 | yes | Lozenges |
| `MainMenu_Backlight_Image` | 119x119 | mask8 | - | yes | Main menu |
| `MainMenu_Shuffle_Image` | 119x119 | mask8 | - | yes | Main menu |
| `MainMenu_Sleep_Image` | 98x146 | mask8 | - | yes | Main menu |
| `Notes_Preview_Image` | 120x146 | indexed16 | 5841 | yes |  |
| `Page_White_Active_Image` | 8x8 | indexed8 | 5 | yes | Page indicators |
| `Page_White_Inactive_Image` | 8x8 | indexed8 | 8 | yes | Page indicators |
| `Photos_Slideshow_Top_Strip` | 1x88 | indexed8 | 4 | yes |  |
| `PreviewArea_Shadow_Image` | 26x240 | indexed8 | 40 | yes |  |
| `RemoteUI_Icon_Apple` | 113x113 | indexed8 | 184 | yes |  |
| `Speakers_Icon_Image` | 159x240 | indexed16 | 3155 | yes |  |
| `WorldClock_Graybar_Image` | 5x80 | indexed8 | 67 | yes | Clock, world clocks |
| `WorldClock_Map_Image` | 320x240 | mask4 | - | yes | Clock, world clocks |
