export default function RippedSongsWidget() {
  const songs = [
    {
      id: 1,
      name: 'Hotel California',
      key: 'Bm',
      hasLyrics: true,
      hasPiano: true,
      hasGuitar: true,
      hasBass: false,
      date: '2 days ago',
    },
    {
      id: 2,
      name: 'Wonderwall',
      key: 'Em',
      hasLyrics: true,
      hasPiano: false,
      hasGuitar: true,
      hasBass: true,
      date: '3 days ago',
    },
    {
      id: 3,
      name: 'Let It Be',
      key: 'C',
      hasLyrics: true,
      hasPiano: true,
      hasGuitar: true,
      hasBass: true,
      date: '5 days ago',
    },
  ];

  return (
    <div className="bg-white rounded-xl shadow-md p-4 border border-blue-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-[#3f3f3f] flex items-center gap-2">
          🎵 Ripped Songs Database
        </h3>
        <a href="#" className="text-xs text-[#00bfc4] hover:underline">
          View All
        </a>
      </div>

      <div className="space-y-3">
        {songs.map((song) => (
          <div
            key={song.id}
            className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="font-medium text-sm text-[#3f3f3f]">{song.name}</h4>
                <p className="text-xs text-gray-500">{song.date}</p>
              </div>
              <span className="px-2 py-1 bg-[#00bfc4] text-white text-xs rounded-full font-medium">
                {song.key}
              </span>
            </div>

            <div className="flex gap-2 flex-wrap">
              {song.hasLyrics && (
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
                  📝 Lyrics
                </span>
              )}
              {song.hasPiano && (
                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">
                  🎹 Piano
                </span>
              )}
              {song.hasGuitar && (
                <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded">
                  🎸 Guitar
                </span>
              )}
              {song.hasBass && (
                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                  🎸 Bass
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
