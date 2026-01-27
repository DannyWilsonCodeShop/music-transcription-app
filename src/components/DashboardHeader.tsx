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
    <header className="bg-gradient-to-r from-primary via-primary to-tertiary text-white py-3 px-4 shadow-lg">
      <div className="max-w-[1600px] mx-auto flex justify-between items-center">
        {/* Left side - Logo */}
        <div className="flex items-center">
          <img 
            src="/Chord Scout Logo 2.png" 
            alt="ChordScout Logo" 
            className="h-12 w-auto"
          />
        </div>
        
        {/* Right side - User info */}
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm font-medium">{greeting}, {userName}! 👋</p>
            <p className="text-xs text-neutral/80">danny@example.com</p>
          </div>
          <div className="w-10 h-10 bg-gradient-to-br from-secondary to-tertiary rounded-full flex items-center justify-center shadow-md">
            <span className="text-lg font-bold text-white">D</span>
          </div>
        </div>
      </div>
    </header>
  );
}
