# Add music you own or have permission to redistribute

This repository accepts actual audio files only when you own the recording or have
clear permission from the rights holder to redistribute it.

## YouTube uploads you own
1. Open YouTube Studio using the account that owns the upload.
2. Download the video using YouTube Studio's download option.
3. Convert the downloaded file to MP3 locally using a tool you trust.
4. Add the MP3 under `audio/owned/` and include the details in
   `licenses/owned-audio-attribution.jsonl`.

Do not use this process for other people's copyrighted uploads unless the
rights holder has explicitly authorised downloading and redistribution.

## Tracks with creator-provided download permission
Use the creator's official download link, not a YouTube ripper. Record one JSON
object per track in `licenses/owned-audio-attribution.jsonl`:

```json
{"file":"audio/owned/example.mp3","title":"Track title","creator":"Artist","source":"https://creator.example/track","permission":"Written permission or licence URL","redistribution_allowed":true}
```

Keep proof of permission or the licence alongside the track. A streaming link,
a public YouTube video, or permission to use a song in a video is not by itself
permission to upload the MP3 to this repository.

## Existing automatic importer
The workflow at `.github/workflows/import-open-audio.yml` imports only tracks
whose archive metadata declares an accepted Creative Commons licence.
