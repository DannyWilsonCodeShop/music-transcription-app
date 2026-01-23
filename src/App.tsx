import { useState, useEffect, useRef } from 'react';
import { Amplify } from 'aws-amplify';
import outputs from '../amplify_outputs.json';
import PostComposer from './components/PostComposer';
import VideoCard from './components/VideoCard';
import CommunityPostCard from './components/CommunityPostCard';
import RippedSongsWidget from './components/RippedSongsWidget';
import BackingTracksWidget from './components/BackingTracksWidget';
import StudyModulesWidget from './components/StudyModulesWidget';
import DashboardHeader from './components/DashboardHeader';

Amplify.configure(outputs);

// Mock data for feed
const generateMockFeed = (count: number) => {
  const items = [];
  for (let i = 0; i < count; i++) {
    if (i % 3 === 0) {
      items.push({
        id: `post-${i}`,
        type: 'post',
        author: {
          name: ['Alex Johnson', 'Sarah Chen', 'Mike Rodriguez', 'Emma Wilson'][i % 4],
          avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${i}`,
        },
        content: [
          'Just finished transcribing "Bohemian Rhapsody" - what a journey! 🎸',
          'Anyone else struggling with the bridge in "Stairway to Heaven"? Need tips!',
          'Loving the new chord detection feature! So accurate! 🎵',
          'Practice session complete! 30 minutes of scales and arpeggios ✨',
        ][i % 4],
        timestamp: `${Math.floor(Math.random() * 24)}h ago`,
        likes: Math.floor(Math.random() * 100),
        comments: Math.floor(Math.random() * 50),
      });
    } else {
      items.push({
        id: `video-${i}`,
        type: 'video',
        author: {
          name: ['David Lee', 'Lisa Park', 'Tom Anderson', 'Nina Patel'][i % 4],
          avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=video${i}`,
        },
        title: [
          'My cover of "Hotel California" - Solo Section',
          'Learning Jazz Chords - Beginner Tutorial',
          'Fingerstyle Arrangement of "Blackbird"',
          'Blues Improvisation Practice Session',
        ][i % 4],
        description: 'Check out my latest practice session! Would love feedback 🎸',
        videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
        thumbnail: `https://picsum.photos/seed/${i}/640/360`,
        timestamp: `${Math.floor(Math.random() * 48)}h ago`,
        likes: Math.floor(Math.random() * 200),
        comments: Math.floor(Math.random() * 80),
        shares: Math.floor(Math.random() * 30),
      });
    }
  }
  return items;
};

function App() {
  const [feedItems] = useState(() => generateMockFeed(1000));
  const [visibleItems, setVisibleItems] = useState(20);
  const feedRef = useRef<HTMLDivElement>(null);
  const [userName] = useState('Danny');

  // Infinite scroll
  useEffect(() => {
    const handleScroll = () => {
      if (!feedRef.current) return;
      
      const { scrollTop, scrollHeight, clientHeight } = feedRef.current;
      if (scrollTop + clientHeight >= scrollHeight - 500) {
        setVisibleItems(prev => Math.min(prev + 20, feedItems.length));
      }
    };

    const feedElement = feedRef.current;
    feedElement?.addEventListener('scroll', handleScroll);
    return () => feedElement?.removeEventListener('scroll', handleScroll);
  }, [feedItems.length]);

  return (
    <div className="min-h-screen bg-[#e5e5e5]">
      {/* Header */}
      <DashboardHeader userName={userName} />

      {/* Main Content - 4 Column Grid */}
      <div className="max-w-[1600px] mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column - Main Feed (3/4 width) */}
          <div className="lg:col-span-3 space-y-6">
            {/* Post Composer */}
            <PostComposer />

            {/* Feed */}
            <div 
              ref={feedRef}
              className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-200"
            >
              {feedItems.slice(0, visibleItems).map((item) => (
                item.type === 'video' ? (
                  <VideoCard key={item.id} {...item} />
                ) : (
                  <CommunityPostCard key={item.id} {...item} />
                )
              ))}
              
              {visibleItems < feedItems.length && (
                <div className="text-center py-4">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-[#00bfc4]"></div>
                </div>
              )}
            </div>
          </div>

          {/* Right Sidebar (1/4 width) */}
          <div className="lg:col-span-1 space-y-4">
            <RippedSongsWidget />
            <BackingTracksWidget />
            <StudyModulesWidget />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
