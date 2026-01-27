import { useState } from 'react';

interface CommunityPostCardProps {
  id: string;
  author: {
    name: string;
    avatar: string;
  };
  content: string;
  timestamp: string;
  likes: number;
  comments: number;
}

export default function CommunityPostCard({
  author,
  content,
  timestamp,
  likes,
  comments,
}: CommunityPostCardProps) {
  const [liked, setLiked] = useState(false);

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-4 border border-blue-200">
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
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

      {/* Content */}
      <p className="text-[#3f3f3f] mb-4">{content}</p>

      {/* Footer */}
      <div className="flex items-center gap-6 text-gray-600 pt-3 border-t border-gray-100">
        <button
          onClick={() => setLiked(!liked)}
          className="flex items-center gap-2 hover:text-[#0089c6] transition-colors"
        >
          <span className="text-xl">{liked ? '❤️' : '🤍'}</span>
          <span className="text-sm font-medium">{liked ? likes + 1 : likes}</span>
        </button>
        <button className="flex items-center gap-2 hover:text-[#0089c6] transition-colors">
          <span className="text-xl">💬</span>
          <span className="text-sm font-medium">{comments}</span>
        </button>
      </div>
    </div>
  );
}
