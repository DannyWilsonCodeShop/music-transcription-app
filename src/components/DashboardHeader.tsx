import { useEffect, useState } from 'react';

interface DashboardHeaderProps {
  userName: string;
}

export default function DashboardHeader({ userName }: DashboardHeaderProps) {
  const [greeting, setGreeting] = useState('');

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting('Good morning');
    else if (hour < 18) setGreeting('Good afternoon');
    else setGreeting('Good evening');
  }, []);

  return (
    <header className="bg-primary text-white py-4 px-4 shadow-lg">
      <div className="max-w-[1600px] mx-auto flex justify-between items-center">
        {/* Left side - App title or empty */}
        <div>
          <h1 className="text-2xl font-bold">ChordScout</h1>
        </div>
        
        {/* Right side - User info */}
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm font-medium">{greeting}, {userName}! 👋</p>
            <p className="text-xs text-gray-300">danny@example.com</p>
          </div>
          <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
            <span className="text-lg font-bold">D</span>
          </div>
        </div>
      </div>
    </header>
  );
}
