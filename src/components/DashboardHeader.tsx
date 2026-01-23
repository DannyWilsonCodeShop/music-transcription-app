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
    <header className="bg-primary text-white py-6 px-4 shadow-lg">
      <div className="max-w-[1600px] mx-auto">
        <h1 className="text-3xl font-bold mb-1">
          {greeting}, {userName}! 👋
        </h1>
        <p className="text-gray-300 text-sm">
          Ready to continue your learning journey?
        </p>
      </div>
    </header>
  );
}
