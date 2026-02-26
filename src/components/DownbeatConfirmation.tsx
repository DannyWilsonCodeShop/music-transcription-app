import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, SkipBack, SkipForward, Check, X } from 'lucide-react';

interface DownbeatConfirmationProps {
  audioUrl: string;
  detectedDownbeat: number;
  detectedTempo: number;
  detectedTimeSignature: string;
  beatTimes: number[];
  onConfirm: (downbeat: number, timeSignature: string) => void;
  onCancel: () => void;
}

export const DownbeatConfirmation: React.FC<DownbeatConfirmationProps> = ({
  audioUrl,
  detectedDownbeat,
  detectedTempo,
  detectedTimeSignature,
  beatTimes,
  onConfirm,
  onCancel,
}) => {
  const [currentDownbeat, setCurrentDownbeat] = useState(detectedDownbeat);
  const [timeSignature, setTimeSignature] = useState(detectedTimeSignature);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [showClickTrack, setShowClickTrack] = useState(true);
  
  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const clickAudioContextRef = useRef<AudioContext | null>(null);
  const clickSourceRef = useRef<AudioBufferSourceNode | null>(null);

  const beatsPerMeasure = parseInt(timeSignature.split('/')[0]);
  const beatDuration = 60 / detectedTempo;

  // Calculate downbeats based on current downbeat
  const getDownbeats = () => {
    const downbeats: number[] = [];
    const firstDownbeatIndex = beatTimes.findIndex(
      (beat) => Math.abs(beat - currentDownbeat) < 0.01
    );
    
    if (firstDownbeatIndex >= 0) {
      for (let i = firstDownbeatIndex; i < beatTimes.length; i += beatsPerMeasure) {
        downbeats.push(beatTimes[i]);
      }
    }
    
    return downbeats;
  };

  const downbeats = getDownbeats();

  // Draw waveform and beat markers
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, width, height);

    // Draw waveform placeholder (simplified)
    ctx.strokeStyle = '#4a5568';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    for (let x = 0; x < width; x++) {
      const y = height / 2 + Math.sin(x * 0.02) * 20;
      ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Draw beat markers
    const clipDuration = 8; // 8 seconds visible
    const clipStart = Math.max(0, currentDownbeat - 0.5);
    
    beatTimes.forEach((beat) => {
      if (beat >= clipStart && beat < clipStart + clipDuration) {
        const x = ((beat - clipStart) / clipDuration) * width;
        const isDownbeat = downbeats.some((db) => Math.abs(db - beat) < 0.01);
        
        ctx.strokeStyle = isDownbeat ? '#ef4444' : '#60a5fa';
        ctx.lineWidth = isDownbeat ? 3 : 1;
        ctx.globalAlpha = isDownbeat ? 1 : 0.5;
        
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
        
        ctx.globalAlpha = 1;
      }
    });

    // Draw current time indicator
    if (isPlaying && currentTime >= clipStart && currentTime < clipStart + clipDuration) {
      const x = ((currentTime - clipStart) / clipDuration) * width;
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
  }, [currentDownbeat, beatTimes, downbeats, currentTime, isPlaying, beatsPerMeasure]);

  // Generate click track
  const generateClickTrack = async () => {
    if (!clickAudioContextRef.current) {
      clickAudioContextRef.current = new AudioContext();
    }

    const audioContext = clickAudioContextRef.current;
    const clipDuration = 8;
    const clipStart = Math.max(0, currentDownbeat - 0.5);
    const sampleRate = audioContext.sampleRate;
    const buffer = audioContext.createBuffer(1, clipDuration * sampleRate, sampleRate);
    const data = buffer.getChannelData(0);

    // Generate clicks
    beatTimes.forEach((beat) => {
      if (beat >= clipStart && beat < clipStart + clipDuration) {
        const isDownbeat = downbeats.some((db) => Math.abs(db - beat) < 0.01);
        const clickStart = Math.floor((beat - clipStart) * sampleRate);
        const clickDuration = isDownbeat ? 0.05 : 0.03; // 50ms for downbeat, 30ms for beat
        const frequency = isDownbeat ? 1000 : 800; // 1000Hz for downbeat, 800Hz for beat
        const amplitude = isDownbeat ? 0.5 : 0.3;

        for (let i = 0; i < clickDuration * sampleRate; i++) {
          const t = i / sampleRate;
          const sample = amplitude * Math.sin(2 * Math.PI * frequency * t) * Math.exp(-t * 20);
          const index = clickStart + i;
          if (index < data.length) {
            data[index] += sample;
          }
        }
      }
    });

    return buffer;
  };

  // Play audio with click track
  const handlePlay = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      if (clickSourceRef.current) {
        clickSourceRef.current.stop();
        clickSourceRef.current = null;
      }
      setIsPlaying(false);
    } else {
      const clipStart = Math.max(0, currentDownbeat - 0.5);
      audio.currentTime = clipStart;
      audio.play();
      setIsPlaying(true);

      // Play click track if enabled
      if (showClickTrack && clickAudioContextRef.current) {
        const clickBuffer = await generateClickTrack();
        const source = clickAudioContextRef.current.createBufferSource();
        source.buffer = clickBuffer;
        source.connect(clickAudioContextRef.current.destination);
        source.start();
        clickSourceRef.current = source;

        // Stop after 8 seconds
        setTimeout(() => {
          audio.pause();
          setIsPlaying(false);
        }, 8000);
      }
    }
  };

  // Update current time
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => {
      setCurrentTime(audio.currentTime);
    };

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('ended', () => setIsPlaying(false));

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('ended', () => setIsPlaying(false));
    };
  }, []);

  // Adjust downbeat
  const adjustDownbeat = (direction: 'prev' | 'next') => {
    const currentIndex = beatTimes.findIndex(
      (beat) => Math.abs(beat - currentDownbeat) < 0.01
    );
    
    if (currentIndex >= 0) {
      const newIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1;
      if (newIndex >= 0 && newIndex < beatTimes.length) {
        setCurrentDownbeat(beatTimes[newIndex]);
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 p-6">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Confirm Downbeat & Time Signature
          </h2>
          <p className="text-gray-600">
            Listen to the audio with click track and confirm the downbeat aligns with measure 1
          </p>
        </div>

        {/* Detection Info */}
        <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <div>
            <div className="text-sm text-gray-600">Tempo</div>
            <div className="text-xl font-semibold">{detectedTempo.toFixed(1)} BPM</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">First Downbeat</div>
            <div className="text-xl font-semibold">{currentDownbeat.toFixed(3)}s</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Time Signature</div>
            <select
              value={timeSignature}
              onChange={(e) => setTimeSignature(e.target.value)}
              className="text-xl font-semibold bg-transparent border-b-2 border-blue-500 focus:outline-none"
            >
              <option value="4/4">4/4</option>
              <option value="3/4">3/4</option>
              <option value="6/8">6/8</option>
              <option value="5/4">5/4</option>
              <option value="7/8">7/8</option>
            </select>
          </div>
        </div>

        {/* Waveform */}
        <div className="mb-6">
          <canvas
            ref={canvasRef}
            width={800}
            height={150}
            className="w-full border border-gray-300 rounded-lg"
          />
          <div className="flex items-center justify-between mt-2 text-sm text-gray-600">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded"></div>
                <span>Downbeats (loud clicks)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-400 rounded"></div>
                <span>Regular beats (soft clicks)</span>
              </div>
            </div>
            <div>Showing 8 seconds from downbeat</div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-center gap-4 mb-6">
          <button
            onClick={() => adjustDownbeat('prev')}
            className="p-3 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
            title="Try previous beat"
          >
            <SkipBack className="w-5 h-5" />
          </button>

          <button
            onClick={handlePlay}
            className="p-4 rounded-full bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          >
            {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
          </button>

          <button
            onClick={() => adjustDownbeat('next')}
            className="p-3 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
            title="Try next beat"
          >
            <SkipForward className="w-5 h-5" />
          </button>
        </div>

        {/* Click Track Toggle */}
        <div className="flex items-center justify-center mb-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showClickTrack}
              onChange={(e) => setShowClickTrack(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-gray-700">Play with click track</span>
          </label>
        </div>

        {/* Instructions */}
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">Instructions:</h3>
          <ol className="list-decimal list-inside space-y-1 text-blue-800 text-sm">
            <li>Click play to hear an 8-second clip with click track</li>
            <li>LOUD clicks should align with the first beat of each measure</li>
            <li>Count beats between loud clicks - should match time signature</li>
            <li>Use ← → buttons to try different beats if alignment is off</li>
            <li>Adjust time signature if needed</li>
            <li>Click "Confirm" when alignment is correct</li>
          </ol>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <X className="w-4 h-4" />
            Cancel
          </button>
          <button
            onClick={() => onConfirm(currentDownbeat, timeSignature)}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <Check className="w-4 h-4" />
            Confirm & Continue
          </button>
        </div>

        {/* Hidden audio element */}
        <audio ref={audioRef} src={audioUrl} preload="auto" />
      </div>
    </div>
  );
};
