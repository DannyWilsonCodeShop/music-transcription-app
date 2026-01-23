import { useState, useRef, useEffect } from 'react';

interface VideoCardProps {
  id: string;
  author: {
    name: string;
    avatar: string;
  };
  title: string;
  description: string;
  videoUrl: string;
  thumbnail: string;
  timestamp: string;
  likes: number;
  comments: number;
  shares: number;
}

export default function VideoCard({
  author,
  title,
  description,
  videoUrl,
  thumbnail,
  timestamp,
  likes,
  comments,
  shares,
}: VideoCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [liked, setLiked] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && videoRef.current) {
            videoRef.current.play();
            setIsPlaying(true);
          } else if (videoRef.current) {
            videoRef.current.pause();
            setIsPlaying(false);
          }
        });
      },
      { threshold: 0.5 }
    );

    if (cardRef.current) {
      observer.observe(cardRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={cardRef}
      className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow border border-blue-200"
    >
      {/* Header */}
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img
            src={author.avatar}
            alt={author.name}
            className="w-10 h-10 rounded-full"
          />
          <div>
            <h3 className="font-semibold text-[#3f3f3f]">{author.name}</h3>
            <p className="text-xs text-gray-500">{timestamp}</p>
          </div>
        </div>
        <button className="px-3 py-1 bg-[#00bfc4] text-white text-sm rounded-full hover:bg-[#00a5aa] transition-colors">
          Practice Buddy
        </button>
      </div>

      {/* Video */}
      <div className="relative aspect-video bg-black">
        <video
          ref={videoRef}
          src={videoUrl}
          poster={thumbnail}
          className="w-full h-full object-cover"
          loop
          muted
          playsInline
        />
        {!isPlaying && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30">
            <div className="w-16 h-16 bg-white bg-opacity-90 rounded-full flex items-center justify-center">
              <div className="w-0 h-0 border-l-[20px] border-l-[#00bfc4] border-t-[12px] border-t-transparent border-b-[12px] border-b-transparent ml-1"></div>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h4 className="font-semibold text-[#3f3f3f] mb-1">{title}</h4>
        <p className="text-sm text-gray-600">{description}</p>
      </div>

      {/* Footer */}
      <div className="px-4 pb-4 flex items-center gap-6 text-gray-600">
        <button
          onClick={() => setLiked(!liked)}
          className="flex items-center gap-2 hover:text-[#00bfc4] transition-colors"
        >
          <span className="text-xl">{liked ? '❤️' : '🤍'}</span>
          <span className="text-sm font-medium">{liked ? likes + 1 : likes}</span>
        </button>
        <button className="flex items-center gap-2 hover:text-[#00bfc4] transition-colors">
          <span className="text-xl">💬</span>
          <span className="text-sm font-medium">{comments}</span>
        </button>
        <button className="flex items-center gap-2 hover:text-[#00bfc4] transition-colors">
          <span className="text-xl">🔄</span>
          <span className="text-sm font-medium">{shares}</span>
        </button>
      </div>
    </div>
  );
}
