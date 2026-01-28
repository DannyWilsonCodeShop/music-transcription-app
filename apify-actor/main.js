// Apify Actor for YouTube Audio Download
// This actor downloads audio from YouTube URLs and returns download links

import { Actor } from 'apify';
import ytdl from '@distube/ytdl-core';

await Actor.init();

try {
    // Get input from Apify
    const input = await Actor.getInput();
    console.log('Input:', input);

    const { youtubeUrl, url, videoId } = input;
    const videoUrl = youtubeUrl || url;

    if (!videoUrl) {
        throw new Error('Missing youtubeUrl or url parameter');
    }

    console.log(`Processing: ${videoUrl}`);

    // Get video info
    const info = await ytdl.getInfo(videoUrl);
    
    // Find best audio format
    const audioFormats = ytdl.filterFormats(info.formats, 'audioonly');
    
    if (!audioFormats || audioFormats.length === 0) {
        throw new Error('No audio formats found');
    }

    // Sort by quality (bitrate)
    audioFormats.sort((a, b) => {
        const aBitrate = a.audioBitrate || 0;
        const bBitrate = b.audioBitrate || 0;
        return bBitrate - aBitrate;
    });

    const bestAudio = audioFormats[0];

    // Prepare output
    const result = {
        videoId: info.videoDetails.videoId,
        title: info.videoDetails.title,
        duration: parseInt(info.videoDetails.lengthSeconds),
        channel: info.videoDetails.author.name,
        audioUrl: bestAudio.url,
        format: bestAudio.container,
        bitrate: bestAudio.audioBitrate,
        quality: bestAudio.audioQuality
    };

    console.log('Result:', JSON.stringify(result, null, 2));

    // Save to dataset
    await Actor.pushData(result);

    console.log('Actor finished successfully');
} catch (error) {
    console.error('Actor failed:', error);
    throw error;
}

await Actor.exit();
