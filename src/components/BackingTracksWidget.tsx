export default function BackingTracksWidget() {
  const tracks = [
    {
      id: 1,
      name: 'Blues in A',
      genre: 'Blues',
      key: 'A',
      instruments: ['Drums', 'Bass', 'Keys'],
      color: 'bg-blue-500',
    },
    {
      id: 2,
      name: 'Jazz Swing',
      genre: 'Jazz',
      key: 'Bb',
      instruments: ['Drums', 'Bass', 'Piano'],
      color: 'bg-purple-500',
    },
    {
      id: 3,
      name: 'Rock Ballad',
      genre: 'Rock',
      key: 'G',
      instruments: ['Drums', 'Bass'],
      color: 'bg-red-500',
    },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-[#3f3f3f] flex items-center gap-2">
          🎼 Backing Tracks
        </h3>
        <a href="#" className="text-xs text-[#00bfc4] hover:underline font-medium">
          View All
        </a>
      </div>

      {/* Tracks List */}
      <div className="space-y-3">
        {tracks.map((track) => (
          <div
            key={track.id}
            className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <div className={`w-2 h-2 rounded-full ${track.color}`}></div>
                  <h4 className="font-medium text-sm text-[#3f3f3f]">{track.name}</h4>
                </div>
                <p className="text-xs text-gray-500">{track.genre}</p>
              </div>
              <span className="px-2 py-1 bg-[#00bfc4] text-white text-xs rounded-full font-medium">
                {track.key}
              </span>
            </div>

            <div className="flex gap-1 flex-wrap">
              {track.instruments.map((instrument, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded"
                >
                  {instrument}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
