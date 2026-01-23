import { useState, useEffect } from 'react';

const dailyQuestions = [
  "Share a funny moment from your day! 😄",
  "What song are you learning right now? 🎸",
  "Drop your best practice tip! 💡",
  "What's your favorite chord progression? 🎵",
  "Share a music goal for this week! 🎯",
  "What instrument do you want to learn next? 🎹",
  "Tell us about your musical inspiration! ✨",
  "What's the hardest song you've mastered? 🏆",
  "Share your practice routine! ⏰",
  "What's your go-to warm-up exercise? 🔥",
  "Recommend a song for beginners! 📚",
  "What's your favorite music genre? 🎼",
  "Share a breakthrough moment! 🌟",
  "What's on your practice playlist? 🎧",
  "Tell us about your first performance! 🎤",
  "What's your dream collaboration? 🤝",
  "Share your favorite music memory! 💭",
  "What motivates you to practice? 💪",
  "Recommend a music learning resource! 📖",
  "What's your practice space like? 🏠",
  "Share a technique you're working on! 🎯",
  "What's your favorite scale to practice? 🎶",
  "Tell us about your music teacher! 👨‍🏫",
  "What's your pre-performance ritual? 🎭",
  "Share your biggest music challenge! 🧗",
  "What's your favorite music app? 📱",
  "Tell us about your instrument! 🎸",
  "What's your practice time sweet spot? ⏱️",
  "Share a music theory tip! 🧠",
  "What's your favorite chord? 🎵",
  "Tell us about a music fail! 😅",
  "What's your dream setlist? 📝",
  "Share your favorite backing track! 🎼",
  "What's your music learning goal? 🎓",
  "Tell us about your band! 🎸🥁🎹",
  "What's your favorite music venue? 🏟️",
  "Share a song that changed your life! 💫",
  "What's your practice accountability hack? ✅",
  "Tell us about your music journey! 🛤️",
  "What's your next musical milestone? 🏁"
];

export default function PostComposer() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [postContent, setPostContent] = useState('');
  const [isExploreMode, setIsExploreMode] = useState(false);
  const [dailyQuestion, setDailyQuestion] = useState('');

  useEffect(() => {
    const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0).getTime()) / 86400000);
    setDailyQuestion(dailyQuestions[dayOfYear % dailyQuestions.length]);
  }, []);

  const handlePost = () => {
    console.log('Posting:', postContent);
    setPostContent('');
    setIsExpanded(false);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-4 border border-blue-200">
      {/* Composer Bar */}
      <div className="flex items-center gap-3">
        {/* Avatar */}
        <img
          src="https://api.dicebear.com/7.x/avataaars/svg?seed=user"
          alt="User avatar"
          className="w-10 h-10 rounded-full"
        />

        {/* Expandable Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex-1 text-left px-4 py-3 rounded-xl bg-gradient-to-r from-[#00bfc4] to-[#ffe600] text-white font-medium hover:shadow-md transition-all"
        >
          <span className="flex items-center gap-2">
            ✨ {dailyQuestion}
          </span>
        </button>

        {/* Explore Toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={isExploreMode}
            onChange={(e) => setIsExploreMode(e.target.checked)}
            className="sr-only peer"
          />
          <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-500"></div>
          <span className="text-2xl">🔥</span>
        </label>
      </div>

      {/* Expanded Textarea */}
      {isExpanded && (
        <div className="mt-4 space-y-3 animate-fadeIn">
          <textarea
            value={postContent}
            onChange={(e) => setPostContent(e.target.value)}
            placeholder="Share your thoughts..."
            className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-[#00bfc4] focus:outline-none resize-none"
            rows={4}
            autoFocus
          />
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => {
                setIsExpanded(false);
                setPostContent('');
              }}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handlePost}
              disabled={!postContent.trim()}
              className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Post ✨
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
